import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Mapa de Entregas de Hipoclorito", layout="wide")
st.title("📍 Mapa Interativo de Entregas de Hipoclorito")

# LINK DA PLANILHA (Google Sheets CSV)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

# FUNÇÃO PARA CARREGAR OS DADOS (SEM CACHE)
def carregar_dados():
    df = pd.read_csv(CSV_URL)

    # Trata nomes de colunas esperados
    df.columns = df.columns.str.lower().str.strip()

    # Confere existência das colunas necessárias
    colunas_necessarias = {'localidade', 'data', 'quantidade', 'latitude', 'longitude'}
    if not colunas_necessarias.issubset(set(df.columns)):
        st.error(f"⚠️ Colunas obrigatórias ausentes: {colunas_necessarias - set(df.columns)}")
        return pd.DataFrame()

    # Converte data
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['Ano'] = df['data'].dt.year
    df['Mês'] = df['data'].dt.month
    return df.dropna(subset=['latitude', 'longitude'])

# Carrega os dados
df = carregar_dados()
if df.empty:
    st.stop()

# === FILTRO POR LOCALIDADE ===
localidades = st.sidebar.multiselect("📍 Localidades", sorted(df['localidade'].dropna().unique()))
if localidades:
    df = df[df['localidade'].isin(localidades)]

# === FILTROS DE TEMPO ===
anos_disponiveis = sorted(df['Ano'].dropna().unique())
meses_disponiveis = sorted(df['Mês'].dropna().unique())

col1, col2 = st.columns(2)
ano_sel = col1.selectbox("📆 Ano", options=["Todos"] + list(anos_disponiveis))
mes_sel = col2.selectbox("🗓️ Mês", options=["Todos"] + list(meses_disponiveis))

# Aplica filtros
df_filt = df.copy()
if ano_sel != "Todos":
    df_filt = df_filt[df_filt['Ano'] == ano_sel]
if mes_sel != "Todos":
    df_filt = df_filt[df_filt['Mês'] == mes_sel]

# Agrupa entregas por localidade/mês/ano
agrupado = df_filt.groupby(
    ['localidade', 'latitude', 'longitude', 'Ano', 'Mês'],
    as_index=False
)['quantidade'].sum()

# === MAPA ===
mapa = folium.Map(location=[-7.5, -39.0], zoom_start=7)
cluster = MarkerCluster().add_to(mapa)

for _, row in agrupado.iterrows():
    popup = f"""<b>Localidade:</b> {row['localidade']}<br>
    <b>Ano:</b> {int(row['Ano'])}<br>
    <b>Mês:</b> {int(row['Mês'])}<br>
    <b>Quantidade entregue:</b> {row['quantidade']} L"""
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup,
        icon=folium.Icon(color="blue", icon="tint", prefix="fa")
    ).add_to(cluster)

folium_static(mapa, width=1100, height=700)