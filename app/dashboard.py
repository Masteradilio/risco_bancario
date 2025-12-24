"""
PRINAD - Streamlit Dashboard
Real-time dashboard for monitoring credit risk classifications.
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
import threading
import websocket
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
</style>
""", unsafe_allow_html=True)

# Configuration
API_URL = st.sidebar.text_input("API URL", "http://localhost:8000")
REFRESH_INTERVAL = st.sidebar.slider("Intervalo de atualização (s)", 1, 10, 2)

# Rating colors
RATING_COLORS = {
    'A1': '#22c55e', 'A2': '#22c55e', 'A3': '#22c55e',
    'B1': '#eab308', 'B2': '#eab308',
    'B3': '#f97316',
    'C1': '#ef4444', 'C2': '#ef4444',
    'D': '#1f2937'
}

# Initialize session state
if 'classifications' not in st.session_state:
    st.session_state.classifications = deque(maxlen=1000)
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total': 0,
        'por_rating': {},
        'por_minuto': deque(maxlen=60),
        'prinad_medio': 0,
        'start_time': datetime.now()
    }
if 'running' not in st.session_state:
    st.session_state.running = False


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


def add_classification(result: Dict[str, Any]):
    """Add a classification result to session state."""
    st.session_state.classifications.append({
        **result,
        'received_at': datetime.now().isoformat()
    })
    
    # Update stats
    st.session_state.stats['total'] += 1
    rating = result.get('rating', 'Unknown')
    st.session_state.stats['por_rating'][rating] = \
        st.session_state.stats['por_rating'].get(rating, 0) + 1
    
    # Update average PRINAD
    prinad = result.get('prinad', 0)
    current_avg = st.session_state.stats['prinad_medio']
    total = st.session_state.stats['total']
    st.session_state.stats['prinad_medio'] = \
        (current_avg * (total - 1) + prinad) / total


def render_header():
    """Render dashboard header."""
    st.title("📊 PRINAD Dashboard")
    st.markdown("**Monitoramento em Tempo Real de Classificação de Risco de Crédito**")
    
    # Health status
    health = check_api_health()
    status_color = "🟢" if health.get('status') == 'healthy' else "🔴"
    st.markdown(f"{status_color} API Status: **{health.get('status', 'unknown')}** | "
                f"Model: **{'Loaded' if health.get('model_loaded') else 'Not Loaded'}**")


def render_kpis():
    """Render KPI metrics."""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Classificações",
            st.session_state.stats['total'],
            delta=None
        )
    
    with col2:
        st.metric(
            "PRINAD Médio",
            f"{st.session_state.stats['prinad_medio']:.1f}%",
            delta=None
        )
    
    with col3:
        # Count by risk level
        high_risk = sum(
            st.session_state.stats['por_rating'].get(r, 0) 
            for r in ['C1', 'C2', 'D']
        )
        st.metric(
            "Alto Risco (C1+)",
            high_risk,
            delta=None
        )
    
    with col4:
        low_risk = sum(
            st.session_state.stats['por_rating'].get(r, 0) 
            for r in ['A1', 'A2', 'A3']
        )
        st.metric(
            "Baixo Risco (A)",
            low_risk,
            delta=None
        )
    
    with col5:
        uptime = datetime.now() - st.session_state.stats['start_time']
        hours = uptime.total_seconds() / 3600
        st.metric(
            "Uptime",
            f"{hours:.1f}h",
            delta=None
        )


def render_rating_distribution():
    """Render rating distribution chart."""
    st.subheader("📊 Distribuição de Ratings")
    
    ratings = st.session_state.stats['por_rating']
    
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


def render_prinad_gauge():
    """Render PRINAD average gauge."""
    st.subheader("🎯 PRINAD Médio")
    
    avg_prinad = st.session_state.stats['prinad_medio']
    
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
    
    if st.session_state.classifications:
        df = pd.DataFrame(list(st.session_state.classifications))
        
        if 'timestamp' in df.columns:
            df['time'] = pd.to_datetime(df['timestamp'])
            
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
            df['minute'] = df['time'].dt.floor('T')
            counts = df.groupby('minute').size().reset_index(name='count')
            
            fig.add_trace(
                go.Bar(
                    x=counts['minute'],
                    y=counts['count'],
                    marker_color='#3b82f6'
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


def render_recent_classifications():
    """Render table of recent classifications."""
    st.subheader("📋 Classificações Recentes")
    
    if st.session_state.classifications:
        df = pd.DataFrame(list(st.session_state.classifications)[-20:])
        
        # Select and rename columns for display
        display_cols = ['cpf', 'prinad', 'rating', 'rating_descricao', 'cor', 'pd_base', 
                        'penalidade_historica', 'acao_sugerida', 'timestamp']
        available_cols = [c for c in display_cols if c in df.columns]
        
        if available_cols:
            df_display = df[available_cols].copy()
            
            # Format CPF (mask for privacy)
            if 'cpf' in df_display.columns:
                df_display['cpf'] = df_display['cpf'].apply(
                    lambda x: f"***{str(x)[-4:]}" if pd.notna(x) else "N/A"
                )
            
            # Format timestamp
            if 'timestamp' in df_display.columns:
                df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%H:%M:%S')
            
            # Rename columns
            col_names = {
                'cpf': 'CPF',
                'prinad': 'PRINAD (%)',
                'rating': 'Rating',
                'rating_descricao': 'Descrição',
                'cor': 'Cor',
                'pd_base': 'PD Base (%)',
                'penalidade_historica': 'Penalidade',
                'acao_sugerida': 'Ação',
                'timestamp': 'Hora'
            }
            df_display = df_display.rename(columns=col_names)
            
            st.dataframe(
                df_display.iloc[::-1],  # Most recent first
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("Aguardando classificações...")


def render_risk_breakdown():
    """Render risk breakdown pie chart."""
    st.subheader("🥧 Breakdown de Risco")
    
    ratings = st.session_state.stats['por_rating']
    
    if ratings:
        # Group by risk level
        risk_levels = {
            'Baixo (A)': sum(ratings.get(r, 0) for r in ['A1', 'A2', 'A3']),
            'Moderado (B1-B2)': sum(ratings.get(r, 0) for r in ['B1', 'B2']),
            'Elevado (B3)': ratings.get('B3', 0),
            'Alto (C)': sum(ratings.get(r, 0) for r in ['C1', 'C2']),
            'Default (D)': ratings.get('D', 0)
        }
        
        colors = ['#22c55e', '#eab308', '#f97316', '#ef4444', '#1f2937']
        
        fig = go.Figure(data=[go.Pie(
            labels=list(risk_levels.keys()),
            values=list(risk_levels.values()),
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
        st.info("Aguardando classificações...")


def main():
    """Main dashboard function."""
    
    render_header()
    st.divider()
    
    # KPIs row
    render_kpis()
    st.divider()
    
    # Charts row 1
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_rating_distribution()
    
    with col2:
        render_prinad_gauge()
    
    st.divider()
    
    # Charts row 2
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_timeseries()
    
    with col2:
        render_risk_breakdown()
    
    st.divider()
    
    # Recent classifications table
    render_recent_classifications()
    
    # Auto-refresh
    if st.sidebar.checkbox("Auto-refresh", value=True):
        time.sleep(REFRESH_INTERVAL)
        st.rerun()
    
    # Manual controls
    st.sidebar.divider()
    st.sidebar.subheader("Controles")
    
    if st.sidebar.button("🔄 Atualizar Agora"):
        st.rerun()
    
    if st.sidebar.button("🗑️ Limpar Dados"):
        st.session_state.classifications = deque(maxlen=1000)
        st.session_state.stats = {
            'total': 0,
            'por_rating': {},
            'por_minuto': deque(maxlen=60),
            'prinad_medio': 0,
            'start_time': datetime.now()
        }
        st.rerun()
    
    # Info
    st.sidebar.divider()
    st.sidebar.info(
        "Este dashboard mostra classificações de risco em tempo real. "
        "Execute o `streaming_sender.py` para simular dados."
    )


if __name__ == "__main__":
    main()
