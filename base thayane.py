import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA E LAYOUT DE MILHÕES
st.set_page_config(page_title="Inadimplência Intelligence", layout="wide", page_icon="📈")

# CSS Personalizado para Design Premium
st.markdown("""
    <style>
    /* Fundo do App */
    .stApp {
        background-color: #f8f9fa;
    }
    /* Estilização dos Cards de Métrica */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #edf2f7;
    }
    /* Títulos e Subtítulos */
    h1, h2, h3 {
        color: #1a365d;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }
    /* Tabelas e Dataframes */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO DE DADOS (Mantido)
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWTtNcaSZtXQ49eVKVbIPbOyC790vzrVDLIcsYeNAgM3jbmpPDLqKHlD3LlAH0qk9T-wuYYAmAGK9d/pub?output=csv"
    df = pd.read_csv(url)
    df['Data de Envio'] = pd.to_datetime(df['Data de Envio'])
    return df

try:
    df = load_data()

    # --- SIDEBAR (Mantida) ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135706.png", width=80) # Ícone decorativo
    st.sidebar.title("Configurações")
    
    min_date = df['Data de Envio'].min().to_pydatetime()
    max_date = df['Data de Envio'].max().to_pydatetime()
    
    date_range = st.sidebar.date_input(
        "Período de Análise",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    seguradoras_list = df['Seguradora'].unique()
    seguradoras_sel = st.sidebar.multiselect(
        "Filtrar Seguradoras",
        options=seguradoras_list,
        default=seguradoras_list
    )

    # Lógica de Filtro
    mask = (df['Seguradora'].isin(seguradoras_sel))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        mask &= (df['Data de Envio'].dt.date >= date_range[0]) & (df['Data de Envio'].dt.date <= date_range[1])
    
    df_filtered = df[mask]

    # --- HEADER ---
    st.title("🛡️ Intelligence Hub | Notificações")
    st.markdown("Monitoramento de performance operacional e controle de inadimplência.")

    # --- 7. CARDS COLORIDOS (Layout de Milhões) ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total de Envios", len(df_filtered))
    with m2:
        recorrencia = df_filtered['Cliente'].value_counts()
        clientes_reincidentes = (recorrencia > 1).sum()
        st.metric("Reincidência (Clientes)", clientes_reincidentes, delta="Crítico", delta_color="inverse")
    with m3:
        top_seg = df_filtered['Seguradora'].mode()[0] if not df_filtered.empty else "N/A"
        st.metric("Seguradora Principal", top_seg)
    with m4:
        # Nova métrica: Operador mais produtivo (exemplo de ideia brilhante)
        top_operador = df_filtered['CPF do Usuário'].mode()[0] if not df_filtered.empty else "N/A"
        st.metric("Operador em Destaque", f"ID: {str(top_operador)[:5]}...")

    st.divider()

    # --- 2. VISÃO TEMPORAL ---
    with st.container():
        st.subheader("📈 Fluxo de Notificações no Tempo")
        df_timeline = df_filtered.groupby(df_filtered['Data de Envio'].dt.date).size()
        st.area_chart(df_timeline, color="#3182ce") # Usei Area Chart para layout mais bonito

    st.divider()

    # --- SEÇÃO INTERMEDIÁRIA (Recorrência e Seguradoras) ---
    col_left, col_right = st.columns([1, 1.2])

    with col_left:
        # 1. Análise de Recorrência por Cliente
        st.subheader("⚠️ Foco em Reincidência")
        recorrencia_table = recorrencia[recorrencia > 1].reset_index()
        recorrencia_table.columns = ['Cliente', 'Envios']
        st.dataframe(recorrencia_table, use_container_width=True, hide_index=True)

    with col_right:
        # SOLICITAÇÃO: Gráfico + Tabela de Volumes por Seguradora
        st.subheader("🏢 Performance por Seguradora")
        tab_grafico, tab_tabela = st.tabs(["Visualização Gráfica", "Dados Analíticos"])
        
        seg_data = df_filtered['Seguradora'].value_counts().reset_index()
        seg_data.columns = ['Seguradora', 'Quantidade']

        with tab_grafico:
            st.bar_chart(seg_data.set_index('Seguradora'), color="#2c5282")
        
        with tab_tabela:
            st.dataframe(seg_data, use_container_width=True, hide_index=True)

    # --- DETALHAMENTO FINAL ---
    st.divider()
    with st.expander("📂 Abrir Base Completa Filtrada"):
        st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")