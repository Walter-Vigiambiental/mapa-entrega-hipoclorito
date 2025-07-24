import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# URL da planilha CSV publicada
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month
    return df.dropna(subset=['LATITUDE', 'LONGITUDE'])

df = load_data()

st.title("📍 Mapa de Entregas de Hipoclorito")
st.write("Filtre por ano e mês para visualizar as entregas georreferenciadas.")

# Filtros interativos
ano = st.selectbox("Filtrar por Ano", sorted(df['Ano'].dropna().unique()))
mes = st.selectbox("Filtrar por Mês", sorted(df[df['Ano'] == ano]['Mês'].dropna().unique()))
dados_filtrados = df[(df['Ano'] == ano) & (df['Mês'] == mes)]

# Construção do mapa
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)
for _, row in dados_filtrados.iterrows():
    folium.Marker(
        location=[row['LATITUDE'], row['LONGITUDE']],
        popup=f"{row['LOCAL']} - {row['QUANTIDADE']}L"
    ).add_to(m)

folium_static(m)
