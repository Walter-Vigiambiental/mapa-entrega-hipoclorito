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

def carregar_dados():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.lower().str.strip()

    # Ajusta nomes e cria quantidade
    df.rename(columns={
        'data': 'data',
        'caixas': 'caixas',
        'frascos': 'frascos',
        'mês': 'mês',
        'ano': 'ano'
    }, inplace=True)

    # Usa frascos como quantidade (você pode ajustar aqui)
    df['quantidade'] = df['frascos']

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['ano'] = df['data'].dt.year
    df['mês'] = df['data'].dt.month

    colunas_necessarias = {'localidade', 'latitude', 'longitude', 'quantidade', 'data'}
    if not colunas_necessarias.issubset(df.columns):
        st.error(f"⚠️ Colunas obrigatórias ausentes: {colunas_necessarias - set(df.columns)}")
        return pd.DataFrame()
    return df.dropna(subset=['latitude', 'longitude'])

df = carregar_dados()
if df.empty:
    st.stop()

# FILTRO POR LOCALIDADE
localidades = st.sidebar.multiselect("📍 Localidades", sorted(df['localidade'].dropna().unique()))
if localidades:
    df = df[df['localidade'].isin(localidades)]

# FILTROS DE ANO E MÊS
anos_disponiveis = sorted(df['ano'].dropna().unique())
meses_disponiveis = sorted(df['mês'].dropna().unique())

col1, col2 = st.columns(2)
ano_sel = col1.selectbox("📆 Ano", options=["Todos"] + list(anos_disponiveis))
mes_sel = col2.selectbox("🗓️ Mês", options=["Todos"] + list(meses_disponiveis))

df_filt = df.copy()
if ano_sel != "Todos":
    df_filt = df_filt[df_filt['ano'] == ano_sel]
if mes_sel != "Todos":
    df_filt = df_filt[df_filt['mês'] == mes_sel]

agrupado = df_filt.groupby(
    ['localidade', 'latitude', 'longitude', 'ano', 'mês'],
    as_index=False
)['quantidade'].sum()

mapa = folium.Map(location=[-7.5, -39.0], zoom_start=7)
cluster = MarkerCluster().add_to(mapa)

for _, row in agrupado.iterrows():
    popup = f"""<b>Localidade:</b> {row['localidade']}<br>
    <b>Ano:</b> {int(row['ano'])}<br>
    <b>Mês:</b> {int(row['mês'])}<br>
    <b>Quantidade entregue:</b> {row['quantidade']} frascos"""
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup,
        icon=folium.Icon(color="blue", icon="tint", prefix="fa")
    ).add_to(cluster)

folium_static(mapa, width=1100, height=700)