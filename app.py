import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# URL da planilha pública
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

# Meses em português
mes_format = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    df[['LATITUDE', 'LONGITUDE']] = df['COORDENADAS'].str.split(',', expand=True)
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'].str.strip(), errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'].str.strip(), errors='coerce')
    df['DATA'] = pd.to_datetime(df['DATA'], format="%d/%m/%Y", errors='coerce')
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month.astype("Int64")
    df['CAIXAS'] = pd.to_numeric(df['CAIXAS'], errors='coerce')
    df['FRASCOS'] = df['CAIXAS'] * 50
    if 'REMANESCENTES' in df.columns:
        df['REMANESCENTES'] = pd.to_numeric(df['REMANESCENTES'], errors='coerce').fillna(0)
    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    return df

df = load_data()

st.title("📦 Entregas de Hipoclorito")
st.write("Visualize os frascos entregues por mês, ano e local.")

# Filtros
ano_opcoes = ["Todos"] + sorted(df['Ano'].dropna().unique().astype(str).tolist())
ano_selecionado = st.selectbox("Filtrar por Ano", options=ano_opcoes)

mes_opcoes = ["Todos"] + sorted(df['Mês'].dropna().unique().tolist())
mes_selecionados = st.multiselect(
    "Filtrar por Mês",
    options=mes_opcoes,
    default=["Todos"],
    format_func=lambda x: "Todos" if x == "Todos" else mes_format.get(x, str(x))
)

local_opcoes = ["Todos"] + sorted(df['LOCAL'].dropna().unique().tolist())
local_selecionado = st.selectbox("Filtrar por Local", options=local_opcoes)

dados = df.copy()
if ano_selecionado != "Todos":
    try:
        dados = dados[dados['Ano'] == int(float(ano_selecionado))]
    except ValueError:
        st.error("Erro: ano inválido.")
        st.stop()

if "Todos" not in mes_selecionados:
    dados = dados[dados['Mês'].isin([int(m) for m in mes_selecionados])]

if local_selecionado != "Todos":
    dados = dados[dados['LOCAL'] == local_selecionado]

# Tabela principal
total_frascos = dados['FRASCOS'].sum()
st.subheader("📋 Dados filtrados")
st.write(f"**Total entregue:** {total_frascos:.0f} frascos")

dados['DATA'] = dados.apply(
    lambda row: f"{mes_format.get(row['Mês'], '')} {int(row['Ano'])}" if pd.notnull(row['DATA']) else "",
    axis=1
)

tabela = dados[['DATA', 'LOCAL', 'CAIXAS', 'FRASCOS', 'LATITUDE', 'LONGITUDE']].copy()
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

# Estoques com data posterior à última entrega no período filtrado
if 'REMANESCENTES' in dados.columns:
    dados['REMANESCENTES'] = pd.to_numeric(dados['REMANESCENTES'], errors='coerce').fillna(0)

    estoque_bruto = dados[dados['REMANESCENTES'] > 0][['LOCAL', 'REMANESCENTES', 'DATA', 'LATITUDE', 'LONGITUDE']]
    entregas_periodo = dados[dados['FRASCOS'] > 0][['LOCAL', 'DATA']].groupby('LOCAL')['DATA'].max().reset_index()
    entregas_periodo.rename(columns={'DATA': 'ULTIMA_ENTREGA'}, inplace=True)

    estoque_validado = pd.merge(estoque_bruto, entregas_periodo, on='LOCAL', how='left')
    estoque_validado = estoque_validado[
        (estoque_validado['DATA'] > estoque_validado['ULTIMA_ENTREGA']) | (estoque_validado['ULTIMA_ENTREGA'].isna())
    ].drop(columns=['ULTIMA_ENTREGA'])

    st.subheader("🧴 Locais com hipoclorito em estoque declarado (pós-entrega)")
    if not estoque_validado.empty:
        st.dataframe(estoque_validado[['LOCAL', 'REMANESCENTES']].sort_values(by='REMANESCENTES', ascending=False), use_container_width=True)
    else:
        st.info("✅ Não há estoque declarado após a última entrega registrada no período.")
else:
    st.warning("⚠️ Campo 'REMANESCENTES' não encontrado nos dados.")

# Mapa de entregas
st.subheader("🗺️ Mapa de Entregas por Local")
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)
agrupados = dados[dados['FRASCOS'] > 0].groupby(['LOCAL', 'LATITUDE', 'LONGITUDE'])['FRASCOS'].sum().reset_index()
for _, row in agrupados.iterrows():
    lat = float(row['LATITUDE'])
    lon = float(row['LONGITUDE'])
    texto = f"{row['LOCAL']} - {row['FRASCOS']:.0f} frascos entregues"
    folium.Marker(location=[lat, lon], popup=texto).add_to(m)
folium_static(m)

# Mapa de estoques
if not estoque_validado.empty:
    st.subheader("🗺️ Estoques visíveis (Remanescentes registrados após entrega)")
    mapa_remanescente = folium.Map(location=[-17.89, -43.42], zoom_start=8)
    for _, row in estoque_validado.iterrows():
        lat = float(row['LATITUDE'])
        lon = float(row['LONGITUDE'])
        estoque = int(row['REMANESCENTES'])
        texto = f"{row['LOCAL']} - {estoque} frascos em estoque"
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color='orange',
            fill=True,
            fill_color='orange',
            fill_opacity=0.7,
            popup=texto
        ).add_to(mapa_remanescente)
    folium_static(mapa_remanescente)
