import streamlit as st
import pandas as pd
import folium
import calendar
from streamlit_folium import folium_static

# Link da planilha CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()

    # Extrair LATITUDE e LONGITUDE da coluna COORDENADAS
    if 'COORDENADAS' in df.columns:
        df[['LATITUDE', 'LONGITUDE']] = df['COORDENADAS'].str.split(',', expand=True)
        df['LATITUDE'] = pd.to_numeric(df['LATITUDE'].str.strip(), errors='coerce')
        df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'].str.strip(), errors='coerce')
    else:
        st.error("Coluna 'COORDENADAS' não encontrada.")
        st.stop()

    df['DATA'] = pd.to_datetime(df['DATA'], format="%d/%m/%Y", errors='coerce')
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month.astype('Int64')

    df['CAIXAS'] = pd.to_numeric(df['CAIXAS'], errors='coerce')
    df['FRASCOS'] = df['CAIXAS'] * 50  # Cada caixa = 50 frascos

    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])

    return df

df = load_data()

st.title("📦 Entregas de Hipoclorito")
st.write("Visualize os frascos entregues por mês, ano e local.")

# Filtros interativos
anos_disponiveis = sorted(df['Ano'].dropna().unique())
ano_opcoes = ["Todos"] + [str(a) for a in anos_disponiveis]
ano_selecionado = st.selectbox("Filtrar por Ano", options=ano_opcoes)

meses_disponiveis = sorted(df['Mês'].dropna().unique())
mes_opcoes = ["Todos"] + list(meses_disponiveis)
mes_format = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
mes_selecionado = st.selectbox(
    "Filtrar por Mês",
    options=mes_opcoes,
    format_func=lambda x: "Todos" if x == "Todos" else mes_format.get(x, str(x))
)

locais_disponiveis = sorted(df['LOCAL'].dropna().unique())
local_opcoes = ["Todos"] + locais_disponiveis
local_selecionado = st.selectbox("Filtrar por Local", options=local_opcoes)

# Aplicar filtros
dados = df.copy()
if ano_selecionado != "Todos":
    try:
        ano_int = int(float(ano_selecionado))
        dados = dados[dados['Ano'] == ano_int]
    except:
        st.error("Erro ao interpretar o ano.")
        st.stop()

if mes_selecionado != "Todos":
    try:
        mes_int = int(mes_selecionado)
        dados = dados[dados['Mês'] == mes_int]
    except:
        st.error("Erro ao interpretar o mês.")
        st.stop()

if local_selecionado != "Todos":
    dados = dados[dados['LOCAL'] == local_selecionado]

# Somatório total
total_frascos = dados['FRASCOS'].sum()
st.subheader("📋 Dados filtrados")
st.write(f"**Total entregue:** {total_frascos:.0f} frascos")

# Exibir DATA como "Janeiro 2024"
df_exibicao = dados.copy()
df_exibicao['DATA'] = df_exibicao.apply(
    lambda row: f"{mes_format.get(row['Mês'], '')} {int(row['Ano'])}" if pd.notnull(row['DATA']) else "",
    axis=1
)
st.dataframe(df_exibicao[['DATA', 'LOCAL', 'CAIXAS', 'FRASCOS', 'LATITUDE', 'LONGITUDE']])

# Mapa por LOCAL com total agrupado
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)

if dados.empty:
    st.warning("⚠️ Nenhuma entrega encontrada para os filtros selecionados.")
else:
    agrupados = dados.groupby(['LOCAL', 'LATITUDE', 'LONGITUDE'])['FRASCOS'].sum().reset_index()
    for _, row in agrupados.iterrows():
        try:
            lat = float(row['LATITUDE'])
            lon = float(row['LONGITUDE'])
            popup_text = f"{row['LOCAL']} - {row['FRASCOS']:.0f} frascos entregues no total"
            folium.Marker(location=[lat, lon], popup=popup_text).add_to(m)
        except:
            continue

    folium_static(m)
