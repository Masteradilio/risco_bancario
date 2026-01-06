"""
PRINAD - Streamlit Dashboard v2.0 (BACEN 4966)
Real-time dashboard for monitoring credit risk classifications.
Features:
- Timeline chart with PD 12m visualization
- Stage distribution (IFRS 9)
- Streaming from database CPFs
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
from pathlib import Path

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="PRINAD Dashboard - BACEN 4966",
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
    .stage-1 { color: #22c55e; }
    .stage-2 { color: #f59e0b; }
    .stage-3 { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# Rating colors
RATING_COLORS = {
    'A1': '#22c55e', 'A2': '#4ade80', 'A3': '#86efac',
    'B1': '#eab308', 'B2': '#facc15',
    'B3': '#f97316',
    'C1': '#ef4444', 'C2': '#f87171', 'C3': '#fca5a5',
    'D': '#1f2937',
    'DEFAULT': '#111827'
}

# Stage colors
STAGE_COLORS = {1: '#22c55e', 2: '#f59e0b', 3: '#ef4444'}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'streaming_active' not in st.session_state:
    st.session_state.streaming_active = False
if 'stream_start_time' not in st.session_state:
    st.session_state.stream_start_time = None
if 'available_cpfs' not in st.session_state:
    st.session_state.available_cpfs = []
if 'classifications' not in st.session_state:
    st.session_state.classifications = []
if 'errors_count' not in st.session_state:
    st.session_state.errors_count = 0

# ============================================================================
# API FUNCTIONS
# ============================================================================

def get_api_url():
    """Get API URL from session state or default."""
    url = st.session_state.get('api_url', 'http://localhost:8000')
    return url.rstrip('/')

def check_api_health() -> Dict[str, Any]:
    """Check API health status."""
    try:
        response = requests.get(f"{get_api_url()}/health", timeout=3)
        return response.json()
    except Exception as e:
        return {"status": "offline", "error": str(e), "model_loaded": False, "database_loaded": False, "total_clientes": 0}

def load_available_cpfs(limit: int = 1000) -> List[str]:
    """Load available CPFs from API."""
    url = f"{get_api_url()}/clientes?limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            st.error(f"Erro API ({response.status_code}): {response.text}")
            return []
            
        data = response.json()
        cpfs = data.get('cpfs', [])
        
        if not cpfs:
            st.warning(f"API retornou 0 CPFs. JSON: {data}")
        
        return cpfs
    except Exception as e:
        st.error(f"Erro de conexão com {url}: {e}")
        return []

def classify_cpf(cpf: str, explained: bool = False) -> Dict[str, Any]:
    """Classify a single CPF."""
    endpoint = "explained_classify" if explained else "simple_classify"
    try:
        response = requests.post(
            f"{get_api_url()}/{endpoint}",
            json={"cpf": cpf},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text, "cpf": cpf}
    except Exception as e:
        return {"error": str(e), "cpf": cpf}

def classify_batch(cpfs: List[str]) -> Dict[str, Any]:
    """Classify multiple CPFs."""
    try:
        response = requests.post(
            f"{get_api_url()}/multiple_classify",
            json={"cpfs": cpfs, "output_format": "json"},
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# SIDEBAR - Streaming Controls
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    
    # API URL
    # API URL
    api_url = st.text_input("🔗 API URL", value="http://127.0.0.1:8000", key="api_url")
    
    # Health status
    health = check_api_health()
    if health.get('status') == 'healthy':
        st.success(f"✅ API Online")
        st.info(f"📊 Clientes na base: {health.get('total_clientes', 0):,}")
    elif health.get('status') == 'degraded':
        st.warning("⚠️ API em modo degradado (usando fallback)")
    else:
        st.error(f"❌ API Offline: {health.get('error', '')}")
    
    # API Docs button (opens in new tab)
    docs_url = f"{api_url}/docs#/"
    st.link_button("📖 Documentação da API", docs_url, use_container_width=True)
    
    st.divider()
    
    # ========================================================================
    # MODE SELECTION
    # ========================================================================
    st.markdown("## 🎛️ Modos de Operação")
    
    # Initialize mode if not set
    if 'classification_mode' not in st.session_state:
        st.session_state.classification_mode = 'explained' # Default requested by user
    
    mode = st.session_state.classification_mode
    
    # Mode Buttons (Exclusive)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚡ Simples", type="primary" if mode == 'simple' else "secondary", use_container_width=True):
            st.session_state.classification_mode = 'simple'
            st.rerun()
        if st.button("📦 Lote Simples", type="primary" if mode == 'batch' else "secondary", use_container_width=True):
            st.session_state.classification_mode = 'batch'
            st.session_state.streaming_active = False # Batch stops streaming
            st.rerun()
            
    with c2:
        if st.button("🧠 Explicado", type="primary" if mode == 'explained' else "secondary", use_container_width=True):
            st.session_state.classification_mode = 'explained'
            st.rerun()
        if st.button("📦 Lote Explicado", type="primary" if mode == 'batch_explained' else "secondary", use_container_width=True):
            st.session_state.classification_mode = 'batch_explained'
            st.session_state.streaming_active = False # Batch stops streaming
            st.rerun()
            
    st.caption(f"Endpoint Ativo: `/{mode}_classify`")
    
    st.divider()
    
    # ========================================================================
    # CONTROLS (Dynamic based on mode)
    # ========================================================================
    
    if 'batch' in mode:
        st.markdown("## 📂 Processamento em Lote")
        uploaded_file = st.file_uploader("Carregar arquivo CSV (coluna 'CPF')", type=['csv'])
        
        if uploaded_file and st.button("🚀 Processar Arquivo", type="primary", use_container_width=True):
            try:
                # Try different encodings
                try:
                    df_upload = pd.read_csv(uploaded_file, sep=',', encoding='utf-8')
                except:
                    uploaded_file.seek(0)
                    df_upload = pd.read_csv(uploaded_file, sep=';', encoding='latin-1')
                    
                # Find CPF column
                cpf_col = next((c for c in df_upload.columns if 'cpf' in c.lower()), None)
                
                if cpf_col:
                    cpfs = df_upload[cpf_col].astype(str).str.zfill(11).tolist()
                    total_cpfs = len(cpfs)
                    
                    is_explained = (mode == 'batch_explained')
                    
                    # Estimate time: ~0.5s per CPF for simple, ~1.5s for explained
                    time_per_cpf = 1.5 if is_explained else 0.5
                    estimated_seconds = int(total_cpfs * time_per_cpf)
                    estimated_min = estimated_seconds // 60
                    estimated_sec = estimated_seconds % 60
                    
                    st.info(f"⏱️ Tempo estimado: **{estimated_min}m {estimated_sec}s** para {total_cpfs} CPFs")
                    
                    # Progress bar
                    progress_bar = st.progress(0, text="Iniciando processamento...")
                    status_text = st.empty()
                    
                    # Process in chunks for progress tracking
                    import time
                    chunk_size = 20  # Process 20 at a time
                    all_results = []
                    all_errors = []
                    
                    endpoint = "multiple_explained_classify" if is_explained else "multiple_classify"
                    start_time = time.time()
                    
                    for i in range(0, total_cpfs, chunk_size):
                        chunk = cpfs[i:i+chunk_size]
                        chunk_num = i // chunk_size + 1
                        total_chunks = (total_cpfs + chunk_size - 1) // chunk_size
                        
                        # Update progress
                        progress = min((i + len(chunk)) / total_cpfs, 1.0)
                        elapsed = time.time() - start_time
                        if progress > 0:
                            remaining = (elapsed / progress) * (1 - progress)
                            rem_min = int(remaining) // 60
                            rem_sec = int(remaining) % 60
                            progress_bar.progress(progress, text=f"Processando... {int(progress*100)}%")
                            status_text.caption(f"Chunk {chunk_num}/{total_chunks} | ⏱️ Restam: {rem_min}m {rem_sec}s")
                        
                        try:
                            resp = requests.post(
                                f"{get_api_url()}/{endpoint}",
                                json={"cpfs": chunk, "output_format": "json"},
                                timeout=120
                            )
                            
                            if resp.status_code == 200:
                                data = resp.json()
                                chunk_results = data.get('resultados', [])
                                chunk_errors = data.get('erros', [])
                                
                                # FORCE CPF from input (fix 'unknown' issue)
                                for idx, r in enumerate(chunk_results):
                                    original_cpf = chunk[idx] if idx < len(chunk) else r.get('cpf', '')
                                    if r.get('cpf', '').lower() == 'unknown' or not r.get('cpf'):
                                        r['cpf'] = original_cpf
                                
                                all_results.extend(chunk_results)
                                all_errors.extend(chunk_errors)
                        except Exception as chunk_e:
                            all_errors.append({'chunk': i, 'erro': str(chunk_e)})
                    
                    # Complete progress
                    progress_bar.progress(1.0, text="✅ Concluído!")
                    status_text.empty()
                    
                    # Build output DataFrame
                    output_rows = []
                    for r in all_results:
                        row = {
                            'CPF': r.get('cpf', ''),
                            'PRINAD': round(r.get('prinad', 0), 2),
                            'PD_12m': round(r.get('pd_12m', 0) * 100, 4),
                            'PD_Lifetime': round(r.get('pd_lifetime', 0) * 100, 4),
                            'Rating': r.get('rating', ''),
                            'Estagio_PE': r.get('estagio_pe', 1),
                            'Acao_Sugerida': r.get('acao_sugerida', '')
                        }
                        
                        if is_explained:
                            shap_list = r.get('explicacao_shap', [])
                            for si, s in enumerate(shap_list[:5]):
                                row[f'SHAP_{si+1}_Feature'] = s.get('feature', '')
                                row[f'SHAP_{si+1}_Contrib'] = s.get('contribuicao', 0)
                            
                            exp = r.get('explicacao_completa', {})
                            comp = exp.get('composicao_prinad', {})
                            pen_int = comp.get('penalidade_interna', {})
                            pen_ext = comp.get('penalidade_externa', {})
                            
                            row['Pen_Interna_%'] = pen_int.get('valor', 0)
                            row['Pen_Externa_%'] = pen_ext.get('valor', 0)
                            row['PD_ML'] = comp.get('pd_modelo_ml', {}).get('valor', 0)
                        
                        output_rows.append(row)
                        
                        # Add to dashboard list
                        r['timestamp'] = datetime.now().isoformat()
                        st.session_state.classifications.append(r)
                    
                    # Trim classifications
                    if len(st.session_state.classifications) > 500:
                        st.session_state.classifications = st.session_state.classifications[-500:]
                    
                    # Store batch results for central display
                    df_output = pd.DataFrame(output_rows)
                    st.session_state.batch_results = df_output
                    
                    # Prepare download
                    import os
                    source_name = uploaded_file.name
                    base_name = os.path.splitext(source_name)[0]
                    suffix = "_explicado" if is_explained else "_simples"
                    output_name = f"{base_name}_resultado{suffix}.csv"
                    csv_bytes = df_output.to_csv(index=False).encode('utf-8')
                    
                    st.success(f"✅ Processados: {len(all_results)} | ❌ Erros: {len(all_errors)}")
                    
                    st.download_button(
                        label=f"📥 Baixar CSV ({output_name})",
                        data=csv_bytes,
                        file_name=output_name,
                        mime="text/csv",
                        type="primary"
                    )
                else:
                    st.error("Coluna 'CPF' não encontrada no CSV.")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")
                
    else:
        # STREAMING CONTROLS (Simple/Explained)
        st.markdown("## 🎮 Controle do Streaming")
        
        # Interval selector
        interval = st.slider("⏱️ Intervalo (segundos)", min_value=1, max_value=10, value=3, key="interval")
        
        # Toggle streaming
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Iniciar", type="primary", use_container_width=True, 
                         disabled=st.session_state.streaming_active):
                
                # Auto-load if empty
                if not st.session_state.available_cpfs:
                    cpfs = load_available_cpfs()
                    if cpfs:
                        st.session_state.available_cpfs = cpfs
                        st.success("CPFs carregados.") 
                    else:
                        st.error("Impossível iniciar: Falha ao carregar CPFs.")
                        st.stop()
                
                st.session_state.streaming_active = True
                st.session_state.stream_start_time = datetime.now()
                # Do NOT clear classifications on start, append new ones
                st.session_state.errors_count = 0
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
            if st.session_state.available_cpfs:
                 st.caption(f"Usando {len(st.session_state.available_cpfs)} CPFs da base")
        else:
            st.markdown('<div class="streaming-off">⚫ Streaming Inativo</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Actions
        st.markdown("## 🛠️ Ações")
        
        if st.button("🗑️ Limpar Classificações", use_container_width=True):
            st.session_state.classifications = []
            st.session_state.errors_count = 0
            st.rerun()
    
    if st.button("🔄 Atualizar Agora", use_container_width=True):
        st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Header
st.markdown('<h1 class="main-header">📊 PRINAD Dashboard v2.0</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Classificação de Risco de Crédito - BACEN 4966 / IFRS 9</p>', unsafe_allow_html=True)

# Get classifications from session state
classifications = st.session_state.classifications

# ==========
# TIMELINE CHART (TOP)
# ==========

st.markdown("### 📈 Timeline de Classificações")

if classifications:
    df = pd.DataFrame(classifications)
    df['time'] = pd.to_datetime(df['timestamp'])
    
    # Create timeline chart with dual y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # PRINAD line
    fig.add_trace(
        go.Scatter(
            x=df['time'], y=df['prinad'],
            mode='lines+markers',
            name='PRINAD %',
            line=dict(color='#3b82f6', width=2),
            marker=dict(size=6)
        ),
        secondary_y=False
    )
    
    # PD 12m line
    fig.add_trace(
        go.Scatter(
            x=df['time'], y=df['pd_12m'] * 100,
            mode='lines+markers',
            name='PD 12m %',
            line=dict(color='#ef4444', width=2, dash='dot'),
            marker=dict(size=4)
        ),
        secondary_y=True
    )

    # PD Lifetime (New)
    if 'pd_lifetime' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['time'], y=df['pd_lifetime'] * 100,
                mode='lines',
                name='PD Lifetime %',
                line=dict(color='#10b981', width=2, dash='dash')
            ),
            secondary_y=True
        )
    
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    fig.update_xaxes(title="Tempo", gridcolor='rgba(128,128,128,0.2)', showgrid=True)
    fig.update_yaxes(title="PRINAD %", gridcolor='rgba(128,128,128,0.2)', showgrid=True, secondary_y=False)
    fig.update_yaxes(title="PD 12m %", gridcolor='rgba(128,128,128,0.2)', showgrid=True, secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Inicie o streaming para ver as classificações em tempo real")

st.divider()

# ==========
# KPIs ROW
# ==========

total = len(classifications)
pd_life_medio = 0
rating_counts = {} 
stage_counts = {}

if classifications:
    df_class = pd.DataFrame(classifications)
    prinad_medio = df_class['prinad'].mean()
    pd_12m_medio = df_class['pd_12m'].mean() * 100
    if 'pd_lifetime' in df_class.columns:
        pd_life_medio = df_class['pd_lifetime'].mean() * 100
    
    # Count by stage
    stage_counts = df_class['estagio_pe'].value_counts().to_dict()
    stage_1 = stage_counts.get(1, 0)
    stage_2 = stage_counts.get(2, 0)
    stage_3 = stage_counts.get(3, 0)
    
    # Count by rating (Required for Distribution Chart below)
    if 'rating' in df_class.columns:
        rating_counts = df_class['rating'].value_counts().to_dict()
else:
    prinad_medio = 0
    pd_12m_medio = 0
    stage_1 = 0
    stage_2 = 0
    stage_3 = 0

# 7 Columns Layout
k1, k2, k3, k4, k5, k6, k7 = st.columns(7)

with k1: st.metric("📊 Total", total)
with k2: st.metric("🔵 PRINAD Avg", f"{prinad_medio:.1f}%")
with k3: st.metric("🟠 PD 12m Avg", f"{pd_12m_medio:.2f}%")
with k4: st.metric("🟢 PD Lifetime Avg", f"{pd_life_medio:.2f}%")
with k5: st.metric("Stage 1", stage_1)
with k6: st.metric("Stage 2", stage_2)
with k7: st.metric("Stage 3", stage_3)

st.divider()

# ============================================================================
# CHARTS ROW
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

# Rating Distribution
with col1:
    st.markdown("### 📊 Ratings")
    if rating_counts:
        all_ratings = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D', 'DEFAULT']
        values = [rating_counts.get(r, 0) for r in all_ratings]
        colors = [] # Define colors locally or use global map if available
        # Simplified color logic for stability
        for r in all_ratings:
             if 'A' in r: colors.append('#10b981')
             elif 'B' in r: colors.append('#f59e0b')
             elif 'C' in r: colors.append('#f97316')
             else: colors.append('#ef4444')
        
        fig = go.Figure(data=[
            go.Bar(x=all_ratings, y=values, marker_color=colors, text=values, textposition='auto')
        ])
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="Rating"),
            yaxis=dict(title="Qtd")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("...")

# Stage Distribution (IFRS 9)
with col2:
    st.markdown("### 📈 Stages")
    if stage_counts:
        fig = go.Figure(data=[go.Pie(
            labels=['Stage 1', 'Stage 2', 'Stage 3'],
            values=[stage_counts.get(1, 0), stage_counts.get(2, 0), stage_counts.get(3, 0)],
            hole=0.4,
            marker_colors=['#10b981', '#f59e0b', '#ef4444']
        )])
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("...")

# PD 12m Distribution by Risk Band
with col3:
    st.markdown("### 📉 PD 12m")
    if classifications:
        pd_values = [c.get('pd_12m', 0) * 100 for c in classifications]
        
        # Categorize by risk bands
        bands = {'<1%': 0, '1-5%': 0, '5-15%': 0, '15-30%': 0, '>30%': 0}
        for v in pd_values:
            if v < 1:
                bands['<1%'] += 1
            elif v < 5:
                bands['1-5%'] += 1
            elif v < 15:
                bands['5-15%'] += 1
            elif v < 30:
                bands['15-30%'] += 1
            else:
                bands['>30%'] += 1
        
        colors = ['#10b981', '#22c55e', '#f59e0b', '#f97316', '#ef4444']
        fig = go.Figure(data=[go.Bar(
            x=list(bands.keys()),
            y=list(bands.values()),
            marker_color=colors,
            text=list(bands.values()),
            textposition='auto'
        )])
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="Faixa de Risco"),
            yaxis=dict(title="Qtd", showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("...")

# PD Lifetime Distribution by Risk Band
with col4:
    st.markdown("### 📉 PD Lifetime")
    if classifications:
        pd_life_values = [c.get('pd_lifetime', 0) * 100 for c in classifications]
        
        # Categorize by risk bands (lifetime has higher values)
        bands = {'<5%': 0, '5-20%': 0, '20-50%': 0, '50-80%': 0, '>80%': 0}
        for v in pd_life_values:
            if v < 5:
                bands['<5%'] += 1
            elif v < 20:
                bands['5-20%'] += 1
            elif v < 50:
                bands['20-50%'] += 1
            elif v < 80:
                bands['50-80%'] += 1
            else:
                bands['>80%'] += 1
        
        colors = ['#10b981', '#22c55e', '#f59e0b', '#f97316', '#ef4444']
        fig = go.Figure(data=[go.Bar(
            x=list(bands.keys()),
            y=list(bands.values()),
            marker_color=colors,
            text=list(bands.values()),
            textposition='auto'
        )])
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="Faixa de Risco"),
            yaxis=dict(title="Qtd", showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("...")

st.divider()

# ============================================================================
# 3. BATCH RESULTS (if available) or INTERACTIVE TABLE
# ============================================================================

# Check if batch results exist
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = None

# Initialize selected_data (used by detail panel later)
selected_data = None

if st.session_state.batch_results is not None and len(st.session_state.batch_results) > 0:
    st.markdown("### 📦 Resultados do Processamento em Lote")
    st.caption(f"Total: {len(st.session_state.batch_results)} registros. Role horizontalmente para ver todas as colunas.")
    
    # Display with horizontal scroll
    st.dataframe(
        st.session_state.batch_results,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Clear button
    if st.button("🗑️ Limpar Resultados do Lote", type="secondary"):
        st.session_state.batch_results = None
        st.rerun()

# Show "Classificações Recentes" ONLY when there are NO batch results
else:
    st.markdown("### 📋 Classificações Recentes")
    
    selected_data = None

    if classifications:
        # Prepare DataFrame for Display
        df_table = pd.DataFrame(classifications)
        
        # Get current mode
        current_mode = st.session_state.get('classification_mode', 'simple')
        is_explained_mode = 'explained' in current_mode
        
        # Base columns (always shown)
        cols_map = {
            'timestamp': 'Hora',
            'cpf': 'CPF',
            'prinad': 'PRINAD',
            'pd_12m': 'PD 12m',
            'pd_lifetime': 'PD Lifetime',
            'rating': 'Rating',
            'estagio_pe': 'Estágio'
        }
        
        # Ensure columns exist and map them
        df_disp = pd.DataFrame()
        for k, v in cols_map.items():
            if k in df_table.columns:
                if k == 'timestamp':
                    df_disp[v] = pd.to_datetime(df_table[k]).dt.strftime('%H:%M:%S')
                elif k == 'prinad':
                    df_disp[v] = df_table[k].apply(lambda x: f"{x:.1f}%")
                elif k in ['pd_12m', 'pd_lifetime']:
                    df_disp[v] = df_table[k].apply(lambda x: f"{x*100:.2f}%")
                else:
                    df_disp[v] = df_table[k]
        
        # Add explainability columns if in Explained mode
        if is_explained_mode:
            if 'acao_sugerida' in df_table.columns:
                df_disp['Ação Sugerida'] = df_table['acao_sugerida']
            
            # Extract SHAP top features if available
            if 'explicacao_shap' in df_table.columns:
                def get_shap_summary(shap_list):
                    if not shap_list or not isinstance(shap_list, list):
                        return ''
                    top = shap_list[:3] if len(shap_list) >= 3 else shap_list
                    return ', '.join([f"{s.get('feature','')}:{s.get('contribuicao',0):.1f}" for s in top])
                df_disp['Top SHAP'] = df_table['explicacao_shap'].apply(get_shap_summary)
            
            # Extract penalties if available
            if 'explicacao_completa' in df_table.columns:
                def get_penalties(exp):
                    if not exp or not isinstance(exp, dict):
                        return '', ''
                    comp = exp.get('composicao_prinad', {})
                    pen_int = comp.get('penalidade_interna', {}).get('valor', 0)
                    pen_ext = comp.get('penalidade_externa', {}).get('valor', 0)
                    return f"{pen_int}%", f"{pen_ext}%"
                df_disp['Pen.Int'] = df_table['explicacao_completa'].apply(lambda x: get_penalties(x)[0])
                df_disp['Pen.Ext'] = df_table['explicacao_completa'].apply(lambda x: get_penalties(x)[1])
        
        # Reverse order (newest first)
        df_disp = df_disp.iloc[::-1]
        
        # Interactive Table
        selection = st.dataframe(
            df_disp,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=300,
            key="recent_classifications" 
        )
        
        # Determine Selection with Persistence
        if 'selected_cpf' not in st.session_state:
            st.session_state.selected_cpf = None

        if len(selection.selection['rows']) > 0:
            # User clicked a row
            row_idx = selection.selection['rows'][0]
            # Map reversed index back to original list index
            idx = len(df_table) - 1 - row_idx
            if 0 <= idx < len(df_table):
                selected_data = classifications[idx]
                st.session_state.selected_cpf = selected_data.get('cpf')
        elif st.session_state.selected_cpf:
            # Try to restore from state (search by CPF)
            selected_data = next((c for c in classifications if c.get('cpf') == st.session_state.selected_cpf), None)

    else:
        st.info("Aguardando classificação...")

# ============================================================================
# 4. DETAIL / EXPLANABILITY PANEL
# ============================================================================

if selected_data:
    st.markdown("### 🔍 Análise de Crédito Detalhada")
    
    # Layout do Painel
    with st.container(border=True):
        # Header Info - 6 metrics columns
        top1, top2, top3, top4, top5, top6 = st.columns([2.5, 1.5, 1.5, 1.5, 1.5, 1.2])
        
        # Safe getters
        cpf_val = selected_data.get('cpf', 'N/A')
        rating_val = selected_data.get('rating', 'N/A')
        stage_val = selected_data.get('estagio_pe', '-')
        prinad_val = selected_data.get('prinad', 0)
        pd_12m_val = selected_data.get('pd_12m', 0) * 100
        pd_life_val = selected_data.get('pd_lifetime', 0) * 100
        action_val = selected_data.get('acao_sugerida', 'N/A')
        
        with top1: st.metric("🆔 CPF", cpf_val)
        with top2: st.metric("📊 PRINAD", f"{prinad_val:.1f}%")
        with top3: st.metric("⭐ Rating", rating_val)
        with top4: st.metric("📉 PD 12m", f"{pd_12m_val:.2f}%")
        with top5: st.metric("📉 PD Lifetime", f"{pd_life_val:.2f}%")
        with top6: st.metric("📈 Estágio PE", stage_val)
        
        # Ação Sugerida in highlighted row (full text visible)
        st.info(f"💡 **Ação Sugerida:** {action_val}")
        
        st.divider()
        
        # Explainability Content
        exp_col1, exp_col2 = st.columns([1, 1])
        
        with exp_col1:
            st.markdown("#### 🚨 Top 5 Fatores de Risco")
            shap_data = selected_data.get('explicacao_shap', [])
            
            # Feature name mapping for readability (all 45 model features)
            feature_names = {
                # Atrasos internos (v-columns)
                'v205': 'Atraso 1-30 dias',
                'v210': 'Atraso 31-60 dias',
                'v220': 'Atraso 61-90 dias',
                'v230': 'Atraso 91-120 dias',
                'v240': 'Atraso 121-150 dias',
                'v245': 'Atraso 151-180 dias',
                'v250': 'Atraso 181-210 dias',
                'v255': 'Atraso 211-240 dias',
                'v260': 'Atraso 241-270 dias',
                'v270': 'Atraso 271-300 dias',
                'v280': 'Atraso 301-330 dias',
                'v290': 'Atraso >330 dias (Prejuízo)',
                
                # SCR/Externo
                'scr_dias_atraso': 'Dias em Atraso (mercado)',
                'scr_score_risco': 'Score de Risco Externo',
                'scr_valor_vencido': 'Valor Vencido (mercado)',
                'scr_tem_prejuizo': 'Prejuízo no Mercado',
                
                # Perfil do cliente
                'IDADE_CLIENTE': 'Idade do Cliente',
                'idade_squared': 'Idade (efeito quadrático)',
                'RENDA_BRUTA': 'Renda Mensal',
                'TEMPO_RELAC': 'Tempo de Relacionamento',
                'log_tempo_relac': 'Tempo Relac. (ajustado)',
                'QT_PRODUTOS': 'Qtd Produtos Contratados',
                
                # Utilização de crédito
                'limite_total': 'Limite Total de Crédito',
                'limite_utilizado': 'Limite Utilizado',
                'taxa_utilizacao': 'Taxa de Utilização do Limite',
                'utilizacao_media_12m': 'Utilização Média 12m',
                'parcelas_mensais': 'Parcelas Mensais',
                'comprometimento_renda': 'Comprometimento de Renda',
                'COMP_RENDA': 'Comprometimento de Renda',
                'margem_disponivel': 'Margem de Crédito Disponível',
                'max_dias_atraso_12m': 'Máx. Dias Atraso 12m',
                
                # Escolaridade (one-hot)
                'ESCOLARIDADE_FUNDAM': 'Escolaridade: Fundamental',
                'ESCOLARIDADE_MEDIO': 'Escolaridade: Médio',
                'ESCOLARIDADE_SUPERIOR': 'Escolaridade: Superior',
                'ESCOLARIDADE_POS': 'Escolaridade: Pós-Grad.',
                'score_escolaridade': 'Score de Escolaridade',
                
                # Estado civil (one-hot)
                'ESTADO_CIVIL_CASADO': 'Estado Civil: Casado',
                'ESTADO_CIVIL_SOLTEIRO': 'Estado Civil: Solteiro',
                'ESTADO_CIVIL_DIVORCIADO': 'Estado Civil: Divorciado',
                'ESTADO_CIVIL_VIUVO': 'Estado Civil: Viúvo',
                'score_estado_civil': 'Score Estado Civil',
                
                # Veículo (one-hot) - Nota: modelo interpreta "não ter" como risco
                'POSSUI_VEICULO_NAO': 'Sem Patrimônio Veicular',
                'POSSUI_VEICULO_SIM': 'Possui Patrimônio Veicular',
                'tem_veiculo': 'Possui Veículo',
                
                # Flags booleanas
                'em_idade_ativa': 'Idade Produtiva (18-65)',
                'cliente_novo': 'Cliente Recente (<6m)',
                'trimestres_sem_uso': 'Trimestres de Inatividade',
            }
            
            if shap_data:
                # Filter ONLY risk-increasing factors (positive contribution)
                risk_factors = [s for s in shap_data if s.get('contribuicao', 0) > 0]
                risk_factors = sorted(risk_factors, key=lambda x: x.get('contribuicao', 0), reverse=True)[:5]
                
                if risk_factors:
                    feats = [feature_names.get(s.get('feature', ''), s.get('feature', '')) for s in risk_factors]
                    vals = [s.get('contribuicao', 0) for s in risk_factors]
                    
                    fig_shap = go.Figure(go.Bar(
                        x=vals, y=feats, orientation='h',
                        marker_color='#ef4444',
                        text=[f"+{v:.1f}%" for v in vals],
                        textposition='outside'
                    ))
                    fig_shap.update_layout(
                        height=180,
                        margin=dict(l=10, r=80, t=10, b=10),
                        yaxis=dict(showgrid=False, autorange='reversed'),
                        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', title='Impacto')
                    )
                    st.plotly_chart(fig_shap, use_container_width=True)
                    
                    if len(risk_factors) < 5:
                        st.caption(f"ℹ️ Apenas {len(risk_factors)} fator(es) de risco identificado(s).")
                else:
                    st.success("✅ Nenhum fator de risco significativo identificado.")
                
                # Section: Model Health (replaces Protective Factors)
                st.markdown("#### 🏥 Saúde do Modelo de Risco")
                
                # Load training metrics
                import joblib
                import os
                from datetime import datetime
                
                try:
                    metrics_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modelo', 'training_metrics.joblib')
                    training_data = joblib.load(metrics_path)
                    metrics = training_data.get('metrics', {})
                    
                    # Get file modification time as training date
                    train_date = datetime.fromtimestamp(os.path.getmtime(metrics_path)).strftime('%d/%m/%Y')
                    
                    st.caption(f"📅 Último treinamento: **{train_date}**")
                    
                    # Metrics table (use precision_bad and recall_bad for bad payer detection)
                    metrics_table = f"""
| Métrica | Valor |
|---------|-------|
| AUC-ROC | {metrics.get('auc_roc', 0)*100:.1f}% |
| Gini | {metrics.get('gini', 0)*100:.1f}% |
| KS | {metrics.get('ks', 0)*100:.1f}% |
| Precision | {metrics.get('precision_bad', 0)*100:.1f}% |
| Recall | {metrics.get('recall_bad', 0)*100:.1f}% |
"""
                    st.markdown(metrics_table)
                    
                    st.caption("""
• **AUC-ROC**: Capacidade de distinguir bons de maus pagadores.  
• **Gini**: Poder discriminatório do modelo.  
• **KS**: Separação máxima entre curvas de bons e maus.  
• **Precision**: Taxa de acerto nas previsões de inadimplência.  
• **Recall**: Cobertura de inadimplentes identificados.
""")
                except Exception as e:
                    st.caption("⚠️ Métricas do modelo não disponíveis.")
            else:
                st.info("ℹ️ Para ver os fatores de risco, use o modo **Explicado**.")
                
        with exp_col2:
            st.markdown("#### 📋 Relatório de Análise")
            full_exp = selected_data.get('explicacao_completa', {})
            
            if full_exp:
                comp_prinad = full_exp.get('composicao_prinad', {})
                rat_info = full_exp.get('rating', {})
                stage_info = full_exp.get('estagio_pe', {})
                perdao_info = full_exp.get('elegibilidade_perdao', {})
                
                pen_int = comp_prinad.get('penalidade_interna', {})
                pen_ext = comp_prinad.get('penalidade_externa', {})
                
                # Compose readable report
                pd_ml = comp_prinad.get('pd_modelo_ml', {}).get('valor', 0)
                pen_int_val = pen_int.get('valor', 0)
                pen_ext_val = pen_ext.get('valor', 0)
                meses_int = pen_int.get('meses_desde_atraso', 'N/A')
                meses_ext = pen_ext.get('meses_desde_atraso', 'N/A')
                
                # Map "nivel_delinquencia" to professional terms
                situacao_map = {
                    'clean': '🟢 Adimplente',
                    'leve': '🟡 Atenção',
                    'moderado': '🟠 Risco Moderado',
                    'severo': '🔴 Risco Elevado',
                    'critico': '⚫ Crítico'
                }
                situacao_raw = perdao_info.get('nivel_delinquencia', 'desconhecido')
                situacao = situacao_map.get(situacao_raw, f"⚪ {situacao_raw.capitalize()}")
                
                # Eligibility for recovery
                elegivel = perdao_info.get('elegivel', False)
                elegivel_txt = "✅ Sim - histórico limpo há 6+ meses" if elegivel else "❌ Não - requer período de regularização"
                
                # Build markdown report
                # Calculate the real formula: PRINAD = PD_Base * (1 + Pen_Int + Pen_Ext)
                # Note: pen_int_val and pen_ext_val are already in % (e.g., 55 means 55%)
                # But the formula uses them as multipliers, so 55% = 0.55
                pen_int_mult = pen_int_val / 100 if pen_int_val > 1 else pen_int_val
                pen_ext_mult = pen_ext_val / 100 if pen_ext_val > 1 else pen_ext_val
                total_mult = 1 + pen_int_mult + pen_ext_mult
                calculated_prinad = min(100, pd_ml * total_mult)
                
                report = f"""
**🏷️ Classificação Final:** {rat_info.get('descricao', 'N/A')}  
_{rat_info.get('justificativa', '')}_

---

**📊 Composição do Score PRINAD**

| Componente | Valor | Multiplicador |
|:-----------|:-----:|:-------------:|
| Score Base (Modelo ML) | {pd_ml:.1f}% | Base |
| Penalidade Interna | +{pen_int_val:.0f}% | ×{1+pen_int_mult:.2f} |
| Penalidade Externa (SCR) | +{pen_ext_val:.0f}% | ×{1+pen_ext_mult:.2f} |

**Fórmula:** `min(PD_Base × (1 + Pen_Int + Pen_Ext), 100)`  
**Cálculo:** `min({pd_ml:.1f}% × {total_mult:.2f}, 100) = {prinad_val:.1f}%`  
**PRINAD Final:** **{prinad_val:.1f}%**

---

**📅 Situação do Histórico**

- **Interno:** Último evento há `{meses_int}` meses
- **Externo:** Último evento há `{meses_ext}` meses
- **Situação Geral:** {situacao}

---

**🔄 Elegibilidade para Reavaliação**

{elegivel_txt}

---

**💼 Ação Recomendada:** {action_val}
"""
                st.markdown(report)
            else:
                st.info("ℹ️ Relatório detalhado disponível apenas no modo **Explicado**.")
        
        # Optional: Show raw data in expander
        with st.expander("🔧 Dados Técnicos (Avançado)", expanded=False):
            st.caption("Informações técnicas para análise detalhada.")
            st.json(selected_data)
else:
    st.info("👆 **Selecione um cliente na tabela acima** para ver a análise de crédito detalhada (Fatores de Risco, Histórico e Sugestões).")

# ============================================================================
# 5. STREAMING EXECUTION LOOP
# ============================================================================

if st.session_state.streaming_active and st.session_state.available_cpfs:
    if 'batch' in st.session_state.classification_mode:
        st.session_state.streaming_active = False
        st.rerun()
        
    import random
    import time
    
    # Rate limiter
    time.sleep(st.session_state.get('interval', 2))
    
    # Pick CPF
    cpf = random.choice(st.session_state.available_cpfs)
    
    # Determine mode
    mode = st.session_state.classification_mode
    is_explained = (mode == 'explained')
    
    # Call API
    result = classify_cpf(cpf, explained=is_explained)
    
    if 'error' not in result:
        # FORCE fix for CPF being 'unknown' or missing
        # The API might return 'unknown' if not properly mapped, so we override it with the input CPF
        if 'cpf' not in result or str(result['cpf']).lower() == 'unknown':
             result['cpf'] = cpf
             
        # Add timestamp
        result['timestamp'] = datetime.now().isoformat()
        
        # Append
        st.session_state.classifications.append(result)
        
        # Trim
        if len(st.session_state.classifications) > 500:
            st.session_state.classifications = st.session_state.classifications[-500:]
            
        st.rerun()
    else:
        st.session_state.errors_count += 1
        st.rerun()
else:
    # Footer
    st.markdown("---")
    if not st.session_state.available_cpfs and not st.session_state.streaming_active:
         st.info("💡 Clique em **▶️ Iniciar** para carregar CPFs e começar.")
    elif st.session_state.available_cpfs and not st.session_state.streaming_active:
         st.info("💡 Clique em **▶️ Iniciar** para continuar o streaming.")

