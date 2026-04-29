import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGIN ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acesso SV")
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["passwords"]["access_password"]:
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- CARREGAR DADOS ---
@st.cache_data(ttl=60)
def carregar_listas():
    try:
        # Tenta ler as abas conforme a imagem da sua planilha
        frotas = conn.read(worksheet="DIM_FROTA")["FROTA"].dropna().unique().tolist()
        locais = conn.read(worksheet="DIM_LOCAIS")["LOCAL_DESTINO"].dropna().unique().tolist()
        ativs = conn.read(worksheet="DIM_ATIVIDADES")["ATIVIDADE"].dropna().unique().tolist()
        return frotas, locais, ativs
    except:
        # Se falhar, usa listas padrão para o app não travar
        return ["CARREGADEIRA VOLVO", "CAMINHÃO MB"], ["TIP", "SEDE"], ["CONTROLE DE PRAGAS"]

frotas, locais, ativs = carregar_listas()

# --- INTERFACE ---
st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")

c1, c2 = st.columns(2)
with c1:
    st.subheader("📍 Fluxo")
    data_reg = st.date_input("Data", datetime.now())
    origem = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
    destino = st.selectbox("Destino", options=locais)
    atividade = st.selectbox("Atividade", options=ativs)

with c2:
    st.subheader("🚜 Equipamento")
    modelo = st.selectbox("Equipamento", options=frotas)
    id_frota = st.text_input("ID / Placa")
    volume = st.number_input("Volume (Lts)", min_value=0.0)
    horimetro = st.number_input("Horímetro", min_value=0.0)

if st.button("✅ SALVAR REGISTRO"):
    try:
        novo = pd.DataFrame([{
            "DATA": data_reg.strftime("%d/%m/%Y"),
            "ORIGEM": origem,
            "LOCAL_DESTINO": destino,
            "FROTA": modelo,
            "ID_FROTA": id_frota,
            "Qtde": volume,
            "HORIMETRO": horimetro,
            "ATIVIDADE": atividade
        }])
        # Tenta salvar na aba ABASTECIMENTO
        df_atual = conn.read(worksheet="ABASTECIMENTO")
        df_final = pd.concat([df_atual, novo], ignore_index=True)
        conn.update(worksheet="ABASTECIMENTO", data=df_final)
        st.success("Salvo com sucesso!")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")