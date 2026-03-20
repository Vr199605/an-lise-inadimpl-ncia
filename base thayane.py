import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DE LAYOUT E DESIGN PREMIUM
st.set_page_config(page_title="Seguros Intelligence Pro", layout="wide", page_icon="📊")

# CSS para Layout de Milhões
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 6px solid #1e3a8a;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #1e3a8a !important; 
        color: white !important; 
    }
    .stDataFrame { background-color: #ffffff; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÕES DE CARREGAMENTO (Links de Abas Diferentes)
@st.cache_data(ttl=300)
def load_data_aba1():
    # Link da Aba 1: Inadimplência
    url1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWTtNcaSZtXQ49eVKVbIPbOyC790vzrVDLIcsYeNAgM3jbmpPDLqKHlD3LlAH0qk9T-wuYYAmAGK9d/pub?output=csv"
    df = pd.read_csv(url1)
    df['Data de Envio'] = pd.to_datetime(df['Data de Envio'], errors='coerce')
    return df

@st.cache_data(ttl=300)
def load_data_aba2():
    # Link da Aba 2: Controle de Envios (Logs) - GID 204684460
    url2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWTtNcaSZtXQ49eVKVbIPbOyC790vzrVDLIcsYeNAgM3jbmpPDLqKHlD3LlAH0qk9T-wuYYAmAGK9d/pub?gid=204684460&single=true&output=csv"
    df = pd.read_csv(url2)
    df['Data de Envio'] = pd.to_datetime(df['Data de Envio'], errors='coerce')
    return df

try:
    df1_raw = load_data_aba1()
    df2_raw = load_data_aba2()

    # --- SIDEBAR GLOBAL ---
    st.sidebar.title("💎 Painel de Filtros")
    st.sidebar.markdown("---")
    
    # Filtro de Data Global (Combina datas das duas bases para o limite do seletor)
    all_dates = pd.concat([df1_raw['Data de Envio'], df2_raw['Data de Envio']]).dropna()
    min_date = all_dates.min().to_pydatetime() if not all_dates.empty else pd.Timestamp.now().to_pydatetime()
    max_date = all_dates.max().to_pydatetime() if not all_dates.empty else pd.Timestamp.now().to_pydatetime()
    
    date_range = st.sidebar.date_input(
        "Selecione o Período Geral",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # --- NAVEGAÇÃO POR ABAS ---
    tab_inadimplencia, tab_logs = st.tabs(["🏛️ Análise de Inadimplência", "📧 Controle de Envios (Logs)"])

    # ---------------------------------------------------------
    # ABA 1: INADIMPLÊNCIA
    # ---------------------------------------------------------
    with tab_inadimplencia:
        st.header("Gestão de Inadimplência e Seguradoras")
        list_seg = df1_raw['Seguradora'].unique() if 'Seguradora' in df1_raw.columns else []
        sel_seg = st.sidebar.multiselect("Filtrar Seguradoras (Aba 1)", list_seg, default=list_seg)
        
        mask1 = df1_raw['Seguradora'].isin(sel_seg) if 'Seguradora' in df1_raw.columns else pd.Series(True, index=df1_raw.index)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            mask1 &= (df1_raw['Data de Envio'].dt.date >= date_range[0]) & (df1_raw['Data de Envio'].dt.date <= date_range[1])
        df1 = df1_raw[mask1]

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Notificações", len(df1))
        with c2:
            rec = df1['Cliente'].value_counts() if 'Cliente' in df1.columns else pd.Series()
            st.metric("Clientes Reincidentes", (rec > 1).sum(), delta="Atenção", delta_color="inverse")
        with c3:
            top_s = df1['Seguradora'].mode()[0] if 'Seguradora' in df1.columns and not df1.empty else "N/A"
            st.metric("Seguradora Líder", top_s)
        with c4:
            op_count = df1['CPF do Usuário'].nunique() if 'CPF do Usuário' in df1.columns else 0
            st.metric("Operadores Ativos", op_count)

        st.divider()
        st.subheader("📈 Evolução de Envios")
        st.area_chart(df1.groupby(df1['Data de Envio'].dt.date).size(), color="#1e3a8a")

        col_v1, col_v2 = st.columns([1, 1])
        with col_v1:
            st.subheader("🏢 Volume por Seguradora")
            if 'Seguradora' in df1.columns:
                seg_counts = df1['Seguradora'].value_counts().reset_index()
                seg_counts.columns = ['Seguradora', 'Quantidade']
                st.bar_chart(seg_counts.set_index('Seguradora'), color="#3b82f6")
        with col_v2:
            st.subheader("📊 Tabela de Volumes")
            if 'Seguradora' in df1.columns:
                st.dataframe(seg_counts, use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # ABA 2: LOGS DE ENVIO (FOCO NA COLUNA 'ENVIADO POR')
    # ---------------------------------------------------------
    with tab_logs:
        st.header("Produtividade de Envios")
        
        mask2 = pd.Series(True, index=df2_raw.index)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            mask2 &= (df2_raw['Data de Envio'].dt.date >= date_range[0]) & (df2_raw['Data de Envio'].dt.date <= date_range[1])
        df2 = df2_raw[mask2]

        # CARDS DE PRODUTIVIDADE
        l1, l2, l3 = st.columns(3)
        with l1: st.metric("Volume de E-mails", len(df2))
        with l2:
            if 'Enviado Por' in df2.columns:
                top_p = df2['Enviado Por'].mode()[0] if not df2.empty else "N/A"
                st.metric("Operador Mais Ativo", top_p)
            else:
                st.metric("Operador Mais Ativo", "Coluna não encontrada")
        with l3:
            # Se não houver coluna status, assume total como sucesso para o card
            status_val = (df2['Status'] == 'Sucesso').sum() if 'Status' in df2.columns else len(df2)
            st.metric("Envios Confirmados", status_val)

        st.divider()

        # SEÇÃO DE PRODUTIVIDADE LIMPA (ENVIADO POR)
        st.subheader("👤 Ranking de Produtividade (Enviado Por)")
        if 'Enviado Por' in df2.columns:
            p_col1, p_col2 = st.columns([1.6, 1])
            
            prod_df = df2['Enviado Por'].value_counts().reset_index()
            prod_df.columns = ['Operador', 'Total de Envios']

            with p_col1:
                # Gráfico horizontal para clareza visual dos nomes
                st.bar_chart(prod_df.set_index('Operador'), color="#059669", horizontal=True)
            
            with p_col2:
                # Tabela limpa com os números exatos
                st.dataframe(prod_df, use_container_width=True, hide_index=True)
        else:
            st.warning("A coluna 'Enviado Por' não foi detectada nesta aba.")
        
        st.divider()

        # Detalhamento de Assuntos e Histórico
        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            st.subheader("📋 Assuntos Frequentes")
            if 'Assunto' in df2.columns:
                st.dataframe(df2['Assunto'].value_counts().head(10).reset_index().rename(columns={'count':'Qtd'}), use_container_width=True, hide_index=True)
        
        with col_sub2:
            st.subheader("🔍 Resumo de Logs Recentes")
            cols_log = [c for c in ['Data de Envio', 'Enviado Por', 'Status'] if c in df2.columns]
            st.dataframe(df2[cols_log].head(15), use_container_width=True, hide_index=True)

        with st.expander("📂 Abrir Base de Logs Completa (Aba 2)"):
            st.dataframe(df2, use_container_width=True)

except Exception as e:
    st.error(f"Erro na integração dos dados: {e}")
