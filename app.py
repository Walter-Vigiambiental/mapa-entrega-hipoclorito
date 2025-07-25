import pandas as pd
import streamlit as st

# 📥 Carregando os dados
df = pd.read_csv("dados_vacinas.csv", parse_dates=["DATA"])

# 🧹 Ordena os dados para garantir que o último lançamento seja o mais recente
df_ord = df.sort_values(by="DATA", ascending=True)

# 🔁 Agrupa por LOCAL, pega o último lançamento (linha mais recente)
últimos = df_ord.groupby("LOCAL").last().reset_index()

# 🧮 Calcula o estoque final com base nos critérios de entrega e remanescente
últimos["ESTOQUE_FINAL"] = últimos.apply(
    lambda row: row["REMANESCENTES"] if row["FRASCOS"] > 0 and row["REMANESCENTES"] > 0 else 0,
    axis=1
)

# 📊 Filtra os locais com estoque final maior que zero
últimos_filtrados = últimos[últimos["ESTOQUE_FINAL"] > 0][["LOCAL", "FRASCOS", "ESTOQUE_FINAL"]]
últimos_filtrados = últimos_filtrados.rename(columns={"FRASCOS": "ENTREGUES"})

# 🖼️ Interface Streamlit
st.set_page_config(page_title="Estoque Final", layout="wide")
st.title("💉 Estoque Final por Local (Último Lançamento)")
st.markdown("Tabela com os valores **mais recentes de remanescente** para cada local que teve entrega.")

# 📍 Tabela interativa
st.dataframe(últimos_filtrados, use_container_width=True, hide_index=True)

# 📢 Dica adicional
st.caption("Os dados refletem apenas o último registro de cada local, evitando somatórios cumulativos.")
