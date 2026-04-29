import streamlit as st
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
import gspread

st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #1a365d; color: white; font-weight: bold; height: 3em; border-radius: 5px; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO ---
SHEET_ID  = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
BASE_URL  = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

ABA_FROTA      = "FROTA"
ABA_LOCAIS     = "DIM_LOCAIS"
ABA_ATIVIDADES = "DIM_ATIVIDADES"
ABA_REGISTRO   = "ABASTECIMENTO"

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
        else:
            st.error("Senha incorreta!")
    st.stop()

# --- LEITURA VIA PANDAS (sem streamlit-gsheets) ---
@st.cache_data(ttl=60)
def ler_aba(nome):
    return pd.read_csv(BASE_URL + nome)

@st.cache_data(ttl=60)
def carregar_listas():
    erros = []
    f_lista, l_lista, a_lista = [], [], []
    try:
        df = ler_aba(ABA_FROTA)
        f_lista = df["FROTA"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ Aba '{ABA_FROTA}': {e}")
    try:
        df = ler_aba(ABA_LOCAIS)
        l_lista = df["LOCAL_DESTINO"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ Aba '{ABA_LOCAIS}': {e}")
    try:
        df = ler_aba(ABA_ATIVIDADES)
        a_lista = df["ATIVIDADE"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ Aba '{ABA_ATIVIDADES}': {e}")
    return f_lista, l_lista, a_lista, erros

frotas, locais, ativs, erros_carga = carregar_listas()

if erros_carga:
    for e in erros_carga:
        st.error(e)

# --- ESCRITA VIA GSPREAD ---
def salvar_registro(novo_registro):
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet(ABA_REGISTRO)
    ws.append_row(list(novo_registro.values()), value_input_option="USER_ENTERED")

# --- INTERFACE ---
st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📍 Gestão de Fluxo")
        data_reg  = st.date_input("Data do Registro", datetime.now())
        origem    = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino   = st.selectbox("Local / Destino", options=locais if locais else ["— sem dados —"])
        atividade = st.selectbox("Atividade / Operação", options=ativs if ativs else ["— sem dados —"])
    with c2:
        st.subheader("🚜 Ativo / Equipamento")
        modelo   = st.selectbox("Modelo do Equipamento", options=frotas if frotas else ["— sem dados —"])
        id_frota = st.text_input("ID Frota / Placa")
        ca, cb   = st.columns(2)
        with ca:
            volume    = st.number_input("Volume (Lts)", min_value=0.0, step=1.0, format="%.1f")
        with cb:
            horimetro = st.number_input("Horímetro / KM", min_value=0.0, step=0.1, format="%.1f")

if st.button("✅ SALVAR NO SISTEMA"):
    if not id_frota.strip() or volume <= 0:
        st.warning("⚠️ Preencha ID Frota e Volume antes de salvar.")
    else:
        try:
            novo = {
                "DATA":          data_reg.strftime("%d/%m/%Y"),
                "ORIGEM":        origem,
                "LOCAL_DESTINO": destino,
                "FROTA":         modelo,
                "ID_FROTA":      id_frota.strip().upper(),
                "COMBUSTÍVEL":   "DIESEL",
                "Qtde":          volume,
                "HORIMETRO":     horimetro,
                "ATIVIDADE":     atividade
            }
            salvar_registro(novo)
            st.cache_data.clear()
            st.success("✅ Registro salvo com sucesso!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

with st.expander("📊 Ver Últimos Registros"):
    col1, _ = st.columns([1, 4])
    with col1:
        n = st.number_input("Qtd registros", min_value=5, max_value=100, value=10, step=5)
    if st.button("🔄 Atualizar Lista"):
        try:
            df_hist = ler_aba(ABA_REGISTRO)
            st.dataframe(df_hist.tail(n), use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")