import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px

# --- Carregando dados diretamente da planilha online (CSV)
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"
df = pd.read_csv(url)

# --- Conversão de coordenadas para colunas separadas
df[['LAT', 'LNG']] = df['COORDENADAS'].str.split(',', expand=True).astype(float)

# --- Filtros interativos
st.title("📦 Distribuição por Local e Mês")
local = st.selectbox("Filtrar por Local:", sorted(df['LOCAL'].unique()))
mes = st.selectbox("Filtrar por Mês:", sorted(df['MÊS'].unique()))

df_filtered = df[(df['LOCAL'] == local) & (df['MÊS'] == mes)]

# --- Gráfico por quantidade
st.subheader("📈 Quantidade por Data")
fig = px.bar(df_filtered, x='DATA', y='QUANTIDADE', color='LOCAL', title=f'Quantidade em {local} - {mes}')
st.plotly_chart(fig)

# --- Mapa interativo
st.subheader("🗺️ Mapa de Distribuição")
m = folium.Map(location=[-16.6, -43.9], zoom_start=9)
marker_cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    folium.Marker(
        location=[row['LAT'], row['LNG']],
        popup=f"{row['LOCAL']} - {row['QUANTIDADE']} unidades",
        tooltip=row['DATA']
    ).add_to(marker_cluster)

st_data = st_folium(m, width=700, height=500)

# --- Tabela de registros
st.subheader("📋 Registros")
st.dataframe(df_filtered)
