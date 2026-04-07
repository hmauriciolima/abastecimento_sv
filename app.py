import streamlit as st
import pandas as pd
import requests
from datetime import date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Abastecimento - Santa Verginia", page_icon="⛽", layout="wide")

# 2. LOGOMARCA E CABEÇALHO
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    try:
        # Nome do arquivo conforme o seu repositório no GitHub
        st.image("logo_sv.png.png", width=120)
    except:
        st.write("# 🚜")

with col_titulo:
    st.markdown("# REGISTRO DE ABASTECIMENTO DE FROTA - SANTA VERGINIA")
    st.markdown("#### Unidade de Gestão Digital")

st.divider()

# 3. CONFIGURAÇÕES DE LINKS (Substitua o URL_WEB_APP pelo seu link novo do Apps Script)
SHEET_ID = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbxFsbyZRJbbI1iUc5wqj12ad1YfEfbEDBIO25Oqwrn09Yg4qxC2a684bIl_5t2YUf8/exec"

# 4. FUNÇÕES PARA CARREGAR LISTAS DA PLANILHA
@st.cache_data(ttl=60)
def carregar_frota():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=DIM_FROTA"
    df = pd.read_csv(url)
    return df['VEICULOS_EQUIPAMENTOS'].dropna().unique().tolist()

@st.cache_data(ttl=60)
def carregar_locais():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=DIM_LOCAIS"
    df = pd.read_csv(url)
    return df['LOCAL_DESTINO'].dropna().unique().tolist()

# Carregando as listas
try:
    lista_modelos = carregar_frota()
    lista_locais = carregar_locais()
except:
    lista_modelos = ["ERRO AO CARREGAR FROTA"]
    lista_locais = ["ERRO AO CARREGAR LOCAIS"]

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
        st.subheader("📍 Detalhes da Operação")
        data_res = st.date_input("Data do Registro", date.today())
        origem_res = st.radio("Origem do Combustível", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino_res = st.selectbox("Local de Destino", lista_locais)
        atividade_res = st.selectbox("Atividade / Setor", ["MANEJO", "LIMPEZA DE PASTO", "AGRICULTURA", "LOGÍSTICA", "ADMINISTRATIVO"])
    
    with c2:
        st.subheader("🚜 Equipamento")
        modelo_res = st.selectbox("Modelo do Veículo/Equipamento", lista_modelos)
        
        # Campo de texto obrigatório para Identificação
        id_frota_res = st.text_input("Nº Frota / Placa / Cód. Galão (OBRIGATÓRIO)", 
                                     placeholder="Ex: 1020, ABC-1234, 0001")
        
        combustivel_res = st.selectbox("Tipo de Combustível", ["DIESEL", "DIESEL S10", "GASOLINA", "ETANOL"])
        qtd_res = st.number_input("Quantidade (Litros)", min_value=0.0, step=0.1, format="%.1f")
        
        # Valor padrão 0.0 para quem não tem horímetro
        horimetro_res = st.number_input("Horímetro / KM Atual (Se não tiver, use 0)", min_value=0.0, step=0.1, value=0.0)

    st.markdown("<br>", unsafe_allow_html=True)
    btn_salvar = st.form_submit_button("💾 REGISTRAR ABASTECIMENTO")

# 7. LÓGICA DE PROCESSAMENTO E ENVIO
if btn_salvar:
    if not id_frota_res:
        st.error("❌ ERRO: Você precisa informar a identificação (Nº Frota ou Placa)!")
    elif qtd_res <= 0:
        st.warning("⚠️ Informe a quantidade de litros abastecida.")
    else:
        pacote_dados = {
            "DATA": data_res.strftime("%d/%m/%Y"),
            "ORIGEM": origem_res,
            "LOCAL_DESTINO": destino_res,
            "VEICULO": modelo_res,      # Coluna D
            "ID_FROTA": id_frota_res.upper(), # Coluna E (Sempre em maiúsculo)
            "COMBUSTIVEL": combustivel_res,
            "Qtde": qtd_res,
            "HORIMETRO": horimetro_res,
            "ATIVIDADE": atividade_res
        }
        
        with st.spinner('Enviando dados para a Controladoria...'):
            try:
                envio = requests.post(URL_WEB_APP, json=pacote_dados)
                if envio.status_code == 200:
                    st.success(f"✅ REGISTRO SALVO COM SUCESSO! Frota: {id_frota_res.upper()}")
                    st.balloons()
                else:
                    st.error("❌ Erro ao salvar na planilha. Verifique a implantação do Script.")
            except Exception as e:
                st.error(f"❌ Falha na conexão: {e}")

# 8. RODAPÉ FIXO
st.markdown('<div class="footer">CRIADO EM 07/04/2026 - CONTROLADORIA-SV | Gestão de Abastecimento Digital</div>', unsafe_allow_html=True)
Lembrete Importante para o Apps Script:
Para que a coluna E receba o ID digitado corretamente, o seu código no Google Sheets deve estar assim:

JavaScript
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("ABASTECIMENTO");
  var data = JSON.parse(e.postData.contents);
  
  sheet.appendRow([
    data.DATA,          // A
    data.ORIGEM,        // B
    data.LOCAL_DESTINO, // C
    data.VEICULO,       // D
    data.ID_FROTA,      // E (Nova coluna)
    data.COMBUSTIVEL,   // F
    data.Qtde,          // G
    "",                 // H (Vazio para seu custo unitário)
    data.HORIMETRO,     // I
    data.ATIVIDADE      // J
  ]);
  
  return ContentService.createTextOutput("Sucesso");
}
