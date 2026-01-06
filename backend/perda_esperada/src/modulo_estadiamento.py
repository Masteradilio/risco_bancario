# -*- coding: utf-8 -*-
"""
Módulo de Estadiamento - Classificação de contratos em estágios conforme IFRS 9

Inclui:
- Classificação de estágios (1, 2, 3)
- Regras de cura por modalidade
- Métricas de estadiamento
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import sys
import os

# Adicionar o caminho do projeto ao sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# =============================================================================
# PERÍODOS DE CURA POR MODALIDADE (Integrado de modulo_modelo_cura.py)
# =============================================================================
# Conforme documentação técnica BIP e Resolução CMN nº 4.966

PERIODOS_CURA = {
    'parcelado': {
        'estagio_2_para_1': 5,   # meses
        'estagio_3_para_2': 9,   # meses
        'estagio_3_para_1': 14   # Soma (requer passar por E2 primeiro)
    },
    'parcelados': {
        'estagio_2_para_1': 5,
        'estagio_3_para_2': 9,
        'estagio_3_para_1': 14
    },
    'rotativo': {
        'estagio_2_para_1': 2,
        'estagio_3_para_2': 7,
        'estagio_3_para_1': 9
    },
    'rotativos': {
        'estagio_2_para_1': 2,
        'estagio_3_para_2': 7,
        'estagio_3_para_1': 9
    },
    'consignado': {
        'estagio_2_para_1': 3,
        'estagio_3_para_2': 6,
        'estagio_3_para_1': 9
    }
}

# Funções utilitárias locais (substituindo utils.csv_utils)
def ler_csv_inteligente(filepath: str, **kwargs) -> pd.DataFrame:
    """Lê CSV com detecção automática de separador e encoding."""
    for sep in [';', ',', '\t']:
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return pd.read_csv(filepath, sep=sep, encoding=enc, **kwargs)
            except:
                continue
    return pd.read_csv(filepath, **kwargs)

def validar_colunas_obrigatorias(df: pd.DataFrame, colunas: list) -> bool:
    """Valida se colunas obrigatórias existem no DataFrame."""
    return all(col in df.columns for col in colunas)

def processar_colunas_numericas(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    """Converte colunas para numérico."""
    df = df.copy()
    for col in colunas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

logger = logging.getLogger(__name__)


def classificar_estagio_aprimorado(df: pd.DataFrame, 
                                 col_dias_atraso: str = 'dias_atraso',
                                 col_pd_concessao: str = 'pd_concessao',
                                 col_pd_behavior: str = 'pd_behavior',
                                 col_id_operacao: str = 'id_operacao',
                                 **kwargs) -> pd.DataFrame:
    """
    Classifica contratos em estágios conforme IFRS 9
    
    Estágio 1: Perda esperada de 12 meses
    Estágio 2: Perda esperada de vida toda (aumento significativo do risco)
    Estágio 3: Perda esperada de vida toda (evidência objetiva de perda)
    """
    df_estagiado = df.copy()
    
    # Garantir que a coluna de estágio existe
    if 'estagio' not in df_estagiado.columns:
        df_estagiado['estagio'] = 1  # Padrão Estágio 1
    
    # Garantir que colunas necessárias existem com valores padrão
    if col_dias_atraso not in df_estagiado.columns:
        logger.warning(f"Coluna '{col_dias_atraso}' não encontrada. Usando 0 como padrão.")
        df_estagiado[col_dias_atraso] = 0
    
    if col_pd_concessao not in df_estagiado.columns:
        logger.warning(f"Coluna '{col_pd_concessao}' não encontrada. Usando 0.05 como padrão.")
        df_estagiado[col_pd_concessao] = 0.05
    
    if col_pd_behavior not in df_estagiado.columns:
        logger.warning(f"Coluna '{col_pd_behavior}' não encontrada. Usando 0.05 como padrão.")
        df_estagiado[col_pd_behavior] = 0.05
    
    # Converter para numérico se necessário
    df_estagiado[col_dias_atraso] = pd.to_numeric(df_estagiado[col_dias_atraso], errors='coerce').fillna(0)
    df_estagiado[col_pd_concessao] = pd.to_numeric(df_estagiado[col_pd_concessao], errors='coerce').fillna(0.05)
    df_estagiado[col_pd_behavior] = pd.to_numeric(df_estagiado[col_pd_behavior], errors='coerce').fillna(0.05)
    
    # Critérios para Estágio 3 (Default)
    # Atraso >= 90 dias ou sinais objetivos de perda
    criterio_estagio_3 = (
        (df_estagiado[col_dias_atraso] >= 90) |
        (df_estagiado[col_pd_behavior] >= 0.95)  # PD muito alta indica default
    )
    
    # Critérios para Estágio 2 (Aumento significativo do risco)
    # Atraso entre 30-89 dias ou aumento significativo da PD
    aumento_significativo_pd = df_estagiado[col_pd_behavior] >= (df_estagiado[col_pd_concessao] * 2)
    
    criterio_estagio_2 = (
        (df_estagiado[col_dias_atraso].between(30, 89)) |
        (aumento_significativo_pd & (df_estagiado[col_pd_behavior] >= 0.1)) |
        (df_estagiado[col_dias_atraso].between(1, 29) & (df_estagiado[col_pd_behavior] >= 0.3))
    )
    
    # Aplicar classificação
    df_estagiado.loc[criterio_estagio_3, 'estagio'] = 3
    df_estagiado.loc[criterio_estagio_2 & ~criterio_estagio_3, 'estagio'] = 2
    df_estagiado.loc[~criterio_estagio_2 & ~criterio_estagio_3, 'estagio'] = 1
    
    # Garantir que estágios são inteiros
    df_estagiado['estagio'] = df_estagiado['estagio'].astype(int)
    
    # Estatísticas da classificação
    distribuicao_estagios = df_estagiado['estagio'].value_counts().sort_index()
    logger.info(f"Distribuição dos estágios: {distribuicao_estagios.to_dict()}")
    
    # Adicionar flags de critérios aplicados
    df_estagiado['flag_atraso_90d'] = df_estagiado[col_dias_atraso] >= 90
    df_estagiado['flag_atraso_30d'] = df_estagiado[col_dias_atraso] >= 30
    df_estagiado['flag_aumento_pd'] = aumento_significativo_pd
    
    return df_estagiado

def aplicar_regras_cura_estagio(df: pd.DataFrame, 
                               col_dias_atraso: str = 'dias_atraso',
                               col_estagio: str = 'estagio') -> pd.DataFrame:
    """
    Aplica regras de cura para rebaixamento de estágio
    """
    df_curado = df.copy()
    
    if col_estagio not in df_curado.columns:
        logger.warning(f"Coluna '{col_estagio}' não encontrada. Aplicando classificação primeiro.")
        df_curado = classificar_estagio_aprimorado(df_curado, col_dias_atraso=col_dias_atraso)
    
    if col_dias_atraso not in df_curado.columns:
        logger.warning(f"Coluna '{col_dias_atraso}' não encontrada. Não é possível aplicar cura.")
        return df_curado
    
    df_curado[col_dias_atraso] = pd.to_numeric(df_curado[col_dias_atraso], errors='coerce').fillna(0)
    
    # Regras de cura
    # Estágio 3 -> Estágio 2: se dias_atraso < 90 e houve pagamento
    cura_3_para_2 = (df_curado[col_estagio] == 3) & (df_curado[col_dias_atraso] < 90)
    
    # Estágio 2 -> Estágio 1: se dias_atraso < 30 e PD melhorou
    cura_2_para_1 = (df_curado[col_estagio] == 2) & (df_curado[col_dias_atraso] < 30)
    
    # Aplicar curas
    contratos_curados = 0
    
    if cura_3_para_2.any():
        df_curado.loc[cura_3_para_2, col_estagio] = 2
        contratos_curados += cura_3_para_2.sum()
        logger.info(f"Cura Estágio 3->2: {cura_3_para_2.sum()} contratos")
    
    if cura_2_para_1.any():
        df_curado.loc[cura_2_para_1, col_estagio] = 1
        contratos_curados += cura_2_para_1.sum()
        logger.info(f"Cura Estágio 2->1: {cura_2_para_1.sum()} contratos")
    
    logger.info(f"Total de contratos curados: {contratos_curados}")
    
    return df_curado

def calcular_metricas_estagio(df: pd.DataFrame, col_estagio: str = 'estagio', col_valor: str = 'saldo_devedor') -> Dict[str, Any]:
    """
    Calcula métricas por estágio
    """
    if col_estagio not in df.columns:
        logger.error(f"Coluna '{col_estagio}' não encontrada para cálculo de métricas.")
        return {}
    
    if col_valor not in df.columns:
        logger.warning(f"Coluna '{col_valor}' não encontrada. Usando 1 como valor padrão.")
        df = df.copy()
        df[col_valor] = 1
    
    metricas = {}
    
    for estagio in sorted(df[col_estagio].unique()):
        subset = df[df[col_estagio] == estagio]
        
        metricas[f'estagio_{estagio}'] = {
            'quantidade_contratos': len(subset),
            'percentual_contratos': len(subset) / len(df) * 100,
            'valor_total': subset[col_valor].sum(),
            'valor_medio': subset[col_valor].mean(),
            'percentual_valor': subset[col_valor].sum() / df[col_valor].sum() * 100
        }
    
    logger.info(f"Métricas calculadas para {len(metricas)} estágios")
    return metricas

def processar_estadiamento_completo(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Processa estadiamento completo com validação e tratamento de dados.
    
    Args:
        df_input: DataFrame com dados da carteira
        
    Returns:
        DataFrame com estadiamento aplicado
    """
    df = df_input.copy()
    
    # Colunas esperadas (com fallbacks)
    colunas_esperadas = {
        'dias_atraso': 0,
        'pd_12m': 0.05,
        'pd_lifetime': 0.05,
        'saldo_devedor': 1000,
        'id_contrato': None
    }
    
    # Adicionar colunas faltantes com valores padrão
    for coluna, valor_padrao in colunas_esperadas.items():
        if coluna not in df.columns:
            if coluna == 'id_contrato':
                df[coluna] = range(1, len(df) + 1)
            else:
                df[coluna] = valor_padrao
            logger.warning(f"Coluna '{coluna}' não encontrada. Usando valor padrão: {valor_padrao}")
    
    # Processar colunas numéricas
    colunas_numericas = ['dias_atraso', 'pd_12m', 'pd_lifetime', 'saldo_devedor']
    df = processar_colunas_numericas(df, colunas_numericas)
    
    # Aplicar classificação de estágio
    df_estagiado = classificar_estagio_aprimorado(
        df,
        col_dias_atraso='dias_atraso',
        col_pd_concessao='pd_12m',
        col_pd_behavior='pd_lifetime'
    )
    
    # Aplicar regras de cura
    df_final = aplicar_regras_cura_estagio(
        df_estagiado,
        col_dias_atraso='dias_atraso',
        col_estagio='estagio'
    )
    
    return df_final

def carregar_e_processar_estadiamento(file_path: str) -> pd.DataFrame:
    """
    Carrega arquivo CSV e processa estadiamento.
    
    Args:
        file_path: Caminho para o arquivo CSV
        
    Returns:
        DataFrame com estadiamento processado
    """
    try:
        # Carregar dados com detecção automática
        df = ler_csv_inteligente(file_path)
        logger.info(f"Arquivo carregado com sucesso: {len(df)} registros")
        
        # Processar estadiamento
        df_processado = processar_estadiamento_completo(df)
        
        return df_processado
        
    except Exception as e:
        logger.error(f"Erro ao carregar e processar estadiamento: {str(e)}")
        raise
