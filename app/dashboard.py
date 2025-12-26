"""
PRINAD - Streamlit Dashboard v2.0
Real-time dashboard for monitoring credit risk classifications.
Features:
- Timeline chart at the top
- Streaming controls in sidebar
- Continuous auto-refresh with streaming
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import time
from typing import Dict, Any, List
import threading

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="PRINAD Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and modern look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        color: #9ca3af;
        font-size: 1rem;
        margin-top: 0;
    }
    .stMetric {
        background-color: rgba(28, 131, 225, 0.1);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid rgba(28, 131, 225, 0.2);
    }
    .streaming-on {
        background-color: #22c55e;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        text-align: center;
        animation: pulse 1.5s infinite;
    }
    .streaming-off {
        background-color: #6b7280;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        text-align: center;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    .rating-pill {
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Rating colors
RATING_COLORS = {
    'A1': '#22c55e', 'A2': '#4ade80', 'A3': '#86efac',
    'B1': '#eab308', 'B2': '#facc15',
    'B3': '#f97316',
    'C1': '#ef4444', 'C2': '#f87171',
    'D': '#1f2937'
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'streaming_active' not in st.session_state:
    st.session_state.streaming_active = False
if 'last_count' not in st.session_state:
    st.session_state.last_count = 0
if 'stream_start_time' not in st.session_state:
    st.session_state.stream_start_time = None

# ============================================================================
# API FUNCTIONS
# ============================================================================

def get_api_url():
    """Get API URL from session state or default."""
    return st.session_state.get('api_url', 'http://localhost:8000')

def check_api_health() -> Dict[str, Any]:
    """Check API health status."""
    try:
        response = requests.get(f"{get_api_url()}/health", timeout=3)
        return response.json()
    except:
        return {"status": "offline", "model_loaded": False}

def get_metrics() -> Dict[str, Any]:
    """Get API metrics."""
    try:
        response = requests.get(f"{get_api_url()}/metrics", timeout=3)
        return response.json()
    except:
        return {}

def get_avaliacoes(limit: int = 100) -> List[Dict[str, Any]]:
    """Get evaluations from API."""
    try:
        response = requests.get(f"{get_api_url()}/avaliacoes?limit={limit}", timeout=3)
        data = response.json()
        return data.get('avaliacoes', [])
    except:
        return []

def get_stats() -> Dict[str, Any]:
    """Get aggregated stats from API."""
    try:
        response = requests.get(f"{get_api_url()}/stats", timeout=3)
        return response.json()
    except:
        return {}

def clear_avaliacoes():
    """Clear all evaluations."""
    try:
        response = requests.delete(f"{get_api_url()}/avaliacoes", timeout=3)
        return True
    except:
        return False

def send_streaming_request() -> Dict[str, Any]:
    """Send a single streaming request to the API."""
    import random
    
    # Generate random client data
    ocupacoes = ['ASSALARIADO', 'AUTONOMO', 'EMPRESARIO', 'APOSENTADO', 'SERVIDOR PUBLICO', 'PENSIONISTA']
    escolaridades = ['FUNDAM', 'MEDIO', 'SUPERIOR', 'POS']
    
    # Generate random CPF
    cpf = ''.join([str(random.randint(0, 9)) for _ in range(11)])
    
    # Weighted random selections
    sistemas = ['app_mobile'] * 50 + ['sis_agencia'] * 30 + ['terminal_eletronico'] * 15 + ['central_cliente'] * 5
    produtos = ['consignado'] * 40 + ['banparacard'] * 20 + ['cartao_credito'] * 20 + ['imobiliario'] * 10 + ['antecipacao_13_sal'] * 5 + ['cred_veiculo'] * 3 + ['energia_solar'] * 2
    tipos = ['Proposta'] * 70 + ['Contratacao'] * 30
    
    # Profile type for behavioral data - more nuanced distribution
    # Creates a realistic distribution from excellent credit to default
    profile = random.choices([
        'excelente',      # A1 - 0.5-2%
        'muito_bom',      # A2 - 2-5%  
        'bom',            # A3 - 5-10%
        'moderado',       # B1 - 10-20%
        'atencao',        # B2 - 20-35%
        'risco',          # B3/C1 - 35-70%
        'alto_risco'      # C2/D - 70-100%
    ], weights=[0.25, 0.20, 0.20, 0.15, 0.10, 0.07, 0.03])[0]
    
    # Generate behavioral data based on profile with gradual escalation
    v_data = {'v205': 0, 'v210': 0, 'v220': 0, 'v230': 0, 'v240': 0, 'v245': 0, 
              'v250': 0, 'v255': 0, 'v260': 0, 'v270': 0, 'v280': 0, 'v290': 0}
    
    # Profile configurations: (v205, v210, v220+, scr_rating, scr_days, scr_score, scr_util)
    profile_configs = {
        'excelente':  {'v205': 0, 'v210': 0, 'scr_rating': 'AA', 'scr_days': 0, 'scr_score': 0, 'scr_util': (0.05, 0.2)},
        'muito_bom':  {'v205': (0, 200), 'v210': 0, 'scr_rating': 'A', 'scr_days': 0, 'scr_score': 1, 'scr_util': (0.1, 0.3)},
        'bom':        {'v205': (100, 500), 'v210': (0, 200), 'scr_rating': 'B', 'scr_days': (0, 15), 'scr_score': 2, 'scr_util': (0.2, 0.4)},
        'moderado':   {'v205': (300, 1000), 'v210': (100, 500), 'scr_rating': 'C', 'scr_days': (15, 30), 'scr_score': 3, 'scr_util': (0.3, 0.5)},
        'atencao':    {'v205': (500, 2000), 'v210': (200, 1000), 'v220': (0, 500), 'scr_rating': 'D', 'scr_days': (30, 60), 'scr_score': 4, 'scr_util': (0.4, 0.6)},
        'risco':      {'v205': (1000, 4000), 'v210': (500, 2000), 'v220': (200, 1000), 'v230': (0, 500), 'scr_rating': 'E', 'scr_days': (60, 120), 'scr_score': 5, 'scr_util': (0.6, 0.85)},
        'alto_risco': {'v205': (3000, 10000), 'v210': (1500, 5000), 'v220': (1000, 4000), 'v230': (500, 2000), 'v240': (0, 1000), 'scr_rating': 'G', 'scr_days': (120, 300), 'scr_score': 7, 'scr_util': (0.85, 0.99)}
    }
    
    cfg = profile_configs[profile]
    
    # Apply v-column values
    for vcol in ['v205', 'v210', 'v220', 'v230', 'v240', 'v245']:
        if vcol in cfg:
            val = cfg[vcol]
            if isinstance(val, tuple):
                v_data[vcol] = random.uniform(val[0], val[1])
            else:
                v_data[vcol] = val
    
    ocupacao = random.choice(ocupacoes)
    escolaridade = random.choice(escolaridades)
    
    base_income = {'FUNDAM': 1500, 'MEDIO': 2500, 'SUPERIOR': 5000, 'POS': 8000}
    renda_bruta = base_income[escolaridade] * random.uniform(0.8, 1.5)
    
    # Generate SCR data based on profile
    scr_util = random.uniform(*cfg['scr_util'])
    scr_days = cfg['scr_days'] if isinstance(cfg['scr_days'], int) else random.randint(*cfg['scr_days'])
    
    payload = {
        'cpf': cpf,
        'dados_cadastrais': {
            'IDADE_CLIENTE': random.randint(22, 70),
            'RENDA_BRUTA': round(renda_bruta, 2),
            'RENDA_LIQUIDA': round(renda_bruta * 0.85, 2),
            'OCUPACAO': ocupacao,
            'ESCOLARIDADE': escolaridade,
            'ESTADO_CIVIL': random.choice(['SOLTEIRO', 'CASADO', 'DIVORCIADO', 'VIUVO']),
            'QT_DEPENDENTES': random.randint(0, 4),
            'TEMPO_RELAC': round(random.uniform(1, 120), 2),
            'TIPO_RESIDENCIA': random.choice(['PROPRIA', 'ALUGADA', 'CEDIDA']),
            'POSSUI_VEICULO': random.choice(['SIM', 'NAO']),
            'PORTABILIDADE': random.choice(['PORTADO', 'NAO PORTADO']),
            'COMP_RENDA': round(random.uniform(0.1, 0.7), 4),
            'QT_PRODUTOS': random.randint(1, 5),
            # SCR Data - gradual variation based on profile
            'scr_classificacao_risco': cfg['scr_rating'],
            'scr_dias_atraso': scr_days,
            'scr_valor_vencido': scr_days * random.uniform(50, 150) if scr_days > 0 else 0,
            'scr_valor_prejuizo': random.uniform(5000, 30000) if profile == 'alto_risco' else 0,
            'scr_tem_prejuizo': 1 if profile == 'alto_risco' else 0,
            'scr_taxa_utilizacao': scr_util,
            'scr_score_risco': cfg['scr_score'],
            'scr_lim_credito': random.uniform(2000, 20000),
            'scr_lim_utilizado': random.uniform(500, 10000),
            'scr_qtd_instituicoes': random.randint(1, 5),
            'scr_qtd_operacoes': random.randint(1, 10)
        },
        'dados_comportamentais': v_data,
        'sistema_origem': random.choice(sistemas),
        'produto_credito': random.choice(produtos),
        'tipo_solicitacao': random.choice(tipos)
    }
    
    try:
        response = requests.post(f"{get_api_url()}/predict", json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# SIDEBAR - Streaming Controls
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    
    # API URL
    api_url = st.text_input("🔗 API URL", value="http://localhost:8000", key="api_url")
    
    # Health status
    health = check_api_health()
    if health.get('status') == 'healthy':
        st.success(f"✅ API Online | Modelo: {'Carregado' if health.get('model_loaded') else 'Não carregado'}")
    else:
        st.error("❌ API Offline")
    
    st.divider()
    
    # Streaming Controls
    st.markdown("## 🎮 Controle do Streaming")
    
    # Interval selector
    interval = st.slider("⏱️ Intervalo (segundos)", min_value=1, max_value=10, value=2, key="interval")
    
    # Toggle streaming
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Iniciar", type="primary", use_container_width=True, 
                     disabled=st.session_state.streaming_active):
            st.session_state.streaming_active = True
            st.session_state.stream_start_time = datetime.now()
            st.rerun()
    
    with col2:
        if st.button("⏹️ Parar", type="secondary", use_container_width=True,
                     disabled=not st.session_state.streaming_active):
            st.session_state.streaming_active = False
            st.session_state.stream_start_time = None
            st.rerun()
    
    # Streaming status
    if st.session_state.streaming_active:
        elapsed = ""
        if st.session_state.stream_start_time:
            delta = datetime.now() - st.session_state.stream_start_time
            elapsed = f" | {int(delta.total_seconds())}s"
        st.markdown(f'<div class="streaming-on">🔴 STREAMING ATIVO{elapsed}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="streaming-off">⚫ Streaming Inativo</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Actions
    st.markdown("## 🛠️ Ações")
    
    if st.button("🗑️ Limpar Dados", use_container_width=True):
        if clear_avaliacoes():
            st.success("Dados limpos!")
            st.rerun()
        else:
            st.error("Erro ao limpar dados")
    
    if st.button("🔄 Atualizar Agora", use_container_width=True):
        st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header
st.markdown('<h1 class="main-header">📊 PRINAD Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Monitoramento em Tempo Real de Classificação de Risco de Crédito</p>', unsafe_allow_html=True)

# Fetch data
stats = get_stats()
avaliacoes = get_avaliacoes(100)
metrics = get_metrics()

# ============================================================================
# TIMELINE CHART (TOP)
# ============================================================================

st.markdown("### 📈 Timeline de Avaliações")

if avaliacoes:
    df = pd.DataFrame(avaliacoes)
    
    if 'timestamp' in df.columns and len(df) > 0:
        df['time'] = pd.to_datetime(df['timestamp'])
        df['prinad'] = pd.to_numeric(df['prinad'], errors='coerce')
        
        # Create timeline chart
        fig = go.Figure()
        
        # Add scatter plot for each rating
        for rating in RATING_COLORS.keys():
            mask = df['rating'] == rating
            if mask.any():
                fig.add_trace(go.Scatter(
                    x=df.loc[mask, 'time'],
                    y=df.loc[mask, 'prinad'],
                    mode='markers+lines',
                    name=rating,
                    marker=dict(color=RATING_COLORS.get(rating, '#888'), size=10),
                    line=dict(color=RATING_COLORS.get(rating, '#888'), width=1, dash='dot'),
                    hovertemplate=f"<b>{rating}</b><br>PRINAD: %{{y:.1f}}%<br>Hora: %{{x}}<extra></extra>"
                ))
        
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                title="Tempo",
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            ),
            yaxis=dict(
                title="PRINAD (%)",
                range=[0, 105],
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⏳ Aguardando avaliações para exibir timeline...")
else:
    st.info("⏳ Inicie o streaming para ver as avaliações em tempo real")

st.divider()

# ============================================================================
# KPIs ROW
# ============================================================================

col1, col2, col3, col4, col5 = st.columns(5)

total = stats.get('total_avaliacoes', 0)
prinad_medio = stats.get('prinad_medio', 0)
por_rating = stats.get('por_rating', {})
high_risk = sum(por_rating.get(r, 0) for r in ['C1', 'C2', 'D'])
low_risk = sum(por_rating.get(r, 0) for r in ['A1', 'A2', 'A3'])
latency = metrics.get('latencia_media_ms', 0)

with col1:
    st.metric("📊 Total Avaliações", total)
with col2:
    st.metric("📈 PRINAD Médio", f"{prinad_medio:.1f}%")
with col3:
    st.metric("🔴 Alto Risco (C/D)", high_risk)
with col4:
    st.metric("🟢 Baixo Risco (A)", low_risk)
with col5:
    st.metric("⚡ Latência", f"{latency:.0f}ms")

st.divider()

# ============================================================================
# CHARTS ROW
# ============================================================================

col1, col2, col3 = st.columns([2, 1, 1])

# Rating Distribution
with col1:
    st.markdown("### 📊 Distribuição de Ratings")
    if por_rating:
        all_ratings = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'D']
        values = [por_rating.get(r, 0) for r in all_ratings]
        colors = [RATING_COLORS[r] for r in all_ratings]
        
        fig = go.Figure(data=[
            go.Bar(x=all_ratings, y=values, marker_color=colors, text=values, textposition='auto')
        ])
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="Rating"),
            yaxis=dict(title="Quantidade")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando dados...")

# Systems Distribution
with col2:
    st.markdown("### 🏦 Sistemas")
    por_sistema = stats.get('por_sistema', {})
    if por_sistema:
        fig = go.Figure(data=[go.Pie(
            labels=list(por_sistema.keys()),
            values=list(por_sistema.values()),
            hole=0.4,
            marker_colors=['#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b']
        )])
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(orientation="h", y=-0.1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando dados...")

# Request Types
with col3:
    st.markdown("### 📝 Tipos")
    por_tipo = stats.get('por_tipo', {})
    if por_tipo:
        proposta = por_tipo.get('Proposta', 0)
        contratacao = por_tipo.get('Contratacao', 0)
        total_tipo = proposta + contratacao
        
        if total_tipo > 0:
            st.metric("📋 Propostas", f"{proposta}", f"{proposta/total_tipo*100:.0f}%")
            st.metric("✅ Contratações", f"{contratacao}", f"{contratacao/total_tipo*100:.0f}%")
        else:
            st.info("Aguardando dados...")
    else:
        st.info("Aguardando dados...")

st.divider()

# ============================================================================
# PRODUCTS AND TABLE
# ============================================================================

col1, col2 = st.columns([1, 2])

# Products Distribution
with col1:
    st.markdown("### 💳 Produtos de Crédito")
    por_produto = stats.get('por_produto', {})
    if por_produto:
        sorted_products = sorted(por_produto.items(), key=lambda x: -x[1])
        labels = [p[0] for p in sorted_products]
        values = [p[1] for p in sorted_products]
        
        fig = go.Figure(data=[
            go.Bar(x=values, y=labels, orientation='h', 
                   marker_color=['#22c55e', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16'][:len(labels)],
                   text=values, textposition='auto')
        ])
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando dados...")

# Recent Evaluations Table
with col2:
    st.markdown("### 📋 Avaliações Recentes")
    if avaliacoes:
        df_table = pd.DataFrame(avaliacoes[:20])  # Last 20
        
        display_cols = ['timestamp', 'cpf', 'prinad', 'rating', 'sistema_origem', 'produto_credito', 'tipo_solicitacao']
        available = [c for c in display_cols if c in df_table.columns]
        
        if available:
            df_display = df_table[available].copy()
            
            # Format timestamp
            if 'timestamp' in df_display.columns:
                df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%H:%M:%S')
            
            # Rename columns
            col_rename = {
                'timestamp': 'Hora', 'cpf': 'CPF', 'prinad': 'PRINAD%',
                'rating': 'Rating', 'sistema_origem': 'Sistema',
                'produto_credito': 'Produto', 'tipo_solicitacao': 'Tipo'
            }
            df_display.rename(columns=col_rename, inplace=True)
            
            st.dataframe(df_display, use_container_width=True, hide_index=True, height=300)
    else:
        st.info("Aguardando avaliações...")

# ============================================================================
# STREAMING LOGIC - Send request if streaming is active
# ============================================================================

if st.session_state.streaming_active:
    # Send a new request
    result = send_streaming_request()
    
    if 'error' not in result:
        # Show last transaction info in expander
        with st.expander("📤 Última transação enviada", expanded=False):
            st.json({
                "cpf": f"***{result.get('cpf', '')[-4:]}",
                "prinad": result.get('prinad'),
                "rating": result.get('rating'),
                "sistema": result.get('sistema_origem'),
                "produto": result.get('produto_credito'),
                "tipo": result.get('tipo_solicitacao')
            })
    
    # Auto-refresh with the selected interval
    time.sleep(st.session_state.get('interval', 2))
    st.rerun()
else:
    # Just show footer when not streaming
    st.markdown("---")
    st.markdown("*💡 Clique em **▶️ Iniciar** na sidebar para começar o streaming de avaliações*")
