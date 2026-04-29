import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #1a365d; color: white; font-weight: bold; height: 3em; border-radius: 5px; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
""", unsafe_allow_html=True)

SHEET_ID = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid="

GID_ABASTECIMENTO = "0"
GID_FROTA         = "442677789"
GID_LOCAIS        = "343819585"
GID_ATIVIDADES    = "198196938"

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

# --- LEITURA ---
@st.cache_data(ttl=60)
def ler_aba(gid):
    return pd.read_csv(BASE_URL + gid)

@st.cache_data(ttl=60)
def carregar_listas():
    erros = []
    f_lista, l_lista, a_lista = [], [], []
    try:
        df_f = ler_aba(GID_FROTA)
        f_lista = df_f["VEICULOS_EQUIPAMENTOS"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ FROTA: {e}")
    try:
        l_lista = ler_aba(GID_LOCAIS)["LOCAL_DESTINO"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ DIM_LOCAIS: {e}")
    try:
        a_lista = ler_aba(GID_ATIVIDADES)["ATIVIDADE"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ DIM_ATIVIDADES: {e}")
    return f_lista, l_lista, a_lista, erros

frotas, locais, ativs, erros_carga = carregar_listas()
if erros_carga:
    for e in erros_carga:
        st.error(e)

# --- ESCRITA ---
def salvar_registro(novo):
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SHEET_ID).worksheet("ABASTECIMENTO")
    ws.append_row(list(novo.values()), value_input_option="USER_ENTERED")

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
            df_hist = ler_aba(GID_ABASTECIMENTO)
            st.dataframe(df_hist.tail(n), use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")