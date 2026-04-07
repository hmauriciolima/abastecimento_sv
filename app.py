import streamlit as st
import pandas as pd
import requests
from datetime import date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Abastecimento - SV", page_icon="⛽", layout="wide")

# 2. CABEÇALHO OTIMIZADO (TÍTULO E SUBTÍTULO NA MESMA LINHA)
col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    try:
        st.image("logo_sv.png.png", width=110)
    except:
        st.write("# 🚜")

with col_titulo:
    st.markdown(
        """
        <div style="display: flex; align-items: baseline; gap: 15px; padding-top: 10px;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700;">
                REGISTRO DE ABASTECIMENTO DE FROTA - SV
            </h1>
            <span style="font-size: 16px; color: #6c757d; font-weight: 400; padding-bottom: 5px;">
                Supply Chain & Inventory Control | Developed by Controladoria
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# 3. CONFIGURAÇÕES DE LINKS
SHEET_ID = "1wbpQ91qD4E8Jwj7w0cXPYqDl6ldJnApU-pJLb_0ZOoo"
# Link novo do Apps Script fornecido
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbwNwbiaBH4vcfcZzPukzxuHj_dVoFh9gO-ziCP-Z9SsfZy0-W_j27ay0nvWt2KnFx7m/exec"

# 4. FUNÇÕES PARA CARREGAR LISTAS DINÂMICAS DA PLANILHA
@st.cache_data(ttl=60)
def carregar_dados(aba, coluna):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={aba}"
    try:
        df = pd.read_csv(url)
        return df[coluna].dropna().unique().tolist()
    except Exception as e:
        return [f"Erro na aba {aba}"]

# Carrega as listas das suas abas DIM_FROTA, DIM_LOCAIS e DIM_ATIVIDADES
lista_modelos = carregar_dados("DIM_FROTA", "VEICULOS_EQUIPAMENTOS")
lista_locais = carregar_dados("DIM_LOCAIS", "LOCAL_DESTINO")
lista_atividades = carregar_dados("DIM_ATIVIDADES", "ATIVIDADE")

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

# 7. LOGÍSTICA DE ENVIO SINCROZINADA COM A PLANILHA (A até J)
if btn_salvar:
    if not id_frota_res:
        st.error("❌ ERRO: É obrigatório informar o ID da Frota!")
    elif qtd_res <= 0:
        st.warning("⚠️ O volume deve ser maior que zero.")
    else:
        pacote_dados = {
            "DATA": data_res.strftime("%d/%m/%Y"),
            "ORIGEM": origem_res,
            "LOCAL_DESTINO": destino_res,
            "VEICULO": modelo_res,      # Coluna D
            "ID_FROTA": id_frota_res.upper(), # Coluna E
            "COMBUSTIVEL": combustivel_res,
            "Qtde": qtd_res,
            "HORIMETRO": horimetro_res,
            "ATIVIDADE": atividade_res
        }
        
        try:
            envio = requests.post(URL_WEB_APP, json=pacote_dados)
            if envio.status_code == 200:
                st.success(f"✅ REGISTRO SALVO! Ativo: {id_frota_res.upper()}")
                st.balloons()
            else:
                st.error(f"❌ Erro na integração (Status: {envio.status_code}).")
        except Exception as e:
            st.error(f"❌ Falha de conexão: {e}")

st.markdown('<div class="footer">SUPPLY CHAIN SYSTEM | CONTROLADORIA SANTA VERGINIA - 2026</div>', unsafe_allow_html=True)
