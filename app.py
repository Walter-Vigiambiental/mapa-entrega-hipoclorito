import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# URL pública da planilha em formato CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)

    # Padronização dos campos de data e extração de ano/mês
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month

    # Remoção de linhas sem coordenadas válidas
    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    return df

df = load_data()

st.title("📍 Mapa de Entregas de Hipoclorito")
st.write("Visualize as entregas georreferenciadas por mês e ano.")

# Filtros interativos
ano = st.selectbox("Filtrar por Ano", sorted(df['Ano'].dropna().unique()))
mes = st.selectbox("Filtrar por Mês", sorted(df[df['Ano'] == ano]['Mês'].dropna().unique()))
dados_filtrados = df[(df['Ano'] == ano) & (df['Mês'] == mes)]

# Inicialização do mapa
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)  # Referência: Montes Claros

# Adição de marcadores com validação
for _, row in dados_filtrados.iterrows():
    try:
        lat = float(row['LATITUDE'])
        lon = float(row['LONGITUDE'])

        if pd.notnull(lat) and pd.notnull(lon):
            popup_text = f"{row['LOCAL']} - {row['QUANTIDADE']}L"
            folium.Marker(location=[lat, lon], popup=popup_text).add_to(m)
    except Exception:
        continue  # ignora linhas com problemas

# Renderização no Streamlit
folium_static(m)
