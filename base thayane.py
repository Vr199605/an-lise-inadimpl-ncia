import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DE LAYOUT E DESIGN DE MILHÕES
st.set_page_config(page_title="Gestão de Seguros Pro", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-left: 5px solid #1a365d;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 10px 10px 0 0;
        gap: 10px;
        padding: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #1a365d !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÕES DE CARREGAMENTO DE DADOS (Duas Bases)
@st.cache_data(ttl=300)
def load_data_inadimplencia():
    # Base 1: Foco em Seguradoras e Inadimplência
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWTtNcaSZtXQ49eVKVbIPbOyC790vzrVDLIcsYeNAgM3jbmpPDLqKHlD3LlAH0qk9T-wuYYAmAGK9d/pub?output=csv"
    df = pd.read_csv(url)
    df['Data de Envio'] = pd.to_datetime(df['Data de Envio'])
    return df

@st.cache_data(ttl=300)
def load_data_envios():
    # Base 2: Foco em Logs de Envio
    url_v2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWTtNcaSZtXQ49eVKVbIPbOyC790vzrVDLIcsYeNAgM3jbmpPDLqKHlD3LlAH0qk9T-wuYYAmAGK9d/pub?output=csv" # Ajustar aqui se o link for diferente para a aba 2
    df = pd.read_csv(url_v2)
    df['Data de Envio'] = pd.to_datetime(df['Data de Envio'])
    return df

try:
    df1 = load_data_inadimplencia()
    df2 = load_data_envios()

    # --- SIDEBAR GLOBAL ---
    st.sidebar.title("💎 Filtros de Gestão")
    st.sidebar.markdown("---")
    
    # Filtro de Data Compartilhado (usando a base 1 como referência)
    min_d, max_d = df1['Data de Envio'].min().to_pydatetime(), df1['Data de Envio'].max().to_pydatetime()
    date_sel = st.sidebar.date_input("Período Geral", value=(min_d, max_d))

    # --- NAVEGAÇÃO POR ABAS DO DASHBOARD ---
    aba_inadimplencia, aba_logs_envio = st.tabs(["🏛️ Análise por Seguradora", "📧 Controle de Envios (Logs)"])

    # ---------------------------------------------------------
    # ABA 1: ANÁLISE DE INADIMPLÊNCIA (MANTENDO TUDO ANTERIOR)
    # ---------------------------------------------------------
    with aba_inadimplencia:
        st.header("Análise Estratégica de Inadimplência")
        
        # Filtro específico de Seguradora
        list_seg = df1['Seguradora'].unique()
        sel_seg = st.sidebar.multiselect("Filtrar Seguradoras", list_seg, default=list_seg)
        
        # Aplicar Filtros
        m1 = df1['Seguradora'].isin(sel_seg)
        if len(date_sel) == 2:
            m1 &= (df1['Data de Envio'].dt.date >= date_sel[0]) & (df1['Data de Envio'].dt.date <= date_sel[1])
        df1_f = df1[m1]

        # CARDS DE MILHÕES
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Notificações Totais", len(df1_f))
        with c2: 
            rec = df1_f['Cliente'].value_counts()
            st.metric("Clientes Reincidentes", (rec > 1).sum(), delta="Atenção", delta_color="inverse")
        with c3: 
            top_s = df1_f['Seguradora'].mode()[0] if not df1_f.empty else "N/A"
            st.metric("Seguradora c/ Maior Volume", top_s)
        with c4:
            taxa = (df1_f['Status'] == 'Enviado').mean() * 100
            st.metric("Eficiência de Disparo", f"{taxa:.1f}%")

        st.divider()

        # GRÁFICO DE ÁREA TEMPORAL
        st.subheader("📈 Evolução de Inadimplência")
        df_time = df1_f.groupby(df1_f['Data de Envio'].dt.date).size()
        st.area_chart(df_time, color="#1e3a8a")

        col_a, col_b = st.columns([1, 1.2])
        with col_a:
            st.subheader("⚠️ Clientes Recorrentes")
            df_rec = rec[rec > 1].reset_index()
            df_rec.columns = ['Cliente', 'Qtd Envios']
            st.dataframe(df_rec, use_container_width=True, hide_index=True)
        
        with col_b:
            st.subheader("🏢 Volume por Seguradora")
            t_seg, t_tab = st.tabs(["Gráfico", "Tabela Analítica"])
            seg_v = df1_f['Seguradora'].value_counts().reset_index()
            seg_v.columns = ['Seguradora', 'Quantidade']
            with t_seg: st.bar_chart(seg_v.set_index('Seguradora'), color="#3b82f6")
            with t_tab: st.dataframe(seg_v, use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # ABA 2: NOVA ANÁLISE DE LOGS (CONTROLE DE ENVIOS)
    # ---------------------------------------------------------
    with aba_logs_envio:
        st.header("Controle de Produtividade e Logs")
        
        # Filtros Base 2
        if len(date_sel) == 2:
            df2_f = df2[(df2['Data de Envio'].dt.date >= date_sel[0]) & (df2['Data de Envio'].dt.date <= date_sel[1])]
        else:
            df2_f = df2

        # CARDS DE LOGS
        l1, l2, l3 = st.columns(3)
        with l1: st.metric("Total de E-mails Enviados", len(df2_f))
        with l2: 
            top_sender = df2_f['Enviado Por'].mode()[0] if not df2_f.empty else "N/A"
            st.metric("Operador Mais Ativo", top_sender)
        with l3:
            status_ok = (df2_f['Status'] == 'Sucesso').sum() if 'Sucesso' in df2_f['Status'].values else len(df2_f)
            st.metric("Envios com Sucesso", status_ok)

        st.divider()

        # IDEIA BRILHANTE: Ranking de Assuntos mais Frequentes
        st.subheader("📋 Tipologia de Assuntos Enviados")
        subject_counts = df2_f['Assunto'].value_counts().head(10).reset_index()
        subject_counts.columns = ['Assunto', 'Frequência']
        
        c_sub1, c_sub2 = st.columns([1.5, 1])
        with c_sub1:
            st.bar_chart(subject_counts.set_index('Assunto'), color="#10b981", horizontal=True)
        with c_sub2:
            st.dataframe(subject_counts, use_container_width=True, hide_index=True)

        st.subheader("🔍 Histórico Detalhado de Envios")
        st.dataframe(df2_f[['Data de Envio', 'Enviado Por', 'Email Destinatário', 'Assunto', 'Status']], 
                     use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro na integração dos dados: {e}")
