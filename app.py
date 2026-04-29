import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #1a365d; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (Usando Secrets) ---
try:
    SENHA_ACESSO = st.secrets["passwords"]["access_password"]
except:
    st.error("Erro: Configure 'access_password' nos Secrets do Streamlit.")
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

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- HEADER ---
st.title("⛽ REGISTRO DE ABASTECIMENTO - SV")
st.markdown("---")

# --- BUSCA DE DADOS DAS ABAS ---
@st.cache_data(ttl=600)
def carregar_listas():
    try:
        # Busca frotas da aba DIM_FROTA
        df_frota = conn.read(worksheet="DIM_FROTA")
        lista_frota = df_frota['FROTA'].dropna().unique().tolist()
        
        # Busca locais da aba DIM_LOCAIS
        df_locais = conn.read(worksheet="DIM_LOCAIS")
        lista_locais = df_locais['LOCAL_DESTINO'].dropna().unique().tolist()
        
        # Busca atividades da aba DIM_ATIVIDADES
        df_ativ = conn.read(worksheet="DIM_ATIVIDADES")
        lista_ativ = df_ativ['ATIVIDADE'].dropna().unique().tolist()
        
        return lista_frota, lista_locais, lista_ativ
    except Exception as e:
        st.error(f"Erro ao carregar listas da planilha: {e}")
        return [], [], []

frotas, locais, atividades = carregar_listas()

# --- FORMULÁRIO ---
with st.container():
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📍 Gestão de Fluxo")
        data_reg = st.date_input("Data do Registro", datetime.now())
        origem = st.radio("Origem do Combustível", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino = st.selectbox("Local / Destino", options=locais if locais else ["Carregando..."])
        atividade = st.selectbox("Atividade / Operação", options=atividades if atividades else ["Carregando..."])

    with c2:
        st.subheader("🚜 Ativo / Equipamento")
        modelo = st.selectbox("Modelo do Equipamento", options=frotas if frotas else ["Carregando..."])
        id_frota = st.text_input("ID Frota / Placa (Ex: 3383)")
        
        col_aux1, col_aux2 = st.columns(2)
        with col_aux1:
            volume = st.number_input("Volume (Lts)", min_value=0.0, step=1.0)
        with col_aux2:
            horimetro = st.number_input("Horímetro / KM", min_value=0.0, step=0.1)

st.markdown("---")

# --- BOTÃO SALVAR ---
if st.button("✅ SALVAR REGISTRO NO SISTEMA"):
    if not id_frota or volume <= 0:
        st.warning("⚠️ Preencha o ID da Frota e o Volume.")
    else:
        try:
            # Prepara os dados para salvar
            novo_registro = pd.DataFrame([{
                "DATA": data_reg.strftime("%d/%m/%Y"),
                "ORIGEM": origem,
                "LOCAL_DESTINO": destino,
                "FROTA": modelo,
                "ID_FROTA": id_frota,
                "COMBUSTÍVEL": "DIESEL", # Padrão conforme imagem
                "Qtde": volume,
                "HORIMETRO": horimetro,
                "ATIVIDADE": atividade
            }])
            
            # Lê os dados existentes na aba ABASTECIMENTO
            df_atual = conn.read(worksheet="ABASTECIMENTO")
            df_final = pd.concat([df_atual, novo_registro], ignore_index=True)
            
            # Atualiza a planilha
            conn.update(worksheet="ABASTECIMENTO", data=df_final)
            
            st.success("✅ Abastecimento registrado com sucesso na aba ABASTECIMENTO!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- ABA DE HISTÓRICO ---
with st.expander("📊 Ver últimos registros"):
    if st.button("🔄 Atualizar Visualização"):
        df_hist = conn.read(worksheet="ABASTECIMENTO")
        st.dataframe(df_hist.tail(10))