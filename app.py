import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# URL da planilha CSV publicada
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df['Ano'] = df['Data'].dt.year
    df['Mês'] = df['Data'].dt.month
    return df.dropna(subset=['Latitude', 'Longitude'])

df = load_data()

st.title("📍 Mapa de Entregas de Hipoclorito")
st.write("Filtre por ano e mês para visualizar as entregas georreferenciadas.")

# Filtros
ano = st.selectbox("Filtrar por Ano", sorted(df['Ano'].dropna().unique()))
mes = st.selectbox("Filtrar por Mês", sorted(df[df['Ano'] == ano]['Mês'].dropna().unique()))
dados_filtrados = df[(df['Ano'] == ano) & (df['Mês'] == mes)]

# Mapa
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)  # Centro aproximado de Montes Claros
for _, row in dados_filtrados.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=f"{row['Local']} - {row['Quantidade']}L"
    ).add_to(m)

folium_static(m)