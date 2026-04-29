import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuração imediata
st.set_page_config(page_title="Abastecimento SV", layout="wide")

# Login Simples
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    senha = st.text_input("Senha SV:", type="password")
    if st.button("Acessar"):
        if senha == st.secrets["passwords"]["access_password"]:
            st.session_state.auth = True
            st.rerun()
    st.stop()

# Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")

# TENTATIVA DE LEITURA (COM TRATAMENTO DE ERRO)
try:
    # Tenta ler a aba que vimos na sua foto
    df_frotas = conn.read(worksheet="DIM_FROTA")
    lista_frotas = df_frotas["FROTA"].dropna().unique().tolist()
except Exception as e:
    st.error(f"Erro ao conectar com a aba DIM_FROTA: {e}")
    lista_frotas = ["ERRO NA PLANILHA - VERIFICAR ABA"]

# INTERFACE
c1, c2 = st.columns(2)
with c1:
    origem = st.radio("Origem", ["POSTO SEDE", "COMBOIO"])
    # Aqui vou deixar fixo por enquanto para não travar o app se a aba DIM_LOCAIS falhar
    destino = st.selectbox("Destino", ["TIP", "RETIRO POCO AZUL", "RETIRO BARRA DO CERVO", "SEDE"])

with c2:
    # AQUI É ONDE ESTAVA TRAVANDO
    modelo = st.selectbox("Equipamento", options=lista_frotas)
    id_frota = st.text_input("ID / Placa")
    volume = st.number_input("Volume (Lts)", min_value=0.0)

if st.button("SALVAR REGISTRO"):
    st.info("Tentando salvar...")
    # Lógica de salvar...