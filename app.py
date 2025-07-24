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

    # Remover espaços dos nomes das colunas
    df.columns = df.columns.str.strip()

    # Verificar se colunas essenciais existem
    required_cols = ['DATA', 'LATITUDE', 'LONGITUDE', 'LOCAL', 'QUANTIDADE']
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Coluna ausente na planilha: {col}")
            st.stop()

    # Converter data e extrair ano/mês
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month.astype('Int64')

    # Garantir que coordenadas sejam numéricas
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'], errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')

    # Remover linhas sem coordenadas válidas
    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])

    return df

df = load_data()

st.title("📍 Mapa de Entregas de Hipoclorito")
st.write("Visualize as entregas georreferenciadas por mês e ano.")

# Filtro de Ano
ano = st.selectbox("Filtrar por Ano", sorted(df['Ano'].dropna().unique()))

# Filtro de Mês com nomes legíveis
meses_disponiveis = sorted(df[df['Ano'] == ano]['Mês'].dropna().unique())
mes_nome = {m: calendar.month_name[m] for m in meses_disponiveis}
mes = st.selectbox("Filtrar por Mês", meses_disponiveis, format_func=lambda x: mes_nome.get(x, str(x)))

# Dados filtrados
dados_filtrados = df[(df['Ano'] == ano) & (df['Mês'] == mes)]

# Inicialização do mapa
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)

# Adição de marcadores
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
