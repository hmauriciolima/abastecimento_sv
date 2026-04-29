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
    st.title("🔐 Acesso Santa Vergínia")
    senha = st.text_input("Senha de Acesso:", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["passwords"]["access_password"]:
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- CARREGAR DADOS DAS ABAS REAIS ---
@st.cache_data(ttl=60)
def carregar_listas():
    try:
        # Busca frotas da aba que você renomeou para FROTA
        df_frota = conn.read(worksheet="FROTA")
        frotas = df_frota["FROTA"].dropna().unique().tolist()
        
        # Busca locais da aba DIM_LOCAIS
        df_locais = conn.read(worksheet="DIM_LOCAIS")
        locais = df_locais["LOCAL_DESTINO"].dropna().unique().tolist()
        
        # Busca atividades da aba DIM_ATIVIDADES
        df_ativ = conn.read(worksheet="DIM_ATIVIDADES")
        ativs = df_ativ["ATIVIDADE"].dropna().unique().tolist()
        
        return frotas, locais, ativs
    except Exception as e:
        st.error(f"Erro ao ler as abas da planilha: {e}")
        return ["Erro ao carregar"], ["Erro ao carregar"], ["Erro ao carregar"]

frotas, locais, ativs = carregar_listas()

# --- INTERFACE ---
st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📍 Gestão de Fluxo")
        data_reg = st.date_input("Data do Registro", datetime.now())
        origem = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino = st.selectbox("Local / Destino", options=locais)
        atividade = st.selectbox("Atividade / Operação", options=ativs)

    with c2:
        st.subheader("🚜 Ativo / Equipamento")
        modelo = st.selectbox("Modelo do Equipamento", options=frotas)
        id_frota = st.text_input("ID Frota / Placa")
        
        ca, cb = st.columns(2)
        with ca:
            volume = st.number_input("Volume (Lts)", min_value=0.0)
        with cb:
            horimetro = st.number_input("Horímetro / KM", min_value=0.0)

if st.button("✅ SALVAR NO SISTEMA"):
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
        # Salva na aba principal ABASTECIMENTO
        df_atual = conn.read(worksheet="ABASTECIMENTO")
        df_final = pd.concat([df_atual, novo], ignore_index=True)
        conn.update(worksheet="ABASTECIMENTO", data=df_final)
        st.success("Registrado com sucesso!")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- HISTÓRICO ---
with st.expander("📊 Ver Últimos Registros"):
    if st.button("🔄 Atualizar"):
        st.dataframe(conn.read(worksheet="ABASTECIMENTO").tail(10))