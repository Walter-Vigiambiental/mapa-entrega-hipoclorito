import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

mes_format = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
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

st.title("📦 Entregas e Estoques de Hipoclorito")

anos = sorted(df['Ano'].dropna().astype(int).unique())
ano_selecionado = st.selectbox("Filtrar por Ano", options=["Todos"] + [str(a) for a in anos])

meses = sorted(df['Mês'].dropna().unique())
mes_selecionados = st.multiselect(
    "Filtrar por Mês",
    options=["Todos"] + list(meses),
    default=["Todos"],
    format_func=lambda x: "Todos" if x == "Todos" else mes_format.get(x, str(x)).capitalize()
)

locais = sorted(df['LOCAL'].dropna().unique())
local_selecionado = st.selectbox("Filtrar por Local", options=["Todos"] + locais)

# 🔍 Filtrando entregas
dados_entrega = df[df['CAIXAS'] > 0].copy()
if ano_selecionado != "Todos":
    dados_entrega = dados_entrega[dados_entrega['Ano'] == int(ano_selecionado)]
if "Todos" not in mes_selecionados:
    dados_entrega = dados_entrega[dados_entrega['Mês'].isin([int(m) for m in mes_selecionados])]
if local_selecionado != "Todos":
    dados_entrega = dados_entrega[dados_entrega['LOCAL'] == local_selecionado]

total_frascos = dados_entrega['FRASCOS'].sum()
st.subheader("📋 Entregas no período selecionado")
st.write(f"**Total entregue:** {total_frascos:.0f} frascos")

df_exibicao = dados_entrega.copy()
df_exibicao['DATA'] = df_exibicao['DATA'].dt.month.map(mes_format).str.capitalize() + " " + df_exibicao['DATA'].dt.year.astype(str)
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
st.dataframe(tabela_final, use_container_width=True, hide_index=True)

# 🆕 Tabela Consolidada: Apenas locais com estoque > 0
df_consolidado = df.copy()
agrupado = df_consolidado.groupby('LOCAL').agg({
    'FRASCOS': 'sum',
    'REMANESCENTES': 'sum'
}).reset_index()

agrupado['ESTOQUE_FINAL'] = agrupado.apply(
    lambda row: row['REMANESCENTES'] if row['FRASCOS'] > 0 and row['REMANESCENTES'] > 0 else 0,
    axis=1
)

agrupado = agrupado.rename(columns={
    'FRASCOS': 'ENTREGUES'
})

agrupado_filtrado = agrupado[agrupado['ESTOQUE_FINAL'] > 0].copy()

st.subheader("📍 Locais com Estoque Positivo")
st.dataframe(
    agrupado_filtrado[['LOCAL', 'ENTREGUES', 'ESTOQUE_FINAL']],
    use_container_width=True,
    hide_index=True
)

# 🗺️ Mapa de Entregas
st.subheader("🗺️ Mapa de Entregas por Local")
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)
agrupados_map = dados_entrega.groupby(['LOCAL', 'LATITUDE', 'LONGITUDE'])['FRASCOS'].sum().reset_index()
for _, row in agrupados_map.iterrows():
    lat = float(row['LATITUDE'])
    lon = float(row['LONGITUDE'])
    texto = f"{row['LOCAL']} - {row['FRASCOS']:.0f} frascos entregues"
    folium.Marker(location=[lat, lon], popup=texto).add_to(m)
folium_static(m)
