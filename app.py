import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

# --- ESTILO CONTROLADORIA ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #1a365d; color: white; font-weight: bold; border-radius: 5px; height: 3em; }
    div[data-testid="stExpander"] { border: 1px solid #e6e9ef; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
try:
    SENHA_ACESSO = st.secrets["passwords"]["access_password"]
except:
    st.error("Configure 'access_password' nos Secrets.")
    st.stop()

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

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- HEADER ---
st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")
st.caption("Developed by Controladoria Santa Vergínia")

# --- FUNÇÃO DE CARREGAMENTO (Ajustada para os nomes da sua imagem) ---
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        # Lendo frotas da aba DIM_FROTA
        df_frota = conn.read(worksheet="DIM_FROTA", usecols=["FROTA"])
        frotas = df_frota["FROTA"].dropna().unique().tolist()
        
        # Lendo locais da aba DIM_LOCAIS
        df_locais = conn.read(worksheet="DIM_LOCAIS", usecols=["LOCAL_DESTINO"])
        locais = df_locais["LOCAL_DESTINO"].dropna().unique().tolist()
        
        # Lendo atividades da aba DIM_ATIVIDADES
        df_ativ = conn.read(worksheet="DIM_ATIVIDADES", usecols=["ATIVIDADE"])
        ativs = df_ativ["ATIVIDADE"].dropna().unique().tolist()
        
        return frotas, locais, ativs
    except Exception as e:
        # Se der erro, ele não trava o app, mostra opções padrão
        return ["ERRO NA ABA"], ["ERRO NA ABA"], ["ERRO NA ABA"]

frotas, locais, ativs = carregar_dados()

# --- INTERFACE ---
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📍 Gestão de Fluxo")
        data_reg = st.date_input("Data do Registro", datetime.now())
        origem = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino = st.selectbox("Local / Destino", options=locais)
        atividade = st.selectbox("Atividade", options=ativs)

    with c2:
        st.markdown("### 🚜 Ativo / Equipamento")
        modelo = st.selectbox("Equipamento", options=frotas)
        id_frota = st.text_input("ID / Placa (Ex: 3383)")
        
        ca, cb = st.columns(2)
        with ca:
            volume = st.number_input("Volume (Lts)", min_value=0.0)
        with cb:
            horimetro = st.number_input("Horímetro / KM", min_value=0.0)

if st.button("✅ VALIDAR E REGISTRAR"):
    if not id_frota or volume <= 0:
        st.error("Preencha os dados corretamente.")
    else:
        try:
            novo = pd.DataFrame([{
                "DATA": data_reg.strftime("%d/%m/%Y"),
                "ORIGEM": origem,
                "LOCAL_DESTINO": destino,
                "FROTA": modelo,
                "ID_FROTA": id_frota,
                "COMBUSTÍVEL": "DIESEL",
                "Qtde": volume,
                "HORIMETRO": horimetro,
                "ATIVIDADE": atividade
            }])
            df_atual = conn.read(worksheet="ABASTECIMENTO")
            df_final = pd.concat([df_atual, novo], ignore_index=True)
            conn.update(worksheet="ABASTECIMENTO", data=df_final)
            st.success("Registrado com sucesso!")
            st.balloons()
        except:
            st.error("Erro ao gravar. Verifique se a aba ABASTECIMENTO permite edição.")

with st.expander("📊 Histórico"):
    if st.button("Atualizar"):
        st.dataframe(conn.read(worksheet="ABASTECIMENTO").tail(10))