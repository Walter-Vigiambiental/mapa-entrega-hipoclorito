import streamlit as st
import pandas as pd
import folium
import calendar
from streamlit_folium import folium_static

# URL da planilha CSV publicada
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)

    # Limpar nomes de colunas
    df.columns = df.columns.str.strip()

    # Verificar colunas obrigatórias
    obrigatorias = ['DATA', 'LATITUDE', 'LONGITUDE', 'LOCAL', 'QUANTIDADE']
    for col in obrigatorias:
        if col not in df.columns:
            st.error(f"❌ Coluna ausente: {col}")
            st.stop()

    # Corrigir tipos
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'], errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')
    df['QUANTIDADE'] = pd.to_numeric(df['QUANTIDADE'], errors='coerce')

    # Extrair ano e mês como inteiros
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month.astype('Int64')

    # Remover linhas sem coordenadas
    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])

    return df

df = load_data()

st.title("📍 Mapa de Entregas de Hipoclorito")
st.write("Visualize as entregas georreferenciadas por mês e ano.")

# Filtro de Ano
anos = sorted(df['Ano'].dropna().unique())
ano = st.selectbox("Filtrar por Ano", anos)

# Filtro de Mês com nomes legíveis
meses_disponiveis = sorted(df[df['Ano'] == ano]['Mês'].dropna().unique())
mes_nome = {m: calendar.month_name[m] for m in meses_disponiveis}
mes = st.selectbox("Filtrar por Mês", meses_disponiveis, format_func=lambda x: mes_nome.get(x, str(x)))

# Filtrar dados
dados_filtrados = df[(df['Ano'] == ano) & (df['Mês'] == mes)]

# Mostrar dados filtrados para depuração
st.subheader("📋 Dados filtrados")
st.dataframe(dados_filtrados[['DATA', 'LOCAL', 'QUANTIDADE', 'LATITUDE', 'LONGITUDE']])

# Criar mapa
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)

if dados_filtrados.empty:
    st.warning("⚠️ Nenhuma entrega encontrada para o período selecionado.")
else:
    for _, row in dados_filtrados.iterrows():
        try:
            lat = float(row['LATITUDE'])
            lon = float(row['LONGITUDE'])
            popup_text = f"{row['LOCAL']} - {row['QUANTIDADE']}L"
            folium.Marker(location=[lat, lon], popup=popup_text).add_to(m)
        except Exception:
            continue

    folium_static(m)
