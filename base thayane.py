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
    .dataframe { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÕES DE CARREGAMENTO (Separadas por Aba)
@st.cache_data(ttl=300)
def load_data_aba1():
    # Link da primeira aba (Inadimplência)
    url1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWTtNcaSZtXQ49eVKVbIPbOyC790vzrVDLIcsYeNAgM3jbmpPDLqKHlD3LlAH0qk9T-wuYYAmAGK9d/pub?output=csv"
    df = pd.read_csv(url1)
    df['Data de Envio'] = pd.to_datetime(df['Data de Envio'], errors='coerce')
    return df

@st.cache_data(ttl=300)
def load_data_aba2():
    # IMPORTANTE: Se o link da segunda aba for diferente, altere aqui. 
    # Geralmente links do Google Sheets para abas diferentes terminam com um 'gid' específico.
    url2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWTtNcaSZtXQ49eVKVbIPbOyC790vzrVDLIcsYeNAgM3jbmpPDLqKHlD3LlAH0qk9T-wuYYAmAGK9d/pub?output=csv"
    df = pd.read_csv(url2)
    df['Data de Envio'] = pd.to_datetime(df['Data de Envio'], errors='coerce')
    return df

try:
    # Carregando as bases
    df1_raw = load_data_aba1()
    df2_raw = load_data_aba2()

    # --- SIDEBAR GLOBAL ---
    st.sidebar.title("💎 Painel de Filtros")
    st.sidebar.markdown("---")
    
    # Filtro de Data que afeta todo o Dashboard
    all_dates = pd.concat([df1_raw['Data de Envio'], df2_raw['Data de Envio']]).dropna()
    min_date, max_date = all_dates.min().to_pydatetime(), all_dates.max().to_pydatetime()
    
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
        
        # Filtros específicos Aba 1
        list_seg = df1_raw['Seguradora'].unique()
        sel_seg = st.sidebar.multiselect("Filtrar Seguradoras (Aba 1)", list_seg, default=list_seg)
        
        # Aplicar Filtros
        mask1 = df1_raw['Seguradora'].isin(sel_seg)
        if len(date_range) == 2:
            mask1 &= (df1_raw['Data de Envio'].dt.date >= date_range[0]) & (df1_raw['Data de Envio'].dt.date <= date_range[1])
        df1 = df1_raw[mask1]

        # CARDS DE MÉTRICAS
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Notificações", len(df1))
        with c2:
            recorrencia = df1['Cliente'].value_counts()
            st.metric("Clientes Reincidentes", (recorrencia > 1).sum(), delta="Atenção", delta_color="inverse")
        with c3:
            top_s = df1['Seguradora'].mode()[0] if not df1.empty else "N/A"
            st.metric("Seguradora Líder", top_s)
        with c4:
            operador = df1['CPF do Usuário'].nunique() if 'CPF do Usuário' in df1.columns else 0
            st.metric("Operadores Ativos", operador)

        st.divider()

        # Evolução Temporal
        st.subheader("📈 Evolução de Envios")
        df_time1 = df1.groupby(df1['Data de Envio'].dt.date).size()
        st.area_chart(df_time1, color="#1e3a8a")

        # Seção de Volumes (Gráfico + Tabela lado a lado)
        col_v1, col_v2 = st.columns([1, 1])
        with col_v1:
            st.subheader("🏢 Volume por Seguradora")
            seg_counts = df1['Seguradora'].value_counts().reset_index()
            seg_counts.columns = ['Seguradora', 'Quantidade']
            st.bar_chart(seg_counts.set_index('Seguradora'), color="#3b82f6")
        with col_v2:
            st.subheader("📊 Tabela de Volumes")
            st.dataframe(seg_counts, use_container_width=True, hide_index=True)

        # Recorrência
        st.subheader("⚠️ Clientes com Múltiplos Avisos")
        st.dataframe(recorrencia[recorrencia > 1].reset_index().rename(columns={'index':'Cliente', 'Cliente':'Total'}), use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # ABA 2: LOGS DE ENVIO (NOVA)
    # ---------------------------------------------------------
    with tab_logs:
        st.header("Controle de Logs e Produtividade")
        
        # Filtro de Data Aba 2
        mask2 = pd.Series(True, index=df2_raw.index)
        if len(date_range) == 2:
            mask2 &= (df2_raw['Data de Envio'].dt.date >= date_range[0]) & (df2_raw['Data de Envio'].dt.date <= date_range[1])
        df2 = df2_raw[mask2]

        # CARDS DE LOGS
        l1, l2, l3 = st.columns(3)
        with l1: st.metric("Total de Envios (Logs)", len(df2))
        with l2:
            if 'Enviado Por' in df2.columns:
                top_sender = df2['Enviado Por'].mode()[0] if not df2.empty else "N/A"
                st.metric("Top Remetente", top_sender)
        with l3:
            status_envio = (df2['Status'] == 'Sucesso').sum() if 'Status' in df2.columns else "N/D"
            st.metric("Status Sucesso", status_envio)

        st.divider()

        # IDEIA BRILHANTE: Ranking de Assuntos (Categorização)
        st.subheader("📋 Assuntos Mais Frequentes")
        sub_col1, sub_col2 = st.columns([1.5, 1])
        
        if 'Assunto' in df2.columns:
            assuntos = df2['Assunto'].value_counts().head(10).reset_index()
            assuntos.columns = ['Assunto', 'Frequência']
            with sub_col1:
                st.bar_chart(assuntos.set_index('Assunto'), color="#10b981", horizontal=True)
            with sub_col2:
                st.dataframe(assuntos, use_container_width=True, hide_index=True)

        st.subheader("🔍 Histórico Completo de Logs")
        st.dataframe(df2, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao processar integração: {e}")
    st.info("Dica: Verifique se as colunas da nova aba estão escritas exatamente como no código.")
