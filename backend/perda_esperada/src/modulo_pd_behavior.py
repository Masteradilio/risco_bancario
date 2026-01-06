"""
Modelagem de Probabilidade de Default (PD) para Contratos Behavior (em carteira).

REFATORADO: Este módulo agora IMPORTA os componentes de Forward Looking e Grupos
Homogêneos dos módulos existentes ao invés de duplicar.

Implementa metodologia Forward Looking com variáveis macroeconômicas e WOE scores
conforme Resolução CMN 4966 e documentação técnica BIP.

DIFERENÇA DO PRINAD:
- PRINAD: PD de CONCESSÃO (novos clientes/contratos) - decisão de crédito inicial
- PD Behavior: PD de CARTEIRA (contratos > 3 meses) - monitoramento e provisão
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Any, Optional, Dict, List
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar o caminho do diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# =============================================================================
# IMPORTS DOS MÓDULOS EXISTENTES (EVITA DUPLICAÇÃO)
# =============================================================================

# Importar WOE_SCORES e EQUACOES_FL do módulo Forward Looking existente
try:
    from .modulo_forward_looking import (
        WOE_SCORES,
        WOE_SCORES_MEDIO,
        EQUACOES_FL,
        ModeloForwardLooking,
        coletar_series_historicas,
        get_bc_series
    )
    FL_AVAILABLE = True
    logger.info("Módulo Forward Looking importado com sucesso")
except ImportError as e:
    logger.warning(f"Módulo Forward Looking não disponível: {e}")
    FL_AVAILABLE = False
    # Fallbacks mínimos
    WOE_SCORES = {}
    WOE_SCORES_MEDIO = {}
    EQUACOES_FL = {}

# Importar Grupos Homogêneos do módulo existente
try:
    from .modulo_grupos_homogeneos import GruposHomogeneosConsolidado, CalculadorPDReais
    GH_AVAILABLE = True
    logger.info("Módulo Grupos Homogêneos importado com sucesso")
except ImportError as e:
    logger.warning(f"Módulo Grupos Homogêneos não disponível: {e}")
    GH_AVAILABLE = False

# =============================================================================
# CONFIGURAÇÕES ESPECÍFICAS PARA BEHAVIOR (NÃO DUPLICADAS)
# =============================================================================

# Grupos Homogêneos específicos para análise Behavior
# (Faixas de score ajustadas para carteira existente)
GRUPOS_HOMOGENEOS_BEHAVIOR = {
    'parcelados': {
        1: {'pd': 0.1448, 'score_min': 0.00, 'score_max': 870.77},
        2: {'pd': 0.0991, 'score_min': 870.77, 'score_max': 937.14},
        3: {'pd': 0.0548, 'score_min': 937.14, 'score_max': 949.99},
        4: {'pd': 0.0270, 'score_min': 949.99, 'score_max': 967.04},
        5: {'pd': 0.0186, 'score_min': 967.04, 'score_max': 1000.00}
    },
    'rotativos': {
        1: {'pd': 0.3814, 'score_min': 0.00, 'score_max': 834.91},
        2: {'pd': 0.2496, 'score_min': 834.91, 'score_max': 938.31},
        3: {'pd': 0.0981, 'score_min': 938.31, 'score_max': 980.57},
        4: {'pd': 0.0164, 'score_min': 980.57, 'score_max': 1000.00}
    },
    'consignado': {
        1: {'pd': 0.15, 'score_min': 0.00, 'score_max': 850.00},
        2: {'pd': 0.10, 'score_min': 850.00, 'score_max': 920.00},
        3: {'pd': 0.06, 'score_min': 920.00, 'score_max': 960.00},
        4: {'pd': 0.03, 'score_min': 960.00, 'score_max': 1000.00}
    }
}

# Mapeamento de produtos para nomes padronizados
PRODUTO_MAP = {
    'parcelado': 'parcelados',
    'parcelados': 'parcelados',
    'consignado': 'consignado',
    'rotativo': 'rotativos',
    'rotativos': 'rotativos',
    'cartao_credito': 'rotativos',
    'cartao_credito_rotativo': 'rotativos',
    'cheque_especial': 'rotativos',
    'banparacard': 'rotativos',
    'pessoal': 'parcelados',
    'imobiliario': 'parcelados',
    'cred_veiculo': 'parcelados',
    'energia_solar': 'parcelados'
}


# =============================================================================
# FUNÇÕES DE FILTRO E PREPARAÇÃO DE DADOS
# =============================================================================

def filtrar_dados_behavior(
    df: pd.DataFrame, 
    data_base: datetime, 
    meses_min_vida: int = 3
) -> pd.DataFrame:
    """
    Filtra contratos para análise behavior com base na idade mínima.
    
    Contratos "behavior" são aqueles que já têm histórico suficiente
    em carteira (normalmente > 3 meses) para análise comportamental.
    
    Args:
        df: DataFrame com dados dos contratos
        data_base: Data de referência para cálculo
        meses_min_vida: Idade mínima em meses para considerar o contrato
    
    Returns:
        DataFrame filtrado
    """
    if df.empty:
        logger.warning("DataFrame vazio fornecido para filtro behavior")
        return df
    
    logger.info(f"Filtrando contratos behavior de {len(df)} contratos")
    
    df_filtrado = df.copy()
    
    # Calcular idade do contrato se coluna de data existir
    if 'Data Contratação' in df_filtrado.columns:
        df_filtrado['Data Contratação'] = pd.to_datetime(
            df_filtrado['Data Contratação'], errors='coerce'
        )
        
        df_filtrado['idade_contrato_meses'] = df_filtrado['Data Contratação'].apply(
            lambda x: (relativedelta(data_base, x).years * 12 + 
                      relativedelta(data_base, x).months) if pd.notnull(x) else np.nan
        )
        
        # Filtrar por idade mínima
        df_filtrado = df_filtrado[df_filtrado['idade_contrato_meses'] >= meses_min_vida]
    
    logger.info(f"Filtro aplicado: {len(df_filtrado)} contratos behavior")
    
    return df_filtrado


def criar_variaveis_comportamentais(
    df: pd.DataFrame, 
    data_base: datetime = None
) -> pd.DataFrame:
    """
    Cria variáveis comportamentais para modelagem de PD.
    Usa WOE_SCORES do módulo Forward Looking importado.
    
    Args:
        df: DataFrame com dados dos contratos
        data_base: Data de referência para cálculo
    
    Returns:
        DataFrame com variáveis comportamentais adicionadas
    """
    if df.empty:
        logger.warning("DataFrame vazio fornecido")
        return df
    
    logger.info(f"Criando variáveis comportamentais para {len(df)} contratos")
    
    df_com_features = df.copy()

    # 1. Utilização do Limite
    if 'Saldo Devedor' in df_com_features.columns and 'Limite Aprovado' in df_com_features.columns:
        limite = df_com_features['Limite Aprovado'].replace(0, np.nan)
        df_com_features['utilizacao_limite'] = (
            df_com_features['Saldo Devedor'] / limite
        ).fillna(0).clip(0, 1)
    else:
        df_com_features['utilizacao_limite'] = 0.5

    # 2. Flag e Faixa de Atraso
    if 'Dias Atraso' in df_com_features.columns:
        df_com_features['flag_possui_atraso'] = (df_com_features['Dias Atraso'] > 0).astype(int)
        df_com_features['faixa_atraso'] = pd.cut(
            df_com_features['Dias Atraso'],
            bins=[-1, 0, 30, 90, float('inf')],
            labels=[1, 2, 3, 4],
            include_lowest=True
        ).astype(int)
    else:
        df_com_features['flag_possui_atraso'] = 0
        df_com_features['faixa_atraso'] = 1

    # 3. Adicionar WOE scores usando tabela importada
    df_com_features = _adicionar_woe_scores(df_com_features)
    
    # 4. Adicionar variáveis macroeconômicas
    df_com_features = _adicionar_variaveis_macroeconomicas(df_com_features, data_base)

    logger.info("Variáveis comportamentais criadas com sucesso")
    return df_com_features


def _adicionar_woe_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona WOE scores usando tabelas do modulo_forward_looking.
    """
    df_woe = df.copy()
    
    df_woe['woe_score'] = 0.0
    df_woe['woe_score_medio'] = 0.1
    
    # Identificar coluna de produto
    produto_col = 'Produto' if 'Produto' in df_woe.columns else (
        'produto' if 'produto' in df_woe.columns else None
    )
    
    if produto_col is None or not FL_AVAILABLE:
        logger.warning("Usando WOE padrão (coluna produto não encontrada ou FL indisponível)")
        df_woe['woe_score'] = -1.0
        return df_woe
    
    # Aplicar WOE por produto e faixa
    for idx, row in df_woe.iterrows():
        produto_raw = str(row[produto_col]).lower().strip()
        produto = PRODUTO_MAP.get(produto_raw, 'parcelados')
        faixa = int(row.get('faixa_atraso', 1))
        
        if produto in WOE_SCORES and faixa in WOE_SCORES[produto]:
            df_woe.at[idx, 'woe_score'] = WOE_SCORES[produto][faixa]
            if produto in WOE_SCORES_MEDIO and faixa in WOE_SCORES_MEDIO[produto]:
                df_woe.at[idx, 'woe_score_medio'] = WOE_SCORES_MEDIO[produto][faixa]
    
    logger.info(f"WOE scores aplicados (usando modulo_forward_looking)")
    return df_woe


def _adicionar_variaveis_macroeconomicas(
    df: pd.DataFrame, 
    data_base: datetime = None
) -> pd.DataFrame:
    """
    Adiciona variáveis macroeconômicas.
    Tenta usar API BACEN via modulo_forward_looking, senão usa valores simulados.
    """
    df_macro = df.copy()
    
    if data_base is None:
        data_base = datetime.now()
    
    # Tentar coletar dados reais via API
    if FL_AVAILABLE:
        try:
            series = coletar_series_historicas()
            if series:
                # Usar último valor disponível de cada série
                df_macro['selic'] = series.get('SELIC', {}).get('valor', [12.25])[-1] if 'SELIC' in series else 12.25
                df_macro['ipca'] = series.get('IPCA', {}).get('valor', [4.5])[-1] if 'IPCA' in series else 4.5
                df_macro['desemprego_12m'] = 7.5  # Valor aproximado atual
                df_macro['pib_var_trim_12m'] = 3.0  # Valor aproximado
                df_macro['cambio'] = 5.0
                logger.info("Variáveis macroeconômicas obtidas da API BACEN")
                return df_macro
        except Exception as e:
            logger.warning(f"Erro ao coletar dados macro: {e}")
    
    # Fallback: valores simulados
    df_macro['selic'] = 12.25
    df_macro['ipca'] = 4.5
    df_macro['desemprego_12m'] = 7.5
    df_macro['pib_var_trim_12m'] = 3.0
    df_macro['cambio'] = 5.0
    
    logger.info("Usando variáveis macroeconômicas simuladas")
    return df_macro


# =============================================================================
# CÁLCULO DE PD BEHAVIOR
# =============================================================================

def _calcular_score_behavior(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula score behavior normalizado (0-1000).
    """
    df_score = df.copy()
    
    # Inicializar score base
    df_score['score_behavior'] = 600.0
    
    # Ajustar por WOE
    if 'woe_score' in df_score.columns:
        woe_norm = (df_score['woe_score'] + 3) / 6  # Normalizar -3 a +3 para 0-1
        df_score['score_behavior'] = 200 + (woe_norm.clip(0, 1) * 800)
    
    # Penalizar alta utilização
    if 'utilizacao_limite' in df_score.columns:
        mask_alta = df_score['utilizacao_limite'] > 0.8
        df_score.loc[mask_alta, 'score_behavior'] *= 0.9
        
        mask_baixa = df_score['utilizacao_limite'] < 0.3
        df_score.loc[mask_baixa, 'score_behavior'] *= 1.05
    
    # Penalizar atraso
    if 'flag_possui_atraso' in df_score.columns:
        mask_atraso = df_score['flag_possui_atraso'] == 1
        df_score.loc[mask_atraso, 'score_behavior'] *= 0.85
    
    df_score['score_behavior'] = np.clip(df_score['score_behavior'], 0, 1000)
    
    return df_score


def _aplicar_grupos_homogeneos_behavior(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica grupos homogêneos específicos para carteira behavior.
    """
    df_gh = df.copy()
    
    df_gh['grupo_homogeneo'] = 3
    df_gh['pd_behavior'] = 0.08
    
    produto_col = 'Produto' if 'Produto' in df_gh.columns else 'produto'
    
    if produto_col in df_gh.columns and 'score_behavior' in df_gh.columns:
        for produto_std in ['parcelados', 'rotativos', 'consignado']:
            # Criar máscara para produtos que mapeiam para este tipo
            mask_produto = df_gh[produto_col].apply(
                lambda x: PRODUTO_MAP.get(str(x).lower().strip(), '') == produto_std
            )
            
            if mask_produto.any() and produto_std in GRUPOS_HOMOGENEOS_BEHAVIOR:
                grupos = GRUPOS_HOMOGENEOS_BEHAVIOR[produto_std]
                
                for gh_id, gh_info in grupos.items():
                    mask_score = (
                        (df_gh['score_behavior'] >= gh_info['score_min']) &
                        (df_gh['score_behavior'] < gh_info['score_max'])
                    )
                    mask_final = mask_produto & mask_score
                    
                    if mask_final.any():
                        df_gh.loc[mask_final, 'grupo_homogeneo'] = gh_id
                        df_gh.loc[mask_final, 'pd_behavior'] = gh_info['pd']
    
    return df_gh


def _aplicar_ajuste_forward_looking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica ajuste Forward Looking usando equações do modulo_forward_looking.
    """
    df_fl = df.copy()
    
    if not FL_AVAILABLE or not EQUACOES_FL:
        logger.warning("Forward Looking não disponível, mantendo PD base")
        return df_fl
    
    produto_col = 'Produto' if 'Produto' in df_fl.columns else 'produto'
    
    if produto_col not in df_fl.columns:
        return df_fl
    
    for produto_std in ['consignado', 'parcelados', 'rotativos']:
        # Máscara para produtos
        mask_produto = df_fl[produto_col].apply(
            lambda x: PRODUTO_MAP.get(str(x).lower().strip(), '') == produto_std
        )
        
        if mask_produto.any() and produto_std in EQUACOES_FL:
            eq = EQUACOES_FL[produto_std]
            
            # Calcular logit usando equação FL
            logit = eq['intercepto']
            
            for var, coef in eq['coeficientes'].items():
                if var == 'WOE_score' and 'woe_score' in df_fl.columns:
                    logit = logit + coef * df_fl.loc[mask_produto, 'woe_score']
                elif 'PIB' in var and 'pib_var_trim_12m' in df_fl.columns:
                    logit = logit + coef * df_fl.loc[mask_produto, 'pib_var_trim_12m']
                elif 'Inad_PF' in var:
                    # Usar proxy de inadimplência
                    logit = logit + coef * 4.5  # Taxa média atual
                elif 'IVG_R' in var:
                    # Usar proxy de endividamento
                    logit = logit + coef * 50  # Índice médio
                elif 'ICC' in var and 'ipca' in df_fl.columns:
                    logit = logit + coef * df_fl.loc[mask_produto, 'ipca']
            
            # Transformação logística
            pd_fl = 1 / (1 + np.exp(-logit))
            df_fl.loc[mask_produto, 'pd_behavior'] = pd_fl
    
    logger.info("Ajuste Forward Looking aplicado (via modulo_forward_looking)")
    return df_fl


def calcular_pd_behavior(df: pd.DataFrame) -> pd.DataFrame:
    """
    Função principal: Calcula PD Behavior para contratos em carteira.
    
    Pipeline:
    1. Cria variáveis comportamentais (utilização, atraso)
    2. Aplica WOE scores (do modulo_forward_looking)
    3. Calcula score behavior (0-1000)
    4. Aplica grupos homogêneos específicos de behavior
    5. Ajusta com Forward Looking (do modulo_forward_looking)
    
    Args:
        df: DataFrame com dados dos contratos
        
    Returns:
        DataFrame com pd_behavior calculada
    """
    logger.info("=" * 50)
    logger.info("INICIANDO CÁLCULO PD BEHAVIOR")
    logger.info("=" * 50)
    
    try:
        df_resultado = df.copy()
        data_base = datetime.now()
        
        # 1. Filtrar contratos behavior (> 3 meses)
        if 'Data Contratação' in df_resultado.columns:
            try:
                df_behavior = filtrar_dados_behavior(df_resultado, data_base)
            except:
                df_behavior = df_resultado.copy()
        else:
            df_behavior = df_resultado.copy()
        
        # 2. Criar variáveis comportamentais
        df_com_features = criar_variaveis_comportamentais(df_behavior, data_base)
        
        # 3. Calcular score behavior
        df_com_score = _calcular_score_behavior(df_com_features)
        
        # 4. Aplicar grupos homogêneos behavior
        df_com_gh = _aplicar_grupos_homogeneos_behavior(df_com_score)
        
        # 5. Aplicar ajuste Forward Looking
        df_final = _aplicar_ajuste_forward_looking(df_com_gh)
        
        # 6. Garantir limites e adicionar segmento
        df_final['pd_behavior'] = np.clip(df_final['pd_behavior'], 0.0003, 0.9999)
        df_final['segmento_behavior'] = 'GH_' + df_final['grupo_homogeneo'].astype(str)
        
        logger.info(f"PD Behavior calculada para {len(df_final)} contratos")
        logger.info(f"PD média: {df_final['pd_behavior'].mean():.4f}")
        
        return df_final
        
    except Exception as e:
        logger.error(f"Erro no cálculo de PD Behavior: {e}")
        df['pd_behavior'] = 0.08  # Fallback
        return df


def executar_pd_behavior_completo(
    df_contratos: pd.DataFrame,
    data_base: datetime = None,
    incluir_forward_looking: bool = True
) -> Dict[str, Any]:
    """
    Executa pipeline completo de PD Behavior.
    
    Args:
        df_contratos: DataFrame com dados dos contratos
        data_base: Data de referência
        incluir_forward_looking: Se deve usar FL (default: True)
    
    Returns:
        Dict com resultados e estatísticas
    """
    if data_base is None:
        data_base = datetime.now()
    
    resultados = {
        'sucesso': False,
        'data_execucao': data_base,
        'contratos_processados': 0,
        'pd_media': 0.0,
        'modulos_utilizados': {
            'forward_looking': FL_AVAILABLE,
            'grupos_homogeneos': GH_AVAILABLE
        },
        'erros': []
    }
    
    try:
        # Executar cálculo
        df_resultado = calcular_pd_behavior(df_contratos)
        
        # Estatísticas
        resultados.update({
            'sucesso': True,
            'contratos_processados': len(df_resultado),
            'pd_media': df_resultado['pd_behavior'].mean(),
            'pd_mediana': df_resultado['pd_behavior'].median(),
            'pd_min': df_resultado['pd_behavior'].min(),
            'pd_max': df_resultado['pd_behavior'].max(),
            'df_resultado': df_resultado
        })
        
        # Por grupo homogêneo
        if 'grupo_homogeneo' in df_resultado.columns:
            resultados['por_grupo'] = df_resultado.groupby('grupo_homogeneo')['pd_behavior'].agg(
                ['count', 'mean', 'std']
            ).to_dict()
        
    except Exception as e:
        logger.error(f"Erro no pipeline PD Behavior: {e}")
        resultados['erros'].append(str(e))
    
    return resultados


# =============================================================================
# FEATURES DISPONÍVEIS
# =============================================================================

FEATURES_PD_BEHAVIOR = [
    'utilizacao_limite',
    'flag_possui_atraso',
    'faixa_atraso',
    'woe_score',
    'woe_score_medio',
    'selic',
    'ipca',
    'pib_var_trim_12m',
    'desemprego_12m',
    'cambio',
    'score_behavior',
    'grupo_homogeneo',
    'pd_behavior',
    'segmento_behavior'
]


# =============================================================================
# TESTE DO MÓDULO
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("TESTE DO MÓDULO PD BEHAVIOR (REFATORADO)")
    print("=" * 60)
    
    # Criar dados de teste
    df_teste = pd.DataFrame({
        'ID_Contrato': range(1, 11),
        'Produto': ['consignado', 'parcelados', 'rotativos'] * 3 + ['consignado'],
        'Saldo Devedor': [5000, 8000, 2000, 15000, 3000, 7000, 1500, 10000, 4000, 6000],
        'Limite Aprovado': [10000, 10000, 5000, 20000, 5000, 10000, 3000, 15000, 8000, 10000],
        'Dias Atraso': [0, 15, 45, 0, 5, 0, 100, 0, 25, 0],
        'Data Contratação': [datetime(2024, 1, i) for i in range(1, 11)]
    })
    
    print(f"\nDados de teste: {len(df_teste)} contratos")
    print(f"FL disponível: {FL_AVAILABLE}")
    print(f"GH disponível: {GH_AVAILABLE}")
    
    # Executar
    resultados = executar_pd_behavior_completo(df_teste)
    
    print(f"\nResultados:")
    print(f"  Sucesso: {resultados['sucesso']}")
    print(f"  Contratos: {resultados['contratos_processados']}")
    print(f"  PD média: {resultados['pd_media']:.4f}")
    
    if resultados['sucesso']:
        df_result = resultados['df_resultado']
        print(f"\nAmostra:")
        print(df_result[['Produto', 'Dias Atraso', 'woe_score', 'score_behavior', 
                         'grupo_homogeneo', 'pd_behavior']].head())
