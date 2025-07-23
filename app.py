import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

st.set_page_config(layout="wide")

# URL da planilha do Google Sheets
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4rNqe1-YHIaKxLgyEbhN0tNytQixaNJnVfcyI0PN6ajT0KXzIGlh_dBrWFs6R9QqCEJ_UTGp3KOmL/pub?gid=317759421&single=true&output=csv"
df = pd.read_csv(url)

# Padronizar nomes de colunas
df.columns = df.columns.str.strip().str.lower()

# Verificar existência da coluna 'data'
if 'data' not in df.columns:
    st.error("❌ A coluna 'Data' não foi encontrada. Verifique o nome da coluna na planilha.")
    st.stop()

# Converter a coluna 'data'
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['latitude', 'longitude'])

# Criar colunas auxiliares
df['ano'] = df['data'].dt.year
df['mes'] = df['data'].dt.month
meses_nome = {1:'Jan.', 2:'Fev.', 3:'Mar.', 4:'Abr.', 5:'Mai.', 6:'Jun.', 7:'Jul.', 8:'Ago.', 9:'Set.', 10:'Out.', 11:'Nov.', 12:'Dez.'}
df['mes_nome'] = df['mes'].map(meses_nome)

# Filtros
st.sidebar.title("Filtros")
ano = st.sidebar.selectbox("Ano", ["Todos"] + sorted(df['ano'].dropna().unique().tolist()))
mes = st.sidebar.selectbox("Mês", ["Todos"] + list(meses_nome.values()))
municipios = st.sidebar.multiselect("Municípios", sorted(df['municipio'].dropna().unique()), default=None)
tipo_solo = st.sidebar.multiselect("Tipo de Solo", sorted(df['tipo de solo'].dropna().unique()), default=None)

if ano != "Todos":
    df = df[df['ano'] == int(ano)]
if mes != "Todos":
    mes_num = {v: k for k, v in meses_nome.items()}[mes]
    df = df[df['mes'] == mes_num]
if municipios:
    df = df[df['municipio'].isin(municipios)]
if tipo_solo:
    df = df[df['tipo de solo'].isin(tipo_solo)]

# Mapa com cluster
st.header("🗺️ Mapa VigiSolo com Cluster")
m = folium.Map(location=[-9.6, -36.6], zoom_start=7)
cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    popup = f"""
    <b>Município:</b> {row['municipio']}<br>
    <b>Data:</b> {row['data'].date()}<br>
    <b>Tipo de Solo:</b> {row.get('tipo de solo', 'N/A')}<br>
    <b>Coordenadas:</b> ({row['latitude']}, {row['longitude']})
    """
    folium.Marker(location=[row['latitude'], row['longitude']], popup=popup).add_to(cluster)

folium_static(m, width=1200, height=600)