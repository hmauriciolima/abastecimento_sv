import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #1a365d; color: white; font-weight: bold; height: 3em; border-radius: 5px; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- DIAGNÓSTICO TOTAL ---
st.subheader("🔍 DIAGNÓSTICO")
st.write("**Secrets:**", st.secrets["connections"]["gsheets"])

try:
    df_teste = conn.read()
    st.success(f"✅ Conexão OK! Colunas da 1ª aba: {df_teste.columns.tolist()}")
except Exception as e:
    st.error(f"❌ Falha total na conexão: {e}")

for aba in ["ABASTECIMENTO", "FROTA", "DIM_LOCAIS", "DIM_ATIVIDADES"]:
    try:
        df = conn.read(worksheet=aba)
        st.success(f"✅ Aba '{aba}' OK — {len(df)} linhas, colunas: {df.columns.tolist()}")
    except Exception as e:
        st.error(f"❌ Aba '{aba}': {e}")

st.divider()

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

ABA_FROTA      = "FROTA"
ABA_LOCAIS     = "DIM_LOCAIS"
ABA_ATIVIDADES = "DIM_ATIVIDADES"
ABA_REGISTRO   = "ABASTECIMENTO"

@st.cache_data(ttl=60)
def carregar_listas():
    erros = []
    f_lista, l_lista, a_lista = [], [], []
    try:
        df_frota = conn.read(worksheet=ABA_FROTA)
        f_lista = df_frota["FROTA"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ Aba '{ABA_FROTA}': {e}")
    try:
        df_locais = conn.read(worksheet=ABA_LOCAIS)
        l_lista = df_locais["LOCAL_DESTINO"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ Aba '{ABA_LOCAIS}': {e}")
    try:
        df_ativ = conn.read(worksheet=ABA_ATIVIDADES)
        a_lista = df_ativ["ATIVIDADE"].dropna().unique().tolist()
    except Exception as e:
        erros.append(f"❌ Aba '{ABA_ATIVIDADES}': {e}")
    return f_lista, l_lista, a_lista, erros

frotas, locais, ativs, erros_carga = carregar_listas()

if erros_carga:
    for e in erros_carga:
        st.error(e)

st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📍 Gestão de Fluxo")
        data_reg = st.date_input("Data do Registro", datetime.now())
        origem = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino = st.selectbox("Local / Destino", options=locais if locais else ["— sem dados —"])
        atividade = st.selectbox("Atividade / Operação", options=ativs if ativs else ["— sem dados —"])
    with c2:
        st.subheader("🚜 Ativo / Equipamento")
        modelo = st.selectbox("Modelo do Equipamento", options=frotas if frotas else ["— sem dados —"])
        id_frota = st.text_input("ID Frota / Placa")
        ca, cb = st.columns(2)
        with ca:
            volume = st.number_input("Volume (Lts)", min_value=0.0, step=1.0, format="%.1f")
        with cb:
            horimetro = st.number_input("Horímetro / KM", min_value=0.0, step=0.1, format="%.1f")

if st.button("✅ SALVAR NO SISTEMA"):
    if not id_frota.strip() or volume <= 0:
        st.warning("⚠️ Preencha ID Frota e Volume antes de salvar.")
    else:
        try:
            novo = pd.DataFrame([{
                "DATA":          data_reg.strftime("%d/%m/%Y"),
                "ORIGEM":        origem,
                "LOCAL_DESTINO": destino,
                "FROTA":         modelo,
                "ID_FROTA":      id_frota.strip().upper(),
                "COMBUSTÍVEL":   "DIESEL",
                "Qtde":          volume,
                "HORIMETRO":     horimetro,
                "ATIVIDADE":     atividade
            }])
            df_atual = conn.read(worksheet=ABA_REGISTRO)
            df_final = pd.concat([df_atual, novo], ignore_index=True)
            conn.update(worksheet=ABA_REGISTRO, data=df_final)
            st.cache_data.clear()
            st.success("✅ Registro salvo com sucesso!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

with st.expander("📊 Ver Últimos Registros"):
    col1, _ = st.columns([1, 4])
    with col1:
        n_registros = st.number_input("Qtd registros", min_value=5, max_value=100, value=10, step=5)
    if st.button("🔄 Atualizar Lista"):
        try:
            df_hist = conn.read(worksheet=ABA_REGISTRO)
            st.dataframe(df_hist.tail(n_registros), use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")