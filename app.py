import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px

# --- Carregando os dados
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"
df = pd.read_csv(url)

# --- Limpeza de nomes de colunas
df.columns = df.columns.str.strip()

# --- Verificando colunas disponíveis
st.write("📋 Colunas encontradas:")
st.write(df.columns.tolist())

# --- Separando coordenadas
if 'COORDENADAS' in df.columns:
    df[['LAT', 'LNG']] = df['COORDENADAS'].str.split(',', expand=True).astype(float)

# --- Aplicando filtros seguros
if 'LOCAL' in df.columns and 'MÊS' in df.columns:
    st.title("📦 Distribuição por Local e Mês")
    
    locais = sorted(df['LOCAL'].dropna().unique())
    meses = sorted(df['MÊS'].dropna().unique())
    
    local = st.selectbox("Filtrar por Local:", locais)
    mes = st.selectbox("Filtrar por Mês:", meses)
    
    df_filtered = df[(df['LOCAL'] == local) & (df['MÊS'] == mes)]

    # --- Gráfico
    if not df_filtered.empty and 'DATA' in df.columns and 'QUANTIDADE' in df.columns:
        st.subheader("📈 Quantidade por Data")
        fig = px.bar(df_filtered, x='DATA', y='QUANTIDADE', color='LOCAL', title=f'Quantidade em {local} - {mes}')
        st.plotly_chart(fig)

    # --- Mapa interativo
    if 'LAT' in df.columns and 'LNG' in df.columns and 'QUANTIDADE' in df.columns:
        st.subheader("🗺️ Mapa de Distribuição")
        m = folium.Map(location=[-16.6, -43.9], zoom_start=9)
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in df.iterrows():
            folium.Marker(
                location=[row['LAT'], row['LNG']],
                popup=f"{row['LOCAL']} - {row['QUANTIDADE']} unidades",
                tooltip=row['DATA']
            ).add_to(marker_cluster)

        st_folium(m, width=700, height=500)

    # --- Tabela
    st.subheader("📋 Registros filtrados")
    st.dataframe(df_filtered)
else:
    st.warning("⚠️ As colunas 'LOCAL' e 'MÊS' não foram encontradas nos dados.")
