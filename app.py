import streamlit as st
import pandas as pd
import requests
from datetime import date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Abastecimento - SV", page_icon="⛽", layout="wide")

# 2. LOGOMARCA E CABEÇALHO
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    try:
        st.image("logo_sv.png.png", width=120)
    except:
        st.write("# 🚜")

with col_titulo:
    # Cabeçalho atualizado conforme sua solicitação
    st.markdown("# REGISTRO DE ABASTECIMENTO DE FROTA - SV")
    st.markdown("#### Supply Chain & Inventory Control | Developed by Controladoria")

st.divider()

# 3. CONFIGURAÇÕES DE LINKS
SHEET_ID = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbxFsbyZRJbbI1iUc5wqj12ad1YfEfbEDBIO25Oqwrn09Yg4qxC2a684bIl_5t2YUf8/exec"

# 4. FUNÇÕES PARA CARREGAR LISTAS DINÂMICAS DA PLANILHA
@st.cache_data(ttl=60)
def carregar_dados(aba, coluna):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={aba}"
    df = pd.read_csv(url)
    return df[coluna].dropna().unique().tolist()

try:
    lista_modelos = carregar_dados("DIM_FROTA", "VEICULOS_EQUIPAMENTOS")
    lista_locais = carregar_dados("DIM_LOCAIS", "LOCAL_DESTINO")
    lista_atividades = carregar_dados("DIM_ATIVIDADES", "ATIVIDADE")
except:
    st.error("Erro ao carregar listas. Verifique as abas DIM_FROTA, DIM_LOCAIS e DIM_ATIVIDADES.")
    lista_modelos, lista_locais, lista_atividades = ["ERRO"], ["ERRO"], ["ERRO"]

# 5. ESTILIZAÇÃO DO BOTÃO E RODAPÉ
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #007bff; color: white; font-weight: bold; font-size: 18px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #6c757d; text-align: center; padding: 10px; font-size: 13px; border-top: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

# 6. FORMULÁRIO DE LANÇAMENTO
with st.form("form_abastecimento", clear_on_submit=True):
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📍 Gestão de Fluxo")
        data_res = st.date_input("Data do Registro", date.today())
        origem_res = st.radio("Origem do Combustível (Estoque)", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino_res = st.selectbox("Centro de Custo / Destino", lista_locais)
        atividade_res = st.selectbox("Operação / Atividade", lista_atividades)
    
    with c2:
        st.subheader("🚜 Ativo / Equipamento")
        modelo_res = st.selectbox("Modelo do Equipamento", lista_modelos)
        id_frota_res = st.text_input("ID Frota / Placa (OBRIGATÓRIO)", placeholder="Ex: 1020, ABC-1234")
        combustivel_res = st.selectbox("Tipo de Insumo", ["DIESEL", "DIESEL S10", "GASOLINA", "ETANOL"])
        qtd_res = st.number_input("Volume Abastecido (Litros)", min_value=0.0, step=0.1, format="%.1f")
        horimetro_res = st.number_input("Horímetro / KM (Se não houver, use 0)", min_value=0.0, step=0.1, value=0.0)

    st.markdown("<br>", unsafe_allow_html=True)
    btn_salvar = st.form_submit_button("💾 VALIDAR E REGISTRAR MOVIMENTAÇÃO")

# 7. LOGÍSTICA DE ENVIO
if btn_salvar:
    if not id_frota_res:
        st.error("❌ ERRO: É obrigatório informar o ID da Frota ou Placa para o controle de estoque!")
    elif qtd_res <= 0:
        st.warning("⚠️ O volume deve ser maior que zero.")
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
                st.success(f"✅ MOVIMENTAÇÃO REGISTRADA! Ativo: {id_frota_res.upper()}")
                st.balloons()
            else:
                st.error("❌ Erro na integração com a planilha.")
        except:
            st.error("❌ Falha de conexão com o servidor de dados.")

st.markdown('<div class="footer">SUPPLY CHAIN SYSTEM | CONTROLADORIA SANTA VERGINIA - 2026</div>', unsafe_allow_html=True)
