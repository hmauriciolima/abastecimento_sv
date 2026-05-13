import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

# Estilo para botões e campos
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #1a365d; color: white; font-weight: bold; height: 3em; border-radius: 5px; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Controladoria Santa Vergínia")
    senha = st.text_input("Senha de Acesso:", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["passwords"]["access_password"]:
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- CONFIGURAÇÕES DA PLANILHA ---
SHEET_ID = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid="

GID_ABASTECIMENTO = "0"
GID_FROTA         = "442677789"
GID_LOCAIS        = "343819585"
GID_ATIVIDADES    = "198196938"

# --- LEITURA DE DADOS ---
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        f = pd.read_csv(BASE_URL + GID_FROTA)["VEICULOS_EQUIPAMENTOS"].dropna().unique().tolist()
        l = pd.read_csv(BASE_URL + GID_LOCAIS)["LOCAL_DESTINO"].dropna().unique().tolist()
        a = pd.read_csv(BASE_URL + GID_ATIVIDADES)["ATIVIDADE"].dropna().unique().tolist()
        return f, l, a
    except:
        return [], [], []

frotas, locais, ativs = carregar_dados()

# --- FUNÇÃO DE SALVAMENTO BLINDADA ---
def salvar_registro(novo):
    # Converte secrets para dicionário manipulável
    info = st.secrets["gcp_service_account"].to_dict()
    
    # LIMPEZA DA CHAVE: Resolve o erro de PEM e InvalidByte
    # Trata tanto se você colou com \n ou se colou com quebras de linha reais
    info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
    
    creds = Credentials.from_service_account_info(
        info, 
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SHEET_ID).worksheet("ABASTECIMENTO")
    ws.append_row(list(novo.values()), value_input_option="USER_ENTERED")

# --- INTERFACE ---
st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")

c1, c2 = st.columns(2)
with c1:
    st.subheader("📍 Fluxo")
    data_reg = st.date_input("Data", datetime.now())
    origem = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
    destino = st.selectbox("Destino", options=locais if locais else ["—"])
    atividade = st.selectbox("Atividade", options=ativs if ativs else ["—"])

with c2:
    st.subheader("🚜 Equipamento")
    modelo = st.selectbox("Equipamento", options=frotas if frotas else ["—"])
    id_frota = st.text_input("ID / Placa").upper()
    ca, cb = st.columns(2)
    with ca:
        volume = st.number_input("Volume (Lts)", min_value=0.0, step=1.0)
    with cb:
        horimetro = st.number_input("Horímetro", min_value=0.0, step=0.1)

if st.button("✅ SALVAR NO SISTEMA"):
    if not id_frota or volume <= 0:
        st.warning("⚠️ Preencha o ID e o Volume.")
    else:
        try:
            dados_salvar = {
                "DATA": data_reg.strftime("%d/%m/%Y"),
                "ORIGEM": origem,
                "DESTINO": destino,
                "FROTA": modelo,
                "ID": id_frota,
                "COMBUST": "DIESEL",
                "QTD": volume,
                "HORIM": horimetro,
                "ATIV": atividade
            }
            salvar_registro(dados_salvar)
            st.success("✅ Salvo com sucesso!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
