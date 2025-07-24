
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Mapa de Entrega de Hipoclorito", layout="wide")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados.csv")
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={
        "localidade": "localidade",
        "latitude": "latitude",
        "longitude": "longitude",
        "data": "data",
        "frascos": "quantidade",
        "mês": "mes",
        "ano": "ano"
    })

    df['latitude'] = df['latitude'].astype(str).str.replace("Â", "", regex=False)
    df['longitude'] = df['longitude'].astype(str).str.replace("Â", "", regex=False)

    df = df.dropna(subset=["latitude", "longitude", "quantidade"])
    df["latitude"] = df["latitude"].astype(float)
    df["longitude"] = df["longitude"].astype(float)
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0).astype(int)

    return df

df = carregar_dados()

st.sidebar.title("Filtros")

anos = ["Todos"] + sorted(df["ano"].dropna().unique().astype(str).tolist())
ano = st.sidebar.selectbox("Ano", anos)

meses = ["Todos"] + sorted(df["mes"].dropna().unique().astype(str).tolist())
mes = st.sidebar.selectbox("Mês", meses)

if ano != "Todos":
    df = df[df["ano"].astype(str) == ano]
if mes != "Todos":
    df = df[df["mes"].astype(str) == mes]

m = folium.Map(location=[-7.2, -39.3], zoom_start=8)
cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    popup = f"<b>{row['localidade']}</b><br>Entregue: {row['quantidade']} frascos<br>{row['mes']}/{row['ano']}"
    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=popup,
        icon=folium.Icon(color="blue", icon="tint", prefix="fa")
    ).add_to(cluster)

folium_static(m)
