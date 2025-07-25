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

# Filtrando dados de entrega
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

# Tabela de entregas
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

# 🎯 Estoques com remanescentes ajustados
df_estoque = df[df['REMANESCENTES'] > 0].copy()

if ano_selecionado != "Todos":
    df_estoque = df_estoque[df_estoque['Ano'] == int(ano_selecionado)]
if "Todos" not in mes_selecionados:
    df_estoque = df_estoque[df_estoque['Mês'].isin([int(m) for m in mes_selecionados])]
if local_selecionado != "Todos":
    df_estoque = df_estoque[df_estoque['LOCAL'] == local_selecionado]

# Incorporando data da última entrega por local
entregas_recentes = dados_entrega.groupby('LOCAL')['DATA'].max().reset_index().rename(columns={'DATA': 'ULTIMA_ENTREGA'})
df_estoque = pd.merge(df_estoque, entregas_recentes, on='LOCAL', how='left')

# Filtrar estoques que vieram depois da última entrega (ou sem entrega registrada)
df_estoque = df_estoque[(df_estoque['DATA'] >= df_estoque['ULTIMA_ENTREGA']) | df_estoque['ULTIMA_ENTREGA'].isna()].copy()

# Criação da coluna de data e mês/ano
df_estoque['DATA_ESTOQUE'] = pd.to_datetime({
    'year': df_estoque['Ano'],
    'month': df_estoque['Mês'],
    'day': 1
}, errors='coerce')
df_estoque['MÊS_ANO'] = df_estoque['DATA_ESTOQUE'].dt.month.map(mes_format).str.capitalize() + " " + df_estoque['DATA_ESTOQUE'].dt.year.astype(str)

# 💡 Ajuste do estoque final condicional
df_estoque['ESTOQUE_FINAL'] = df_estoque.apply(
    lambda row: 0 if pd.isna(row['CAIXAS']) or row['CAIXAS'] == 0 else row['REMANESCENTES'],
    axis=1
)

st.subheader("🧴 Locais com hipoclorito em estoque declarado")
if not df_estoque.empty:
    st.dataframe(
        df_estoque[['LOCAL', 'MÊS_ANO', 'ESTOQUE_FINAL']].drop_duplicates(),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("✅ Nenhum estoque declarado válido para este filtro.")

# 🗺️ Mapa de entregas
st.subheader("🗺️ Mapa de Entregas por Local")
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)
agrupados = dados_entrega.groupby(['LOCAL', 'LATITUDE', 'LONGITUDE'])['FRASCOS'].sum().reset_index()
for _, row in agrupados.iterrows():
    lat = float(row['LATITUDE'])
    lon = float(row['LONGITUDE'])
    texto = f"{row['LOCAL']} - {row['FRASCOS']:.0f} frascos entregues"
    folium.Marker(location=[lat, lon], popup=texto).add_to(m)
folium_static(m)

# 🗺️ Mapa de estoques
if not df_estoque.empty:
    st.subheader("🗺️ Estoques visíveis")
    mapa_estoque = folium.Map(location=[-17.89, -43.42], zoom_start=8)
    for _, row in df_estoque.iterrows():
        lat = float(row['LATITUDE'])
        lon = float(row['LONGITUDE'])
        estoque = int(row['ESTOQUE_FINAL'])
        texto_popup = f"{row['LOCAL']} - {estoque} frascos em estoque"
        folium.Marker(
            location=[lat, lon],
            popup=texto_popup,
            icon=folium.Icon(color='orange', icon='medkit', prefix='fa')
        ).add_to(mapa_estoque)
    folium_static(mapa_estoque)
