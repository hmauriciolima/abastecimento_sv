import streamlit as st
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
import os
import urllib.parse
from datetime import datetime

# --- CONFIGURAÇÕES DE SEGURANÇA (Secrets do Streamlit) ---
SENHA_BANCO = st.secrets.get("db_password", "VerginiaAgro2026")
PROJECT_ID = st.secrets.get("project_id", "yvakbrkllvavtnzywkor")
SENHA_ACESSO = st.secrets.get("access_password", "sv2026")

# --- CONEXÃO COM SUPABASE ---
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

# CSS para customização (Logo e Cores)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #1a365d; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Acesso Restrito - Controladoria SV")
    senha_digitada = st.text_input("Senha de Acesso:", type="password")
    if st.button("Entrar"):
        if senha_digitada == SENHA_ACESSO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# --- HEADER COM LOGO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    # Ajuste o nome do arquivo da logo se necessário
    if os.path.exists('logo.png.png'):
        st.image('logo.png.png', width=150)
with col_titulo:
    st.title("REGISTRO DE ABASTECIMENTO DE FROTA - SV")
    st.caption("Supply Chain & Inventory Control | Developed by Controladoria")

# --- FUNÇÕES ---
@st.cache_data(ttl=600)
def listar_frotas():
    try:
        conn = conectar_banco()
        df = pd.read_sql("SELECT numero_frota, descricao FROM dim_frota ORDER BY numero_frota", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame(columns=['numero_frota', 'descricao'])

aba1, aba2, aba3 = st.tabs(["⛽ Registro", "📊 Histórico", "⚙️ Configurações"])

with aba1:
    df_frotas = listar_frotas()
    
    with st.container():
        st.subheader("📍 Gestão de Fluxo")
        c1, c2 = st.columns(2)
        with c1:
            data_hoje = st.date_input("Data do Registro", datetime.now())
            origem = st.radio("Origem do Combustível (Estoque)", ["POSTO SEDE", "COMBOIO"], horizontal=True)
            centro_custo = st.selectbox("Centro de Custo / Destino", ["RETIRO POCO AZUL", "TIP", "RETIRO BARRA DO CERVO", "SEDE"])
            operacao = st.selectbox("Operação / Atividade", ["APLICAÇÃO DE CORRETIVOS", "CONTROLE DE PRAGAS", "VIAGENS EXTERNAS", "TRATO BOVINO"])

        with c2:
            st.subheader("🚜 Ativo / Equipamento")
            opcoes_frota = [f"{row['numero_frota']} - {row['descricao']}" for _, row in df_frotas.iterrows()]
            frota_sel = st.selectbox("Modelo do Equipamento", options=opcoes_frota if opcoes_frota else ["Nenhum cadastrado"])
            id_frota = st.text_input("ID Frota / Placa (OBRIGATÓRIO)", placeholder="Ex: 1020, ABC-1234")
            tipo_insumo = st.selectbox("Tipo de Insumo", ["DIESEL", "GASOLINA", "ARLA 32", "LUBRIFICANTE"])
            
            col_dados1, col_dados2 = st.columns(2)
            with col_dados1:
                volume = st.number_input("Volume Abastecido (Litros)", min_value=0.0, step=0.1)
            with col_dados2:
                horimetro = st.number_input("Horímetro / KM", min_value=0.0, step=0.1)

    if st.button("💾 VALIDAR E REGISTRAR MOVIMENTAÇÃO"):
        if not id_frota:
            st.warning("⚠️ O campo ID Frota é obrigatório!")
        else:
            try:
                conn = conectar_banco()
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS fato_abastecimento (
                        id SERIAL PRIMARY KEY,
                        data_reg DATE,
                        origem TEXT,
                        destino TEXT,
                        operacao TEXT,
                        frota_modelo TEXT,
                        frota_id TEXT,
                        insumo TEXT,
                        volume NUMERIC,
                        horimetro NUMERIC,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO fato_abastecimento (data_reg, origem, destino, operacao, frota_modelo, frota_id, insumo, volume, horimetro)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (data_hoje, origem, centro_custo, operacao, frota_sel, id_frota, tipo_insumo, volume, horimetro))
                conn.commit()
                conn.close()
                st.success("✅ Abastecimento registrado com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

with aba2:
    st.subheader("📈 Histórico de Movimentações")
    if st.button("🔄 Atualizar Relatório"):
        try:
            conn = conectar_banco()
            df_hist = pd.read_sql("SELECT * FROM fato_abastecimento ORDER BY data_reg DESC", conn)
            st.dataframe(df_hist, use_container_width=True)
            conn.close()
        except:
            st.info("Nenhum registro encontrado.")

with aba3:
    st.subheader("⚙️ Atualizar Lista de Frota (CSV)")
    arquivo = st.file_uploader("Upload CSV", type=['csv'])
    if arquivo and st.button("🚀 Executar Carga"):
        try:
            df_imp = pd.read_csv(arquivo, sep=None, engine='python', encoding='latin1')
            engine = criar_engine_sql()
            with engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE dim_frota CASCADE;"))
                df_imp.to_sql('dim_frota', conn, if_exists='append', index=False)
            st.success("Frota atualizada!")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro: {e}")

st.markdown("---")
st.caption("SUPPLY CHAIN SYSTEM | CONTROLADORIA SANTA VERGINIA - 2026")