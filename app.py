import streamlit as st
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
import os
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÕES DE SEGURANÇA (Secrets) ---
# O código busca nos 'Secrets' do Streamlit Cloud ou no arquivo local secrets.toml
SENHA_BANCO = st.secrets.get("db_password", "VerginiaAgro2026")
PROJECT_ID = st.secrets.get("project_id", "yvakbrkllvavtnzywkor")
SENHA_ACESSO = st.secrets.get("access_password", "sv2026")

# --- CONEXÃO COM SUPABASE (POOLER PORTA 5432) ---
senha_safe = urllib.parse.quote_plus(SENHA_BANCO)
USUARIO = f"postgres.{PROJECT_ID}"
DB_URL = f"postgresql://{USUARIO}:{senha_safe}@aws-0-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

@st.cache_resource
def criar_engine_sql():
    return create_engine(DB_URL, pool_pre_ping=True)

def conectar_banco():
    return psycopg2.connect(DB_URL)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Abastecimento SV", layout="wide", page_icon="⛽")

# Estilo para manter o padrão da Controladoria
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { width: 100%; background-color: #1a365d; color: white; font-weight: bold; height: 3em; border-radius: 5px; }
    div[data-testid="stExpander"] { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Acesso Restrito - Controladoria SV")
    with st.container():
        senha_digitada = st.text_input("Senha de Acesso:", type="password")
        if st.button("Entrar"):
            if senha_digitada == SENHA_ACESSO:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# --- HEADER ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    if os.path.exists('logo.png.png'):
        st.image('logo.png.png', width=160)
with col_titulo:
    st.title("REGISTRO DE ABASTECIMENTO DE FROTA - SV")
    st.caption("Supply Chain & Inventory Control | Developed by Controladoria Santa Vergínia")

# --- FUNÇÕES DE DADOS ---
@st.cache_data(ttl=600)
def listar_frotas():
    try:
        conn = conectar_banco()
        df = pd.read_sql("SELECT numero_frota, descricao FROM dim_frota ORDER BY numero_frota", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame(columns=['numero_frota', 'descricao'])

# --- INTERFACE PRINCIPAL ---
aba1, aba2, aba3 = st.tabs(["⛽ Validar Movimentação", "📊 Histórico", "⚙️ Painel ADM"])

with aba1:
    df_frotas = listar_frotas()
    
    # Criando o layout em duas colunas conforme a imagem
    col_fluxo, col_ativo = st.columns(2)
    
    with col_fluxo:
        st.markdown("### 📍 Gestão de Fluxo")
        data_reg = st.date_input("Data do Registro", datetime.now())
        origem = st.radio("Origem do Combustível (Estoque)", ["POSTO SEDE", "COMBOIO"], horizontal=True)
        destino = st.selectbox("Centro de Custo / Destino", ["RETIRO POCO AZUL", "TIP", "RETIRO BARRA DO CERVO", "SEDE", "OUTROS"])
        atividade = st.selectbox("Operação / Atividade", ["APLICAÇÃO DE CORRETIVOS", "CONTROLE DE PRAGAS", "VIAGENS EXTERNAS", "TRATO BOVINO", "MANUTENÇÃO"])

    with col_ativo:
        st.markdown("### 🚜 Ativo / Equipamento")
        opcoes = [f"{r['numero_frota']} - {r['descricao']}" for _, r in df_frotas.iterrows()]
        modelo_sel = st.selectbox("Modelo do Equipamento", options=opcoes if opcoes else ["Carregando..."])
        id_frota = st.text_input("ID Frota / Placa (OBRIGATÓRIO)", placeholder="Ex: 1020, ABC-1234")
        tipo_insumo = st.selectbox("Tipo de Insumo", ["DIESEL", "GASOLINA", "ARLA 32", "LUBRIFICANTE"])
        
        c_vol, c_hor = st.columns(2)
        with c_vol:
            volume = st.number_input("Volume Abastecido (Litros)", min_value=0.0, step=1.0)
        with c_hor:
            horimetro = st.number_input("Horímetro / KM", min_value=0.0, step=0.1)

    st.markdown("---")
    if st.button("💾 VALIDAR E REGISTRAR MOVIMENTAÇÃO"):
        if not id_frota or volume <= 0:
            st.error("⚠️ Verifique o ID da Frota e o Volume Abastecido!")
        else:
            try:
                conn = conectar_banco()
                cur = conn.cursor()
                # Garante a existência da tabela
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS fato_abastecimento (
                        id SERIAL PRIMARY KEY,
                        data_abast DATE,
                        origem TEXT,
                        destino TEXT,
                        atividade TEXT,
                        modelo TEXT,
                        identificacao TEXT,
                        insumo TEXT,
                        volume NUMERIC,
                        horimetro NUMERIC,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO fato_abastecimento (data_abast, origem, destino, atividade, modelo, identificacao, insumo, volume, horimetro)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (data_reg, origem, destino, atividade, modelo_sel, id_frota, tipo_insumo, volume, horimetro))
                conn.commit()
                conn.close()
                st.success("✅ Abastecimento registrado com sucesso na base SV!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

with aba2:
    st.subheader("📊 Relatório de Abastecimentos")
    if st.button("🔄 Sincronizar Dados"):
        try:
            conn = conectar_banco()
            df_hist = pd.read_sql("SELECT * FROM fato_abastecimento ORDER BY criado_em DESC", conn)
            st.dataframe(df_hist, use_container_width=True)
            conn.close()
        except:
            st.info("Nenhum registro encontrado no banco de dados.")

with aba3:
    st.subheader("⚙️ Atualização de Cadastros")
    arquivo_csv = st.file_uploader("Upload CSV de Frota", type=['csv'])
    if arquivo_csv and st.button("🚀 ATUALIZAR LISTA DE FROTA"):
        try:
            df_novo = pd.read_csv(arquivo_csv, sep=None, engine='python', encoding='latin1')
            engine = criar_engine_sql()
            with engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE dim_frota CASCADE;"))
                df_novo.to_sql('dim_frota', conn, if_exists='append', index=False)
            st.success("Lista de frotas atualizada com sucesso!")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro na carga: {e}")

st.markdown("---")
st.caption(f"SUPPLY CHAIN SYSTEM | CONTROLADORIA SANTA VERGINIA - {datetime.now().year}")