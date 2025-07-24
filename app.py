import streamlit as st
import pandas as pd
import folium
import calendar
from streamlit_folium import folium_static

# URL da planilha pública
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

# Mapeamento de meses em português
mes_format = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()

    # Coordenadas
    df[['LATITUDE', 'LONGITUDE']] = df['COORDENADAS'].str.split(',', expand=True)
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'].str.strip(), errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'].str.strip(), errors='coerce')

    # Conversões
    df['DATA'] = pd.to_datetime(df['DATA'], format="%d/%m/%Y", errors='coerce')
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month.astype('Int64')
    df['CAIXAS'] = pd.to_numeric(df['CAIXAS'], errors='coerce')
    df['FRASCOS'] = df['CAIXAS'] * 50

    # Remanescentes
    if 'REMANESCENTES' in df.columns:
        df['REMANESCENTES'] = pd.to_numeric(df['REMANESCENTES'], errors='coerce').fillna(0)

    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    df = df[df['CAIXAS'] > 0]

    return df

df = load_data()

st.title("📦 Entregas de Hipoclorito")
st.write("Visualize os frascos entregues por mês, ano e local.")

# Filtros
anos = sorted(df['Ano'].dropna().unique())
ano_opcoes = ["Todos"] + [str(a) for a in anos]
ano_selecionado = st.selectbox("Filtrar por Ano", options=ano_opcoes)

meses = sorted(df['Mês'].dropna().unique())
mes_opcoes = ["Todos"] + list(meses)
mes_selecionados = st.multiselect(
    "Filtrar por Mês",
    options=mes_opcoes,
    default=["Todos"],
    format_func=lambda x: "Todos" if x == "Todos" else mes_format.get(x, str(x))
)

locais = sorted(df['LOCAL'].dropna().unique())
local_opcoes = ["Todos"] + locais
local_selecionado = st.selectbox("Filtrar por Local", options=local_opcoes)

# Aplicar filtros
dados = df.copy()
if ano_selecionado != "Todos":
    ano_int = int(float(ano_selecionado))
    dados = dados[dados['Ano'] == ano_int]

if "Todos" not in mes_selecionados:
    meses_int = [int(m) for m in mes_selecionados]
    dados = dados[dados['Mês'].isin(meses_int)]

if local_selecionado != "Todos":
    dados = dados[dados['LOCAL'] == local_selecionado]

# Dados filtrados
total_frascos = dados['FRASCOS'].sum()
st.subheader("📋 Dados filtrados")
st.write(f"**Total entregue:** {total_frascos:.0f} frascos")

df_exibicao = dados.copy()
df_exibicao['DATA'] = df_exibicao.apply(
    lambda row: f"{mes_format.get(row['Mês'], '')} {int(row['Ano'])}" if pd.notnull(row['DATA']) else "",
    axis=1
)

tabela = df_exibicao[['DATA', 'LOCAL', 'CAIXAS', 'FRASCOS', 'LATITUDE', 'LONGITUDE']]
linha_total = pd.DataFrame([{
    'DATA': 'Total',
    'LOCAL': '',
    'CAIXAS': tabela['CAIXAS'].sum(),
    'FRASCOS': tabela['FRASCOS'].sum(),
    'LATITUDE': '',
    'LONGITUDE': ''
}])
tabela_final = pd.concat([tabela, linha_total], ignore_index=True)
st.dataframe(tabela_final, use_container_width=True)

# Remanescentes reais: estoques declarados
if 'REMANESCENTES' in df.columns:
    df_estoque = df[df['REMANESCENTES'] > 0][['LOCAL', 'REMANESCENTES']].drop_duplicates()
    st.subheader("🧴 Locais com hipoclorito em estoque declarado")
    if not df_estoque.empty:
        st.dataframe(df_estoque.sort_values(by='REMANESCENTES', ascending=False), use_container_width=True)
    else:
        st.info("✅ Nenhum estoque declarado no campo 'REMANESCENTES'.")
else:
    st.warning("⚠️ Campo 'REMANESCENTES' não encontrado na planilha.")

# Mapa por LOCAL
st.subheader("🗺️ Mapa por Local")
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)

if dados.empty:
    st.warning("⚠️ Nenhuma entrega encontrada para os filtros selecionados.")
else:
    agrupados = dados.groupby(['LOCAL', 'LATITUDE', 'LONGITUDE'])['FRASCOS'].sum().reset_index()
    for _, row in agrupados.iterrows():
        lat = float(row['LATITUDE'])
        lon = float(row['LONGITUDE'])
        popup_text = f"{row['LOCAL']} - {row['FRASCOS']:.0f} frascos entregues no total"
        folium.Marker(location=[lat, lon], popup=popup_text).add_to(m)
    folium_static(m)
