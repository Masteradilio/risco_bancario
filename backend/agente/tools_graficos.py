# -*- coding: utf-8 -*-
"""
Ferramentas de Geração de Gráficos para o Agente IA
Usa Seaborn/Matplotlib com tema customizado
"""

import io
import base64
import logging
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Backend não-interativo
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ============================================================================
# TEMAS DE CORES
# ============================================================================

# Tema escuro (combina com o app)
TEMA_DARK = {
    "background": "#0a0a0a",
    "paper": "#1a1a2e",
    "text": "#ffffff",
    "grid": "#333344",
    "primary": "#a855f7",    # Purple
    "secondary": "#06b6d4",  # Cyan
    "success": "#22c55e",    # Green
    "warning": "#f59e0b",    # Amber
    "danger": "#ef4444",     # Red
    "palette": ["#a855f7", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#ec4899", "#3b82f6", "#14b8a6"]
}

# Tema claro (para impressão)
TEMA_LIGHT = {
    "background": "#ffffff",
    "paper": "#f8fafc",
    "text": "#1e293b",
    "grid": "#e2e8f0",
    "primary": "#7c3aed",
    "secondary": "#0891b2",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "palette": ["#7c3aed", "#0891b2", "#16a34a", "#d97706", "#dc2626", "#db2777", "#2563eb", "#0d9488"]
}


def aplicar_tema(tema: str = "dark"):
    """Aplica tema aos gráficos."""
    colors = TEMA_DARK if tema == "dark" else TEMA_LIGHT
    
    plt.rcParams.update({
        "figure.facecolor": colors["background"],
        "axes.facecolor": colors["paper"],
        "axes.edgecolor": colors["grid"],
        "axes.labelcolor": colors["text"],
        "text.color": colors["text"],
        "xtick.color": colors["text"],
        "ytick.color": colors["text"],
        "grid.color": colors["grid"],
        "legend.facecolor": colors["paper"],
        "legend.edgecolor": colors["grid"],
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
    })
    
    sns.set_palette(colors["palette"])
    return colors


# ============================================================================
# TIPOS DE GRÁFICOS DISPONÍVEIS
# ============================================================================

TIPOS_GRAFICOS = {
    "linha": "Gráfico de linhas - ideal para tendências temporais",
    "barra": "Gráfico de barras - comparação entre categorias",
    "barra_horizontal": "Gráfico de barras horizontais - categorias com nomes longos",
    "pizza": "Gráfico de pizza - proporções de um todo",
    "donut": "Gráfico de rosca - proporções com destaque central",
    "area": "Gráfico de área - evolução com volume",
    "dispersao": "Gráfico de dispersão - correlação entre variáveis",
    "heatmap": "Mapa de calor - matriz de correlação",
    "boxplot": "Boxplot - distribuição estatística",
    "histograma": "Histograma - distribuição de frequência",
    "waterfall": "Gráfico cascata - composição de valor",
}


def gerar_grafico_linha(
    dados: pd.DataFrame,
    x: str,
    y: str,
    titulo: str,
    xlabel: str = None,
    ylabel: str = None,
    legenda: str = None,
    tema: str = "dark",
    figsize: tuple = (10, 6)
) -> bytes:
    """Gera gráfico de linhas."""
    colors = aplicar_tema(tema)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.lineplot(data=dados, x=x, y=y, marker='o', linewidth=2.5, 
                 markersize=8, color=colors["primary"], ax=ax)
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel or x, fontsize=11)
    ax.set_ylabel(ylabel or y, fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Adicionar valores nos pontos
    for i, (xi, yi) in enumerate(zip(dados[x], dados[y])):
        ax.annotate(f'{yi:,.0f}', (i, yi), textcoords="offset points", 
                   xytext=(0, 10), ha='center', fontsize=8,
                   color=colors["text"])
    
    # Legenda explicativa
    if legenda:
        ax.text(0.02, 0.98, legenda, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', style='italic', 
               color=colors["text"], alpha=0.8)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=colors["background"])
    plt.close()
    
    return buf.getvalue()


def gerar_grafico_barra(
    dados: pd.DataFrame,
    x: str,
    y: str,
    titulo: str,
    xlabel: str = None,
    ylabel: str = None,
    hue: str = None,
    horizontal: bool = False,
    legenda: str = None,
    tema: str = "dark",
    figsize: tuple = (10, 6)
) -> bytes:
    """Gera gráfico de barras (vertical ou horizontal)."""
    colors = aplicar_tema(tema)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if horizontal:
        sns.barplot(data=dados, x=y, y=x, hue=hue, palette=colors["palette"], ax=ax)
        ax.set_xlabel(ylabel or y)
        ax.set_ylabel(xlabel or x)
    else:
        sns.barplot(data=dados, x=x, y=y, hue=hue, palette=colors["palette"], ax=ax)
        ax.set_xlabel(xlabel or x)
        ax.set_ylabel(ylabel or y)
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y' if not horizontal else 'x')
    
    # Adicionar valores nas barras
    for container in ax.containers:
        ax.bar_label(container, fmt='%.0f', fontsize=8, color=colors["text"])
    
    if legenda:
        ax.text(0.02, 0.98, legenda, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', style='italic', 
               color=colors["text"], alpha=0.8)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=colors["background"])
    plt.close()
    
    return buf.getvalue()


def gerar_grafico_pizza(
    dados: pd.DataFrame,
    valores: str,
    labels: str,
    titulo: str,
    donut: bool = False,
    legenda: str = None,
    tema: str = "dark",
    figsize: tuple = (8, 8)
) -> bytes:
    """Gera gráfico de pizza ou donut."""
    colors = aplicar_tema(tema)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    wedges, texts, autotexts = ax.pie(
        dados[valores],
        labels=dados[labels],
        autopct='%1.1f%%',
        colors=colors["palette"][:len(dados)],
        explode=[0.02] * len(dados),
        shadow=False,
        startangle=90
    )
    
    # Estilo dos textos
    for text in texts:
        text.set_color(colors["text"])
        text.set_fontsize(10)
    for autotext in autotexts:
        autotext.set_color(colors["background"] if tema == "dark" else "white")
        autotext.set_fontweight('bold')
    
    if donut:
        centre_circle = plt.Circle((0, 0), 0.55, fc=colors["background"])
        ax.add_patch(centre_circle)
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=15)
    
    if legenda:
        ax.text(0.5, -0.1, legenda, transform=ax.transAxes, fontsize=9,
               ha='center', style='italic', color=colors["text"], alpha=0.8)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=colors["background"])
    plt.close()
    
    return buf.getvalue()


def gerar_grafico_area(
    dados: pd.DataFrame,
    x: str,
    y: List[str],
    titulo: str,
    xlabel: str = None,
    ylabel: str = None,
    stacked: bool = True,
    legenda: str = None,
    tema: str = "dark",
    figsize: tuple = (10, 6)
) -> bytes:
    """Gera gráfico de área empilhada ou não."""
    colors = aplicar_tema(tema)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if stacked:
        ax.stackplot(dados[x], [dados[col] for col in y], labels=y,
                    colors=colors["palette"][:len(y)], alpha=0.8)
    else:
        for i, col in enumerate(y):
            ax.fill_between(dados[x], dados[col], alpha=0.5, 
                          color=colors["palette"][i], label=col)
            ax.plot(dados[x], dados[col], color=colors["palette"][i], linewidth=2)
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or "Valor")
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    if legenda:
        ax.text(0.02, 0.02, legenda, transform=ax.transAxes, fontsize=9,
               style='italic', color=colors["text"], alpha=0.8)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=colors["background"])
    plt.close()
    
    return buf.getvalue()


def gerar_grafico_heatmap(
    dados: pd.DataFrame,
    titulo: str,
    annot: bool = True,
    legenda: str = None,
    tema: str = "dark",
    figsize: tuple = (10, 8)
) -> bytes:
    """Gera mapa de calor (correlação ou matriz)."""
    colors = aplicar_tema(tema)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Se for numérico, calcular correlação
    numeric_cols = dados.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 1:
        corr_matrix = dados[numeric_cols].corr()
    else:
        corr_matrix = dados
    
    cmap = "RdYlGn" if tema == "light" else "coolwarm"
    
    sns.heatmap(corr_matrix, annot=annot, cmap=cmap, center=0,
               square=True, linewidths=0.5, ax=ax,
               annot_kws={"size": 9, "color": colors["text"]})
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=15)
    
    if legenda:
        ax.text(0.5, -0.1, legenda, transform=ax.transAxes, fontsize=9,
               ha='center', style='italic', color=colors["text"], alpha=0.8)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=colors["background"])
    plt.close()
    
    return buf.getvalue()


def gerar_grafico_dispersao(
    dados: pd.DataFrame,
    x: str,
    y: str,
    titulo: str,
    hue: str = None,
    size: str = None,
    legenda: str = None,
    tema: str = "dark",
    figsize: tuple = (10, 6)
) -> bytes:
    """Gera gráfico de dispersão."""
    colors = aplicar_tema(tema)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.scatterplot(data=dados, x=x, y=y, hue=hue, size=size,
                   palette=colors["palette"], ax=ax, alpha=0.7)
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Linha de tendência
    z = np.polyfit(dados[x], dados[y], 1)
    p = np.poly1d(z)
    ax.plot(dados[x].sort_values(), p(dados[x].sort_values()), 
           linestyle='--', color=colors["warning"], alpha=0.8,
           label=f'Tendência (R² = {np.corrcoef(dados[x], dados[y])[0,1]**2:.3f})')
    ax.legend()
    
    if legenda:
        ax.text(0.02, 0.98, legenda, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', style='italic', 
               color=colors["text"], alpha=0.8)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=colors["background"])
    plt.close()
    
    return buf.getvalue()


def gerar_grafico_boxplot(
    dados: pd.DataFrame,
    x: str,
    y: str,
    titulo: str,
    legenda: str = None,
    tema: str = "dark",
    figsize: tuple = (10, 6)
) -> bytes:
    """Gera boxplot para análise de distribuição."""
    colors = aplicar_tema(tema)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.boxplot(data=dados, x=x, y=y, palette=colors["palette"], ax=ax)
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    if legenda:
        ax.text(0.02, 0.98, legenda, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', style='italic', 
               color=colors["text"], alpha=0.8)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=colors["background"])
    plt.close()
    
    return buf.getvalue()


def gerar_grafico_histograma(
    dados: pd.DataFrame,
    coluna: str,
    titulo: str,
    bins: int = 20,
    kde: bool = True,
    legenda: str = None,
    tema: str = "dark",
    figsize: tuple = (10, 6)
) -> bytes:
    """Gera histograma com curva de densidade."""
    colors = aplicar_tema(tema)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.histplot(data=dados, x=coluna, bins=bins, kde=kde,
                color=colors["primary"], alpha=0.7, ax=ax)
    
    ax.set_title(titulo, fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Estatísticas
    media = dados[coluna].mean()
    mediana = dados[coluna].median()
    ax.axvline(media, color=colors["warning"], linestyle='--', 
              label=f'Média: {media:,.2f}')
    ax.axvline(mediana, color=colors["success"], linestyle='-.',
              label=f'Mediana: {mediana:,.2f}')
    ax.legend()
    
    if legenda:
        ax.text(0.02, 0.98, legenda, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', style='italic', 
               color=colors["text"], alpha=0.8)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=colors["background"])
    plt.close()
    
    return buf.getvalue()


# ============================================================================
# FUNÇÃO PRINCIPAL DE GERAÇÃO
# ============================================================================


def gerar_grafico(
    tipo: str,
    dados: pd.DataFrame,
    config: Dict[str, Any],
    tema: str = "dark"
) -> bytes:
    """
    Função principal para gerar qualquer tipo de gráfico.
    
    Args:
        tipo: Tipo do gráfico (linha, barra, pizza, etc.)
        dados: DataFrame com os dados
        config: Configurações específicas do gráfico
        tema: 'dark' ou 'light'
    
    Returns:
        Bytes da imagem PNG
    """
    logger.info(f"Gerando gráfico tipo '{tipo}' com tema '{tema}'")
    
    try:
        if tipo == "linha":
            return gerar_grafico_linha(dados, tema=tema, **config)
            
        elif tipo == "barra":
            return gerar_grafico_barra(dados, horizontal=False, tema=tema, **config)
            
        elif tipo == "barra_horizontal":
            return gerar_grafico_barra(dados, horizontal=True, tema=tema, **config)
            
        elif tipo == "pizza":
            return gerar_grafico_pizza(dados, donut=False, tema=tema, **config)
            
        elif tipo == "donut":
            return gerar_grafico_pizza(dados, donut=True, tema=tema, **config)
            
        elif tipo == "area":
            return gerar_grafico_area(dados, tema=tema, **config)
            
        elif tipo == "dispersao":
            return gerar_grafico_dispersao(dados, tema=tema, **config)
            
        elif tipo == "heatmap":
            return gerar_grafico_heatmap(dados, tema=tema, **config)
            
        elif tipo == "boxplot":
            return gerar_grafico_boxplot(dados, tema=tema, **config)
            
        elif tipo == "histograma":
            return gerar_grafico_histograma(dados, tema=tema, **config)
            
        else:
            raise ValueError(f"Tipo de gráfico '{tipo}' não suportado.")
            
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico {tipo}: {e}")
        # Em caso de erro, re-raise para ser tratado pelo chamador
        raise e

__all__ = [
    "gerar_grafico",
    "gerar_grafico_linha",
    "gerar_grafico_barra",
    "gerar_grafico_pizza",
    "gerar_grafico_area",
    "gerar_grafico_heatmap",
    "gerar_grafico_dispersao",
    "gerar_grafico_boxplot",
    "gerar_grafico_histograma",
    "TIPOS_GRAFICOS"
]
