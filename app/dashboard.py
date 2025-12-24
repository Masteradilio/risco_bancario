"""
PRINAD - Streamlit Dashboard
Real-time dashboard for monitoring credit risk classifications.
Includes bank system simulation metrics and streaming control.
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
from collections import deque
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Page config
st.set_page_config(
    page_title="PRINAD Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .rating-A1, .rating-A2, .rating-A3 { color: #22c55e; }
    .rating-B1, .rating-B2 { color: #eab308; }
    .rating-B3 { color: #f97316; }
    .rating-C1, .rating-C2 { color: #ef4444; }
    .rating-D { color: #1f2937; }
    .stMetric { background-color: rgba(28, 131, 225, 0.1); border-radius: 10px; padding: 10px; }
    .big-button {
        font-size: 20px !important;
        padding: 15px 30px !important;
    }
    .streaming-active {
        background-color: #22c55e;
        padding: 10px;
        border-radius: 5px;
        color: white;
        text-align: center;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_URL = st.sidebar.text_input("API URL", "http://localhost:8000")
REFRESH_INTERVAL = 5  # Fixed 5 seconds as requested

# Rating colors
RATING_COLORS = {
    'A1': '#22c55e', 'A2': '#22c55e', 'A3': '#22c55e',
    'B1': '#eab308', 'B2': '#eab308',
    'B3': '#f97316',
    'C1': '#ef4444', 'C2': '#ef4444',
    'D': '#1f2937'
}

# Sistema colors
SISTEMA_COLORS = {
    'app_mobile': '#3b82f6',
    'sis_agencia': '#8b5cf6',
    'terminal_eletronico': '#06b6d4',
    'central_cliente': '#f59e0b'
}

# Produto colors
PRODUTO_COLORS = {
    'consignado': '#22c55e',
    'banparacard': '#3b82f6',
    'cartao_credito': '#8b5cf6',
    'imobiliario': '#f59e0b',
    'antecipacao_13_sal': '#ef4444',
    'cred_veiculo': '#06b6d4',
    'energia_solar': '#84cc16'
}

# Initialize session state
if 'streaming_process' not in st.session_state:
    st.session_state.streaming_process = None
if 'streaming_active' not in st.session_state:
    st.session_state.streaming_active = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()


def check_api_health() -> Dict[str, Any]:
    """Check API health status."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.json()
    except:
        return {"status": "offline", "model_loaded": False}


def get_metrics() -> Dict[str, Any]:
    """Get API metrics."""
    try:
        response = requests.get(f"{API_URL}/metrics", timeout=5)
        return response.json()
    except:
        return {}


def get_avaliacoes(limit: int = 50) -> List[Dict[str, Any]]:
    """Get evaluations from API."""
    try:
        response = requests.get(f"{API_URL}/avaliacoes?limit={limit}", timeout=5)
        data = response.json()
        return data.get('avaliacoes', [])
    except:
        return []


def get_stats() -> Dict[str, Any]:
    """Get aggregated stats from API."""
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        return response.json()
    except:
        return {}


def clear_avaliacoes():
    """Clear all evaluations."""
    try:
        response = requests.delete(f"{API_URL}/avaliacoes", timeout=5)
        return response.json()
    except:
        return {"error": "Failed to clear"}


def start_streaming():
    """Start the streaming sender process."""
    if st.session_state.streaming_process is None or st.session_state.streaming_process.poll() is not None:
        # Get path to streaming_sender.py
        app_dir = Path(__file__).parent
        sender_path = app_dir / "streaming_sender.py"
        
        # Start process
        st.session_state.streaming_process = subprocess.Popen(
            [sys.executable, str(sender_path), "-i", "5", "-u", API_URL],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        st.session_state.streaming_active = True
        st.session_state.start_time = datetime.now()


def stop_streaming():
    """Stop the streaming sender process."""
    if st.session_state.streaming_process is not None:
        st.session_state.streaming_process.terminate()
        st.session_state.streaming_process = None
        st.session_state.streaming_active = False


def render_header():
    """Render dashboard header."""
    st.title("📊 PRINAD Dashboard")
    st.markdown("**Monitoramento em Tempo Real de Classificação de Risco de Crédito**")
    
    # Health status
    health = check_api_health()
    status_color = "🟢" if health.get('status') == 'healthy' else "🔴"
    st.markdown(f"{status_color} API Status: **{health.get('status', 'unknown')}** | "
                f"Model: **{'Loaded' if health.get('model_loaded') else 'Not Loaded'}** | "
                f"Atualização: **{REFRESH_INTERVAL}s**")


def render_streaming_control():
    """Render streaming control buttons."""
    st.subheader("🎮 Controle do Streaming")
    
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        if st.button("▶️ Iniciar Streaming", type="primary", use_container_width=True,
                     disabled=st.session_state.streaming_active):
            start_streaming()
            st.rerun()
    
    with col2:
        if st.button("⏹️ Parar Streaming", type="secondary", use_container_width=True,
                     disabled=not st.session_state.streaming_active):
            stop_streaming()
            st.rerun()
    
    with col3:
        if st.session_state.streaming_active:
            # Check if process is still running
            if st.session_state.streaming_process and st.session_state.streaming_process.poll() is None:
                elapsed = datetime.now() - st.session_state.start_time
                st.markdown(f"""
                <div class="streaming-active">
                    🔴 STREAMING ATIVO | Tempo: {int(elapsed.total_seconds())}s | Intervalo: 5s
                </div>
                """, unsafe_allow_html=True)
            else:
                st.session_state.streaming_active = False
                st.info("Streaming parou")
        else:
            st.info("Streaming inativo. Clique em 'Iniciar Streaming' para começar.")


def render_kpis():
    """Render KPI metrics."""
    stats = get_stats()
    metrics = get_metrics()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total = stats.get('total_avaliacoes', 0)
        st.metric("Total Classificações", total)
    
    with col2:
        prinad_medio = stats.get('prinad_medio', 0)
        st.metric("PRINAD Médio", f"{prinad_medio:.1f}%")
    
    with col3:
        # Count high risk
        por_rating = stats.get('por_rating', {})
        high_risk = sum(por_rating.get(r, 0) for r in ['C1', 'C2', 'D'])
        st.metric("Alto Risco (C1+)", high_risk)
    
    with col4:
        low_risk = sum(por_rating.get(r, 0) for r in ['A1', 'A2', 'A3'])
        st.metric("Baixo Risco (A)", low_risk)
    
    with col5:
        latency = metrics.get('latencia_media_ms', 0)
        st.metric("Latência Média", f"{latency:.0f}ms")


def render_rating_distribution():
    """Render rating distribution chart."""
    st.subheader("📊 Distribuição de Ratings")
    
    stats = get_stats()
    ratings = stats.get('por_rating', {})
    
    if ratings:
        # Ensure all ratings are present
        all_ratings = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'D']
        data = [ratings.get(r, 0) for r in all_ratings]
        colors = [RATING_COLORS[r] for r in all_ratings]
        
        fig = go.Figure(data=[
            go.Bar(
                x=all_ratings,
                y=data,
                marker_color=colors,
                text=data,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Rating",
            yaxis_title="Quantidade"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando classificações...")


def render_sistema_distribution():
    """Render system origin distribution chart."""
    st.subheader("🏦 Sistemas de Origem")
    
    stats = get_stats()
    sistemas = stats.get('por_sistema', {})
    
    if sistemas and any(v > 0 for v in sistemas.values()):
        labels = list(sistemas.keys())
        values = list(sistemas.values())
        colors = [SISTEMA_COLORS.get(s, '#888888') for s in labels]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=0.4,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando dados de sistemas...")


def render_produto_distribution():
    """Render credit product distribution chart."""
    st.subheader("💳 Produtos de Crédito")
    
    stats = get_stats()
    produtos = stats.get('por_produto', {})
    
    if produtos and any(v > 0 for v in produtos.values()):
        # Sort by value descending
        sorted_items = sorted(produtos.items(), key=lambda x: -x[1])
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        colors = [PRODUTO_COLORS.get(p, '#888888') for p in labels]
        
        fig = go.Figure(data=[
            go.Bar(
                x=values,
                y=labels,
                orientation='h',
                marker_color=colors,
                text=values,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Quantidade",
            yaxis_title=""
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando dados de produtos...")


def render_tipo_distribution():
    """Render request type distribution."""
    st.subheader("📝 Tipo de Solicitação")
    
    stats = get_stats()
    tipos = stats.get('por_tipo', {})
    
    if tipos and any(v > 0 for v in tipos.values()):
        col1, col2 = st.columns(2)
        
        proposta = tipos.get('Proposta', 0)
        contratacao = tipos.get('Contratacao', 0)
        total = proposta + contratacao
        
        with col1:
            pct = (proposta / total * 100) if total > 0 else 0
            st.metric("📋 Propostas", f"{proposta}", f"{pct:.1f}%")
        
        with col2:
            pct = (contratacao / total * 100) if total > 0 else 0
            st.metric("✅ Contratações", f"{contratacao}", f"{pct:.1f}%")
    else:
        st.info("Aguardando dados...")


def render_prinad_gauge():
    """Render PRINAD average gauge."""
    st.subheader("🎯 PRINAD Médio")
    
    stats = get_stats()
    avg_prinad = stats.get('prinad_medio', 0)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_prinad,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 20], 'color': "#22c55e"},
                {'range': [20, 50], 'color': "#eab308"},
                {'range': [50, 70], 'color': "#f97316"},
                {'range': [70, 100], 'color': "#ef4444"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': avg_prinad
            }
        },
        number={'suffix': '%'}
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_timeseries():
    """Render classification timeseries."""
    st.subheader("📈 Classificações ao Longo do Tempo")
    
    avaliacoes = get_avaliacoes(100)
    
    if avaliacoes:
        df = pd.DataFrame(avaliacoes)
        
        if 'timestamp' in df.columns:
            df['time'] = pd.to_datetime(df['timestamp'])
            df['prinad'] = pd.to_numeric(df['prinad'], errors='coerce')
            
            # PRINAD over time
            fig = make_subplots(rows=2, cols=1, 
                               subplot_titles=('PRINAD por Classificação', 'Contagem por Minuto'),
                               vertical_spacing=0.15)
            
            # PRINAD scatter with color
            for rating in df['rating'].unique():
                mask = df['rating'] == rating
                fig.add_trace(
                    go.Scatter(
                        x=df.loc[mask, 'time'],
                        y=df.loc[mask, 'prinad'],
                        mode='markers',
                        name=rating,
                        marker=dict(
                            color=RATING_COLORS.get(rating, '#888888'),
                            size=8
                        )
                    ),
                    row=1, col=1
                )
            
            # Count per minute
            df['minute'] = df['time'].dt.floor('min')
            counts = df.groupby('minute').size().reset_index(name='count')
            
            fig.add_trace(
                go.Bar(
                    x=counts['minute'],
                    y=counts['count'],
                    marker_color='#3b82f6',
                    showlegend=False
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=500,
                showlegend=True,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando classificações...")


def render_avaliacoes_table():
    """Render table of evaluations."""
    st.subheader("📋 Tabela de Avaliações de Risco")
    
    avaliacoes = get_avaliacoes(50)
    
    if avaliacoes:
        df = pd.DataFrame(avaliacoes)
        
        # Select and rename columns for display
        display_cols = ['timestamp', 'cpf', 'pd_base', 'penalidade_historica', 'prinad', 
                        'rating', 'sistema_origem', 'produto_credito', 'tipo_solicitacao']
        available_cols = [c for c in display_cols if c in df.columns]
        
        if available_cols:
            df_display = df[available_cols].copy()
            
            # Format timestamp
            if 'timestamp' in df_display.columns:
                df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%H:%M:%S')
            
            # Rename columns
            col_names = {
                'timestamp': 'Hora',
                'cpf': 'CPF',
                'pd_base': 'PD Base (%)',
                'penalidade_historica': 'Penalidade',
                'prinad': 'PRINAD (%)',
                'rating': 'Rating',
                'sistema_origem': 'Sistema',
                'produto_credito': 'Produto',
                'tipo_solicitacao': 'Tipo'
            }
            df_display = df_display.rename(columns=col_names)
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                height=400
            )
    else:
        st.info("Aguardando avaliações...")


def main():
    """Main dashboard function."""
    
    render_header()
    st.divider()
    
    # Streaming control
    render_streaming_control()
    st.divider()
    
    # KPIs row
    render_kpis()
    st.divider()
    
    # Charts row 1: Ratings and Systems
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_rating_distribution()
    
    with col2:
        render_prinad_gauge()
    
    st.divider()
    
    # Charts row 2: Products and Types
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        render_produto_distribution()
    
    with col2:
        render_sistema_distribution()
    
    with col3:
        render_tipo_distribution()
    
    st.divider()
    
    # Timeseries
    render_timeseries()
    
    st.divider()
    
    # Evaluations table
    render_avaliacoes_table()
    
    # Sidebar controls
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Controles")
    
    if st.sidebar.button("🔄 Atualizar Agora"):
        st.rerun()
    
    if st.sidebar.button("🗑️ Limpar Dados"):
        clear_avaliacoes()
        st.rerun()
    
    # Auto-refresh
    st.sidebar.divider()
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)
    
    if auto_refresh:
        time.sleep(REFRESH_INTERVAL)
        st.rerun()
    
    # Info
    st.sidebar.divider()
    st.sidebar.info(
        "Este dashboard mostra classificações de risco em tempo real. "
        "Clique em 'Iniciar Streaming' para começar a simulação."
    )


if __name__ == "__main__":
    main()
