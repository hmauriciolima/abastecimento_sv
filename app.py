import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- LOGIN ---
SENHA_ACESSO = st.secrets["passwords"]["access_password"]

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Acesso Restrito - Controladoria SV")
    senha = st.text_input("Senha de Acesso:", type="password")
    if st.button("Entrar"):
        if senha == SENHA_ACESSO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- HEADER ---
st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")

# --- FUNÇÃO PARA LISTAR FROTA ---
@st.cache_data(ttl=600)
def listar_frotas():
    try:
        # Puxa os dados da aba 'EQUIPAMENTOS'
        df = conn.read(worksheet="EQUIPAMENTOS")
        return df['numero_frota'].tolist()
    except Exception as e:
        st.error(f"Erro ao ler lista de frotas: {e}")
        return ["Erro ao carregar"]

# --- INTERFACE ---
frotas = listar_frotas()

c1, c2 = st.columns(2)
with c1:
    st.subheader("📍 Gestão de Fluxo")
    data = st.date_input("Data do Registro")
    origem = st.radio("Origem", ["POSTO SEDE", "COMBOIO"])
    destino = st.selectbox("Destino", ["RETIRO POCO AZUL", "TIP", "SEDE"])

with c2:
    st.subheader("🚜 Ativo / Equipamento")
    # AQUI A LISTA VAI APARECER:
    modelo = st.selectbox("Modelo do Equipamento", options=frotas)
    id_frota = st.text_input("ID Frota / Placa")
    volume = st.number_input("Volume (Lts)", min_value=0.0)

if st.button("✅ SALVAR NO GOOGLE SHEETS"):
    # Lógica para salvar os dados na aba 'REGISTROS'
    st.success("Registrado com sucesso!")