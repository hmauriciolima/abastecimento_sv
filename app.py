import streamlit as st
import pandas as pd
import requests
from datetime import date

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira linha de comando Streamlit)
st.set_page_config(page_title="Abastecimento - Santa Verginia", page_icon="⛽", layout="wide")

# 2. LOGOMARCA E CABEÇALHO
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    try:
        # Tenta carregar a logo que você subiu no GitHub
        st.image("logo_sv.png", width=120)
    except:
        # Se a imagem ainda não estiver lá ou o nome estiver errado, mostra um ícone reserva
        st.write("# 🚜")

with col_titulo:
    st.markdown("## Agropecuária Santa Verginia")
    st.markdown("#### Registro de Abastecimento Digital")

st.divider()

# 3. CONFIGURAÇÕES DE LINKS (Google Sheets e Apps Script)
SHEET_ID = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbxFsbyZRJbbI1iUc5wqj12ad1YfEfbEDBIO25Oqwrn09Yg4qxC2a684bIl_5t2YUf8/exec"

# 4. ESTILIZAÇÃO CSS (Botão e Rodapé)
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #007bff; 
        color: white; 
        font-weight: bold; 
        font-size: 18px; 
    }
    .footer { 
        position: fixed; 
        left: 0; 
        bottom: 0; 
        width: 100%; 
        background-color: #f8f9fa; 
        color: #6c757d; 
        text-align: center; 
        padding: 10px; 
        font-size: 13px; 
        border-top: 1px solid #dee2e6; 
    }
    </style>
    """, unsafe_allow_html=True)

# 5. FUNÇÃO PARA CARREGAR A FROTA ATUALIZADA
@st.cache_data(ttl=60)
def carregar_frota():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=DIM_FROTA"
    try:
        df = pd.read_csv(url)
        return df['VEICULOS_EQUIPAMENTOS'].dropna().unique().tolist()
    except:
        return ["ERRO AO CONECTAR COM A PLANILHA"]

lista_veiculos = carregar_frota()

# 6. FORMULÁRIO DE ENTRADA DE DADOS
with st.form("form_abastecimento", clear_on_submit=True):
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📍 Operação")
        data_res = st.date_input("Data do Registro", date.today())
        origem_res = st.radio("Origem", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino_res = st.selectbox("Destino do Combustível", 
                             ["POSTO DE ABASTECIMENTO", "RETIRO SÃO JOSÉ", "RETIRO SANTA MARIA", "RETIRO SÃO JOÃO", "MANUTENÇÃO"])
        atividade_res = st.selectbox("Atividade", 
                               ["MANEJO", "LIMPEZA DE PASTO", "AGRICULTURA", "LOGÍSTICA", "ADMINISTRATIVO"])

    with c2:
        st.subheader("🚜 Equipamento")
        veiculo_res = st.selectbox("Selecione o Veículo/Trator", lista_veiculos)
        combustivel_res = st.selectbox("Tipo", ["DIESEL", "DIESEL S10", "GASOLINA", "ETANOL"])
        qtd_res = st.number_input("Quantidade (Litros)", min_value=0.0, step=0.1, format="%.1f")
        horimetro_res = st.number_input("Horímetro / KM", min_value=0.0, step=0.1)

    st.markdown("<br>", unsafe_allow_html=True)
    btn_salvar = st.form_submit_button("💾 REGISTRAR ABASTECIMENTO")

# 7. LÓGICA DE ENVIO PARA O GOOGLE SHEETS
if btn_salvar:
    if qtd_res > 0:
        pacote_dados = {
            "DATA": data_res.strftime("%d/%m/%Y"),
            "ORIGEM": origem_res,
            "LOCAL_DESTINO": destino_res,
            "FROTA": veiculo_res,
            "COMBUSTIVEL": combustivel_res,
            "Qtde": qtd_res,
            "HORIMETRO": horimetro_res,
            "ATIVIDADE": atividade_res
        }
        
        with st.spinner('Enviando para a Controladoria...'):
            try:
                envio = requests.post(URL_WEB_APP, json=pacote_dados)
                if envio.status_code == 200:
                    st.success(f"✅ REGISTRO SALVO! {veiculo_res} com {qtd_res} litros.")
                    st.balloons()
                else:
                    st.error("Erro no servidor do Google.")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")
    else:
        st.warning("⚠️ Informe a quantidade de litros.")

# 8. RODAPÉ FIXO (CRIADO EM 07/04/2026 - CONTROLADORIA-SV)
st.markdown("""
    <div class="footer">
        CRIADO EM 07/04/2026 - CONTROLADORIA-SV | Gestão de Abastecimento Santa Verginia
    </div>
    """, unsafe_allow_html=True)
