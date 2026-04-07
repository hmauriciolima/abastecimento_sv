import streamlit as st
import pandas as pd
import requests
from datetime import date

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre no topo)
st.set_page_config(page_title="Abastecimento - Santa Verginia", page_icon="⛽", layout="wide")

# ESTILIZAÇÃO PARA O CELULAR
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# ⛽ Registro de Abastecimento - Santa Verginia")
st.divider()

# 2. LINKS ATUALIZADOS (Google Sheets e seu Novo Web App)
SHEET_ID = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbxFsbyZRJbbI1iUc5wqj12ad1YfEfbEDBIO25Oqwrn09Yg4qxC2a684bIl_5t2YUf8/exec"

# 3. FUNÇÃO PARA LER A LISTA DE VEÍCULOS
@st.cache_data(ttl=60)
def carregar_frota():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=DIM_FROTA"
    try:
        df = pd.read_csv(url)
        return df['VEICULOS_EQUIPAMENTOS'].dropna().unique().tolist()
    except:
        return ["ERRO AO CARREGAR FROTA"]

lista_veiculos = carregar_frota()

# 4. FORMULÁRIO DE ENTRADA
with st.form("form_abastecimento", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Origem e Destino")
        data_res = st.date_input("Data", date.today())
        origem_res = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino_res = st.selectbox("Destino", ["POSTO DE ABASTECIMENTO", "RETIRO SÃO JOSÉ", "RETIRO SANTA MARIA", "RETIRO SÃO JOÃO", "MANUTENÇÃO"])
        atividade_res = st.selectbox("Atividade", ["MANEJO", "LIMPEZA DE PASTO", "AGRICULTURA", "LOGÍSTICA", "ADMINISTRATIVO"])
        
    with col2:
        st.subheader("🚜 Equipamento e Volume")
        veiculo_res = st.selectbox("Veículo/Equipamento", lista_veiculos)
        combustivel_res = st.selectbox("Combustível", ["DIESEL", "DIESEL S10", "GASOLINA", "ETANOL"])
        qtd_res = st.number_input("Litros", min_value=0.0, step=0.1, format="%.1f")
        horimetro_res = st.number_input("Horímetro/KM", min_value=0.0, step=0.1)

    st.markdown("---")
    btn_salvar = st.form_submit_button("💾 REGISTRAR ABASTECIMENTO")

# 5. LÓGICA DE ENVIO (POST)
if btn_salvar:
    if qtd_res > 0:
        dados = {
            "DATA": data_res.strftime("%d/%m/%Y"),
            "ORIGEM": origem_res,
            "LOCAL_DESTINO": destino_res,
            "FROTA": veiculo_res,
            "COMBUSTIVEL": combustivel_res,
            "Qtde": qtd_res,
            "HORIMETRO": horimetro_res,
            "ATIVIDADE": atividade_res
        }
        
        with st.spinner('Gravando na planilha...'):
            try:
                # Envia os dados para o Google Apps Script
                response = requests.post(URL_WEB_APP, json=dados)
                
                if response.status_code == 200:
                    st.success(f"✅ SUCESSO! Registro do {veiculo_res} salvo na planilha.")
                    st.balloons()
                else:
                    st.error(f"Erro no Google (Status {response.status_code})")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")
    else:
        st.warning("⚠️ Informe a quantidade de litros.")

st.markdown("<p style='text-align: center; color: gray;'>Santa Verginia - Gestão de Frota</p>", unsafe_allow_html=True)
