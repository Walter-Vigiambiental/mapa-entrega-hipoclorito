import streamlit as st
import pandas as pd
import folium
import re
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

st.set_page_config(page_title="Mapa de Entregas de Hipoclorito", layout="wide")
st.title("📍 Mapa Interativo de Entregas de Hipoclorito")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

def limpar_coordenada(valor):
    if pd.isna(valor):
        return None
    valor = re.sub(r"[^0-9.\-]", "", str(valor))
    try:
        return float(valor)
    except:
        return None

def carregar_dados():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip().str.lower()
    df.rename(columns={
        'localidade': 'localidade',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'data': 'data',
        'frascos': 'quantidade',
        'mês': 'mes',
        'ano': 'ano'
    }, inplace=True)
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['latitude'] = df['latitude'].apply(limpar_coordenada)
    df['longitude'] = df['longitude'].apply(limpar_coordenada)
    df = df.dropna(subset=['localidade', 'latitude', 'longitude', 'quantidade', 'ano', 'mes'])
    return df

df = carregar_dados()

st.sidebar.header("Filtros")
localidades = st.sidebar.multiselect("📍 Localidades", sorted(df['localidade'].unique()))
anos = st.sidebar.selectbox("📆 Ano", options=["Todos"] + sorted(df['ano'].astype(str).unique()))
meses = st.sidebar.selectbox("🗓️ Mês", options=["Todos"] + sorted(df['mes'].astype(str).unique()))

if localidades:
    df = df[df['localidade'].isin(localidades)]
if anos != "Todos":
    df = df[df['ano'].astype(str) == anos]
if meses != "Todos":
    df = df[df['mes'].astype(str) == meses]

df_agrupado = df.groupby(['localidade', 'latitude', 'longitude', 'ano', 'mes'], as_index=False)['quantidade'].sum()

mapa = folium.Map(location=[-7.5, -39.0], zoom_start=7)
cluster = MarkerCluster().add_to(mapa)

for _, row in df_agrupado.iterrows():
    popup = f"""<b>Localidade:</b> {row['localidade']}<br>
    <b>Ano:</b> {row['ano']}<br>
    <b>Mês:</b> {row['mes']}<br>
    <b>Total entregue:</b> {int(row['quantidade'])} frascos"""
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup,
        icon=folium.Icon(color="blue", icon="tint", prefix="fa")
    ).add_to(cluster)

folium_static(mapa, width=1100, height=700)