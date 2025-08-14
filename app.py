import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime
import plotly.express as px

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKVnXBBM5iqN_dl4N_Ys0m0MWgpIIr0ejqG1UzDR7Ede-OJ03uX1oU5Jjxi8wSuRDXHil1MD-JoFhG/pub?gid=202398924&single=true&output=csv"

mes_format = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}

@st.cache_data(ttl=0)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    df[['LATITUDE', 'LONGITUDE']] = df['COORDENADAS'].str.split(',', expand=True)
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'].str.strip(), errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'].str.strip(), errors='coerce')
    df['DATA'] = pd.to_datetime(df['DATA'], format="%d/%m/%Y", errors='coerce')
    df['Ano'] = df['DATA'].dt.year
    df['Mês'] = df['DATA'].dt.month.astype("Int64")
    df['CAIXAS'] = pd.to_numeric(df['CAIXAS'], errors='coerce')
    df['FRASCOS'] = df['CAIXAS'] * 50
    if 'REMANESCENTES' in df.columns:
        df['REMANESCENTES'] = pd.to_numeric(df['REMANESCENTES'], errors='coerce').fillna(0)
    df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    return df

df = load_data()

st.set_page_config(page_title="Distribuição Hipoclorito")
st.title("📦 Entregas e Estoques de Hipoclorito")

# 🔎 Filtros
anos = sorted(df['Ano'].dropna().astype(int).unique())
meses = sorted(df['Mês'].dropna().unique())
locais = sorted(df['LOCAL'].dropna().unique())

col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    ano_selecionado = st.selectbox("Ano", options=["Todos"] + [str(a) for a in anos])
with col2:
    mes_selecionados = st.multiselect(
        "Mês",
        options=["Todos"] + list(meses),
        default=["Todos"],
        format_func=lambda x: "Todos" if x == "Todos" else mes_format.get(x, str(x)).capitalize()
    )
with col3:
    local_selecionado = st.selectbox("Local", options=["Todos"] + locais)

# 📦 Entregas
dados_entrega = df[df['CAIXAS'] > 0].copy()
if ano_selecionado != "Todos":
    dados_entrega = dados_entrega[dados_entrega['Ano'] == int(ano_selecionado)]
if "Todos" not in mes_selecionados:
    dados_entrega = dados_entrega[dados_entrega['Mês'].isin([int(m) for m in mes_selecionados])]
if local_selecionado != "Todos":
    dados_entrega = dados_entrega[dados_entrega['LOCAL'] == local_selecionado]

total_frascos = dados_entrega['FRASCOS'].sum()
st.subheader("📋 Entregas no período selecionado")
st.write(f"**Total entregue:** {total_frascos:.0f} frascos")

# 🔄 Tabela resumida por local
tabela_agrupada = dados_entrega.groupby(['LOCAL'], as_index=False)[['CAIXAS', 'FRASCOS']].sum()
linha_total = pd.DataFrame([{
    'LOCAL': 'Total Geral',
    'CAIXAS': tabela_agrupada['CAIXAS'].sum(),
    'FRASCOS': tabela_agrupada['FRASCOS'].sum()
}])
tabela_final = pd.concat([tabela_agrupada, linha_total], ignore_index=True)

st.dataframe(
    tabela_final,
    use_container_width=True,
    column_config={
        "LOCAL": st.column_config.TextColumn(width="small"),
        "CAIXAS": st.column_config.NumberColumn(width="small"),
        "FRASCOS": st.column_config.NumberColumn(width="small"),
    },
    hide_index=True
)

# 🧴 Estoques válidos
df_filtrado = df.copy()
if ano_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Ano'] == int(ano_selecionado)]
if "Todos" not in mes_selecionados:
    df_filtrado = df_filtrado[df_filtrado['Mês'].isin([int(m) for m in mes_selecionados])]
if local_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['LOCAL'] == local_selecionado]

df_ordenado = df_filtrado.sort_values(by="DATA", ascending=True)
últimos_lançamentos = df_ordenado.groupby("LOCAL").last().reset_index()
estoques_validos = últimos_lançamentos[últimos_lançamentos['REMANESCENTES'] > 0].copy()
estoques_validos['MÊS_ANO'] = estoques_validos['DATA'].dt.month.map(mes_format).str.capitalize() + " " + estoques_validos['DATA'].dt.year.astype(str)

st.subheader("📋 Locais com hipoclorito em estoque declarado")
if not estoques_validos.empty:
    st.dataframe(
        estoques_validos[['LOCAL', 'MÊS_ANO', 'REMANESCENTES']],
        use_container_width=True,
        column_config={
            "LOCAL": st.column_config.TextColumn(width="small"),
            "MÊS_ANO": st.column_config.TextColumn(width="small"),
            "REMANESCENTES": st.column_config.NumberColumn(width="small"),
        },
        hide_index=True
    )
else:
    st.info("✅ Nenhum estoque declarado válido para este filtro.")

# 🗺️ Mapa de entregas
st.subheader("🗺️ Mapa de Entregas por Local")
m = folium.Map(location=[-17.89, -43.42], zoom_start=8)
agrupados = dados_entrega.groupby(['LOCAL', 'LATITUDE', 'LONGITUDE'])['FRASCOS'].sum().reset_index()
for _, row in agrupados.iterrows():
    folium.Marker(
        location=[row['LATITUDE'], row['LONGITUDE']],
        popup=f"{row['LOCAL']} - {row['FRASCOS']:.0f} frascos entregues"
    ).add_to(m)
folium_static(m)

# 🗺️ Mapa de estoques
if not estoques_validos.empty:
    st.subheader("🗺️ Estoques visíveis (Remanescentes > 0)")
    mapa_estoque = folium.Map(location=[-17.89, -43.42], zoom_start=8)
    for _, row in estoques_validos.iterrows():
        folium.Marker(
            location=[row['LATITUDE'], row['LONGITUDE']],
            popup=f"{row['LOCAL']} - {int(row['REMANESCENTES'])} frascos em estoque",
            icon=folium.Icon(color='orange', icon='medkit', prefix='fa')
        ).add_to(mapa_estoque)
    folium_static(mapa_estoque)

# 🔔 Alerta de locais sem entrega há mais de 1 mês
st.subheader("🔔 Locais sem entregas há mais de 1 mês")
hoje = pd.Timestamp.now().normalize()
última_entrega = df[df['FRASCOS'] > 0].groupby('LOCAL')['DATA'].max().reset_index()
última_entrega['DIAS_SEM_ENTREGA'] = (hoje - última_entrega['DATA']).dt.days
locais_alerta = última_entrega[última_entrega['DIAS_SEM_ENTREGA'] > 30].copy()

# 🔹 Garantir formato fixo
locais_alerta['DATA'] = locais_alerta['DATA'].dt.strftime('%d/%m/%Y')

if not locais_alerta.empty:
    for _, row in locais_alerta.iterrows():
        st.warning(
            f"⚠️ **{row['LOCAL']}** está há **{int(row['DIAS_SEM_ENTREGA'])} dias** sem entrega (última em {row['DATA']})"
        )

    # Exibir tabela formatada
    st.dataframe(
        locais_alerta[['LOCAL', 'DATA', 'DIAS_SEM_ENTREGA']],
        use_container_width=True,
        column_config={
            "LOCAL": st.column_config.TextColumn(width="small"),
            "DATA": st.column_config.TextColumn(width="small"),
            "DIAS_SEM_ENTREGA": st.column_config.NumberColumn(width="small"),
        },
        hide_index=True
    )

# 📊 Gráficos de TOP 5 entregas por local
ranking_entrega = dados_entrega.groupby('LOCAL', as_index=False)['FRASCOS'].sum()

# 🏆 Locais com mais entregas
top_5 = ranking_entrega.sort_values(by='FRASCOS', ascending=False).head(5)
fig_top = px.bar(
    top_5,
    x='FRASCOS',
    y='LOCAL',
    orientation='h',
    title='🏆 Locais com Mais Entregas',
    text='FRASCOS',
    color='FRASCOS',
    color_continuous_scale='Greens'
)
fig_top.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_top, use_container_width=True)

# 🐢 Locais com menos entregas
bottom_5 = ranking_entrega.sort_values(by='FRASCOS', ascending=True).head(5)
fig_bottom = px.bar(
    bottom_5,
    x='FRASCOS',
    y='LOCAL',
    orientation='h',
    title='⚠️ Locais com Menos Entregas',
    text='FRASCOS',
    color='FRASCOS',
    color_continuous_scale='Reds'
)
fig_bottom.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_bottom, use_container_width=True)

st.markdown("---")
st.caption("Desenvolvido por Walter Alves usando Streamlit.")



