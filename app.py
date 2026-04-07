import streamlit as st
import pandas as pd
import requests
from datetime import date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Abastecimento - SV", page_icon="⛽", layout="wide")

# 2. CABEÇALHO
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo_sv.png.png", width=110)
    except:
        st.write("# 🚜")

with col_titulo:
    st.markdown('<h1 style="margin-bottom: 0px; font-size: 2.2rem;">REGISTRO DE ABASTECIMENTO DE FROTA - SV</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.1rem; color: #6c757d; margin-top: 0px;">Supply Chain & Inventory Control | <span style="font-weight: bold;">Developed by Controladoria</span></p>', unsafe_allow_html=True)

st.divider()

# 3. LINKS (COLE O SEU NOVO LINK DO APPS SCRIPT AQUI)
SHEET_ID = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
URL_WEB_APP = "COLE_AQUI_O_NOVO_LINK_DO_APPS_SCRIPT"

# 4. CARREGAMENTO DE DADOS
@st.cache_data(ttl=60)
def carregar_dados(aba, coluna):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={aba}"
    try:
        df = pd.read_csv(url)
        return df[coluna].dropna().unique().tolist()
    except:
        return ["ERRO"]

lista_modelos = carregar_dados("DIM_FROTA", "VEICULOS_EQUIPAMENTOS")
lista_locais = carregar_dados("DIM_LOCAIS", "LOCAL_DESTINO")
lista_atividades = carregar_dados("DIM_ATIVIDADES", "ATIVIDADE")

# 5. FORMULÁRIO
with st.form("form_abastecimento", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📍 Gestão de Fluxo")
        data_res = st.date_input("Data", date.today())
        origem_res = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino_res = st.selectbox("Destino", lista_locais)
        atividade_res = st.selectbox("Operação", lista_atividades)
    with c2:
        st.subheader("🚜 Ativo")
        modelo_res = st.selectbox("Equipamento", lista_modelos)
        id_frota_res = st.text_input("ID Frota / Placa (OBRIGATÓRIO)")
        combustivel_res = st.selectbox("Insumo", ["DIESEL", "DIESEL S10", "GASOLINA", "ETANOL"])
        qtd_res = st.number_input("Litros", min_value=0.0, format="%.1f")
        horimetro_res = st.number_input("Horímetro / KM", min_value=0.0, value=0.0)

    btn_salvar = st.form_submit_button("💾 VALIDAR E REGISTRAR")

# 6. LOGÍSTICA DE ENVIO SINCROZINADA
if btn_salvar:
    if not id_frota_res:
        st.error("❌ Informe o ID da Frota!")
    else:
        pacote_dados = {
            "DATA": data_res.strftime("%d/%m/%Y"),
            "ORIGEM": origem_res,
            "LOCAL_DESTINO": destino_res,
            "VEICULO": modelo_res,
            "ID_FROTA": id_frota_res.upper(),
            "COMBUSTIVEL": combustivel_res,
            "Qtde": qtd_res,
            "HORIMETRO": horimetro_res,
            "ATIVIDADE": atividade_res
        }
        try:
            envio = requests.post(URL_WEB_APP, json=pacote_dados)
            if envio.status_code == 200:
                st.success("✅ REGISTRO REALIZADO COM SUCESSO!")
                st.balloons()
        except:
            st.error("❌ Erro de conexão.")

st.markdown('<div style="position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #6c757d; text-align: center; padding: 10px; font-size: 13px; border-top: 1px solid #dee2e6;">SUPPLY CHAIN SYSTEM | CONTROLADORIA SANTA VERGINIA - 2026</div>', unsafe_allow_html=True)
