import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

# --- ESTILO VISUAL (CONTROLADORIA) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #1a365d; color: white; font-weight: bold; height: 3em; border-radius: 5px; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

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

# --- CARREGAR DADOS DAS ABAS ---
@st.cache_data(ttl=60)
def carregar_listas():
    try:
        # Lê a aba que você renomeou para FROTA
        df_frota = conn.read(worksheet="FROTA")
        frotas = df_frota["FROTA"].dropna().unique().tolist()
        
        # Lê a aba DIM_LOCAIS
        df_locais = conn.read(worksheet="DIM_LOCAIS")
        locais = df_locais["LOCAL_DESTINO"].dropna().unique().tolist()
        
        # Lê a aba DIM_ATIVIDADES
        df_ativ = conn.read(worksheet="DIM_ATIVIDADES")
        ativs = df_ativ["ATIVIDADE"].dropna().unique().tolist()
        
        return frotas, locais, ativs
    except Exception as e:
        st.error(f"Erro ao ler abas: {e}. Verifique se os nomes das colunas e abas estão corretos.")
        return [], [], []

frotas, locais, ativs = carregar_listas()

# --- INTERFACE ---
st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📍 Gestão de Fluxo")
        data_reg = st.date_input("Data do Registro", datetime.now())
        origem = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino = st.selectbox("Local / Destino", options=locais if locais else ["Erro ao carregar"])
        atividade = st.selectbox("Atividade / Operação", options=ativs if ativs else ["Erro ao carregar"])

    with c2:
        st.subheader("🚜 Ativo / Equipamento")
        modelo = st.selectbox("Modelo do Equipamento", options=frotas if frotas else ["Erro ao carregar"])
        id_frota = st.text_input("ID Frota / Placa")
        
        ca, cb = st.columns(2)
        with ca:
            volume = st.number_input("Volume (Lts)", min_value=0.0, step=1.0)
        with cb:
            horimetro = st.number_input("Horímetro / KM", min_value=0.0, step=0.1)

# --- BOTÃO SALVAR ---
if st.button("✅ SALVAR NO SISTEMA"):
    if not id_frota or volume <= 0:
        st.warning("⚠️ Preencha o ID da Frota e o Volume.")
    else:
        try:
            novo_registro = pd.DataFrame([{
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
            
            # Salva na aba ABASTECIMENTO
            df_atual = conn.read(worksheet="ABASTECIMENTO")
            df_final = pd.concat([df_atual, novo_registro], ignore_index=True)
            conn.update(worksheet="ABASTECIMENTO", data=df_final)
            
            st.success("✅ Registro realizado com sucesso!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao salvar na planilha: {e}")

# --- ABA DE HISTÓRICO ---
with st.expander("📊 Ver Últimos Registros"):
    if st.button("🔄 Atualizar Lista"):
        df_hist = conn.read(worksheet="ABASTECIMENTO")
        st.dataframe(df_hist.tail(10))