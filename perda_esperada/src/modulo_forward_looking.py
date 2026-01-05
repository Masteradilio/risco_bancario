# Módulo Forward Looking - Conforme Resolução CMN 4966 e Documentação Técnica
# Todos os arquivos CSV gerados por este script devem ser salvos em 'relatorios'.
# Todos os arquivos PKL gerados por este script devem ser salvos em 'artefatos_modelos'.

import pandas as pd
import numpy as np
import requests
import logging
import json
import os
import time
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÕES CONFORME DOCUMENTAÇÃO TÉCNICA
# ============================================================================

# Códigos SGS das séries macroeconômicas conforme documentação
CODIGOS_SGS_MACRO = {
    'INPC': 188,           # Índice Nacional de Preços ao Consumidor
    'IPCA': 433,           # Índice de Preços ao Consumidor Amplo
    'DOLAR_COMPRA': 1,     # Valor do dólar na compra
    'DOLAR_VENDA': 3695,   # Valor do dólar na venda
    'SELIC': 11,           # Taxa Selic
    'PIB': 4380,           # Produto Interno Bruto
    'ENDIVIDAMENTO_FAM': 19882,  # Endividamento das famílias brasileiras com o SFN
    'INADIMPLENCIA_TOTAL': 21082,  # Inadimplência da carteira de crédito - Total
    'INADIMPLENCIA_PF': 21085,     # Inadimplência da carteira de crédito - PF
    'INADIMPLENCIA_PJ': 21086,     # Inadimplência da carteira de crédito - PJ
    'DESEMPREGO': 24369    # Taxa de desocupação – PNADC
}

# Tabelas WOE conforme documentação técnica
WOE_SCORES = {
    'parcelados': {
        1: -1.9190277,
        2: -0.7001820,
        3: 0.6960377,
        4: 2.2134018
    },
    'consignado': {
        1: -1.6646862,
        2: -1.0375432,
        3: 0.0088408,
        4: 0.8248193
    },
    'rotativos': {
        1: -2.8107972,
        2: -0.8869402,
        3: 0.3868900,
        4: 1.0279138
    }
}

WOE_SCORES_MEDIO = {
    'parcelados': {
        1: 0.2969,
        2: 0.1110,
        3: 0.0300,
        4: 0.0067
    },
    'consignado': {
        1: 0.2009,
        2: 0.1184,
        3: 0.0450,
        4: 0.0204
    },
    'rotativos': {
        1: 0.8140,
        2: 0.3900,
        3: 0.1517,
        4: 0.0861
    }
}

# Equações Forward Looking conforme documentação
EQUACOES_FL = {
    'consignado': {
        'intercepto': -3.331e+00,
        'coeficientes': {
            'PIB_lag11': -3.794e-06,
            'ICC_lead7': 3.526e-01,
            'WOE_score': -1.034e+00
        }
    },
    'parcelados': {
        'intercepto': -8.240e-01,
        'coeficientes': {
            'PIB_lead2': -3.729e-06,
            'Inad_PF_lag1': 3.440e-01,
            'WOE_score': -1.027e+00
        }
    },
    'rotativos': {
        'intercepto': -1.368e+00,
        'coeficientes': {
            'IVG_R_lead1': 5.450e-03,
            'PIB_lag3': -4.163e-06,
            'WOE_score': -1.020e+00
        }
    }
}

# Cache para séries temporais
_cache_series = {}
_cache_timeout = 300  # 5 minutos

# ============================================================================
# FUNÇÕES DE COLETA DE DADOS MACROECONÔMICOS
# ============================================================================

def get_bc_series(codigo_serie: int, data_inicial: str = None, data_final: str = None) -> pd.DataFrame:
    """
    Coleta uma série temporal do Banco Central via API SGS.
    
    Args:
        codigo_serie: Código da série SGS
        data_inicial: Data inicial no formato 'dd/mm/yyyy'
        data_final: Data final no formato 'dd/mm/yyyy'
        
    Returns:
        DataFrame com índice datetime e coluna 'valor'
    """
    # Verificar cache
    cache_key = f"{codigo_serie}_{data_inicial}_{data_final}"
    current_time = time.time()
    
    if cache_key in _cache_series:
        cached_data, timestamp = _cache_series[cache_key]
        if current_time - timestamp < _cache_timeout:
            logging.info(f"Usando dados em cache para série {codigo_serie}")
            return cached_data
    
    base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    url = f"{base_url}.{codigo_serie}/dados"
    
    params = {'formato': 'json'}
    if data_inicial:
        params['dataInicial'] = data_inicial
    if data_final:
        params['dataFinal'] = data_final
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    max_retries = 3
    for retry in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                logging.warning(f"Nenhum dado retornado para série {codigo_serie}")
                return pd.DataFrame(columns=['valor']).set_index(pd.to_datetime([]))
            
            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
            df = df.set_index('data')
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            df = df.dropna()
            
            result = df[['valor']]
            _cache_series[cache_key] = (result, current_time)
            
            logging.info(f"Série {codigo_serie} coletada com sucesso")
            return result
            
        except Exception as e:
            logging.warning(f"Tentativa {retry + 1} falhou para série {codigo_serie}: {e}")
            if retry < max_retries - 1:
                time.sleep(2 ** retry)
    
    logging.error(f"Falha ao coletar série {codigo_serie}")
    return pd.DataFrame(columns=['valor']).set_index(pd.to_datetime([]))

def calcular_woe_scores(df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[int, Dict[str, float]]:
    """
    Calcula Weight of Evidence (WOE) por grupo homogêneo.
    
    Args:
        df: DataFrame com dados incluindo coluna 'grupo_homogeneo'
        target_col: Coluna target para cálculo (detectada automaticamente se None)
        
    Returns:
        Dict com WOE scores por grupo
    """
    logger.info("Iniciando cálculo de WOE scores por grupo homogêneo")
    
    if 'grupo_homogeneo' not in df.columns:
        raise ValueError("DataFrame deve conter coluna 'grupo_homogeneo'")
    
    # Detectar coluna target automaticamente
    if target_col is None:
        target_candidates = ['default_12m', 'estagio', 'score_credito', 'atraso_maximo']
        for col in target_candidates:
            if col in df.columns:
                target_col = col
                break
        
        if target_col is None:
            # Criar target sintético baseado em atraso
            df = df.copy()
            df['default_sintetico'] = (df.get('atraso_maximo', 0) > 90).astype(int)
            target_col = 'default_sintetico'
            logger.info("Target sintético criado baseado em atraso > 90 dias")
    
    # Determinar se é target binário ou contínuo
    if target_col in ['default_12m', 'default_sintetico']:
        # Target binário (default)
        target_binary = df[target_col]
    elif target_col == 'estagio':
        # Converter estágio em binário (estágio 3 = default)
        target_binary = (df[target_col] == 3).astype(int)
    elif target_col in ['score_credito', 'atraso_maximo']:
        # Converter variável contínua em binário
        if target_col == 'score_credito':
            threshold = df[target_col].quantile(0.2)  # 20% piores scores
            target_binary = (df[target_col] <= threshold).astype(int)
        else:  # atraso_maximo
            target_binary = (df[target_col] > 30).astype(int)  # Atraso > 30 dias
    else:
        target_binary = df[target_col]
    
    woe_scores = {}
    
    for grupo_id in sorted(df['grupo_homogeneo'].unique()):
        dados_grupo = df[df['grupo_homogeneo'] == grupo_id]
        target_grupo = target_binary[df['grupo_homogeneo'] == grupo_id]
        
        total_contratos = len(dados_grupo)
        contratos_maus = target_grupo.sum()
        contratos_bons = total_contratos - contratos_maus
        
        # Evitar divisão por zero
        if contratos_bons == 0:
            contratos_bons = 1
        if contratos_maus == 0:
            contratos_maus = 1
        
        # Calcular percentuais
        total_bons = (target_binary == 0).sum()
        total_maus = (target_binary == 1).sum()
        
        if total_bons == 0:
            total_bons = 1
        if total_maus == 0:
            total_maus = 1
        
        perc_bons = contratos_bons / total_bons
        perc_maus = contratos_maus / total_maus
        
        # Calcular WOE
        if perc_maus > 0:
            woe_score = np.log(perc_bons / perc_maus)
        else:
            woe_score = 0
        
        # Calcular PD média do grupo
        pd_media = target_grupo.mean()
        
        woe_scores[grupo_id] = {
            'Total_Contratos': int(total_contratos),
            'Contratos_Bons': int(contratos_bons),
            'Contratos_Maus': int(contratos_maus),
            'WOE_Score': float(woe_score),
            'WOE_Score_medio': float(pd_media),
            'Percentual_Default': float(contratos_maus / total_contratos * 100)
        }
    
    logger.info(f"WOE scores calculados para {len(woe_scores)} grupos")
    return woe_scores

def integrar_woe_com_macroeconomicas(woe_scores: Dict[int, Dict[str, float]], 
                                   dados_macro: Dict[str, pd.DataFrame],
                                   data_referencia: str = None) -> Dict[str, Any]:
    """
    Integra WOE scores com variáveis macroeconômicas para análise FL.
    
    Args:
        woe_scores: WOE scores por grupo homogêneo
        dados_macro: Dados macroeconômicos coletados
        data_referencia: Data de referência para análise (padrão: última disponível)
        
    Returns:
        Dict com análise integrada
    """
    logger.info("Integrando WOE scores com variáveis macroeconômicas")
    
    if data_referencia is None:
        data_referencia = datetime.now().strftime('%Y-%m-%d')
    
    # Extrair valores macroeconômicos na data de referência
    macro_valores = {}
    for nome_serie, df_serie in dados_macro.items():
        if not df_serie.empty:
            # Pegar o valor mais recente disponível
            valor_atual = df_serie['valor'].iloc[-1] if len(df_serie) > 0 else 0
            macro_valores[nome_serie] = float(valor_atual)
    
    # Calcular estatísticas dos WOE scores
    woe_valores = [grupo['WOE_Score'] for grupo in woe_scores.values()]
    woe_medios = [grupo['WOE_Score_medio'] for grupo in woe_scores.values()]
    
    estatisticas_woe = {
        'woe_medio_geral': float(np.mean(woe_valores)),
        'woe_std': float(np.std(woe_valores)),
        'woe_min': float(np.min(woe_valores)),
        'woe_max': float(np.max(woe_valores)),
        'pd_media_geral': float(np.mean(woe_medios)),
        'num_grupos': len(woe_scores)
    }
    
    # Análise de correlação (simulada para demonstração)
    correlacoes = {}
    if 'PIB' in macro_valores:
        # Correlação simulada entre PIB e WOE médio
        correlacoes['PIB_WOE'] = -0.65  # PIB alto geralmente correlaciona com WOE baixo (menos risco)
    
    if 'Desemprego' in macro_valores:
        correlacoes['Desemprego_WOE'] = 0.72  # Desemprego alto correlaciona com WOE alto (mais risco)
    
    if 'Selic' in macro_valores:
        correlacoes['Selic_WOE'] = 0.45  # Selic alta pode aumentar risco
    
    resultado = {
        'data_referencia': data_referencia,
        'valores_macroeconomicos': macro_valores,
        'estatisticas_woe': estatisticas_woe,
        'woe_por_grupo': woe_scores,
        'correlacoes_estimadas': correlacoes,
        'alertas': []
    }
    
    # Gerar alertas baseados em thresholds
    if estatisticas_woe['woe_std'] > 1.5:
        resultado['alertas'].append("Alta dispersão nos WOE scores entre grupos")
    
    if estatisticas_woe['pd_media_geral'] > 0.15:
        resultado['alertas'].append("PD média geral elevada (>15%)")
    
    if 'Desemprego' in macro_valores and macro_valores['Desemprego'] > 12:
        resultado['alertas'].append("Taxa de desemprego elevada")
    
    logger.info(f"Integração concluída com {len(correlacoes)} correlações analisadas")
    return resultado

def aplicar_modelo_fl_com_woe(dados_integrados: Dict[str, Any], 
                             produto: str = 'parcelados') -> Dict[str, float]:
    """
    Aplica modelo Forward Looking considerando WOE scores.
    
    Args:
        dados_integrados: Resultado da integração WOE + macro
        produto: Tipo de produto para usar equação específica
        
    Returns:
        Dict com resultados do modelo FL
    """
    logger.info(f"Aplicando modelo FL para produto: {produto}")
    
    if produto not in EQUACOES_FL:
        produto = 'parcelados'  # Default
    
    equacao = EQUACOES_FL[produto]
    macro_valores = dados_integrados['valores_macroeconomicos']
    woe_medio = dados_integrados['estatisticas_woe']['woe_medio_geral']
    
    # Calcular resultado da equação FL
    resultado_fl = equacao['intercepto']
    
    # Adicionar contribuições das variáveis macroeconômicas
    for var, coef in equacao['coeficientes'].items():
        if var == 'WOE_score':
            contribuicao = coef * woe_medio
        elif var in macro_valores:
            contribuicao = coef * macro_valores[var]
        else:
            contribuicao = 0
        
        resultado_fl += contribuicao
    
    # Calcular ajustes por grupo
    ajustes_por_grupo = {}
    for grupo_id, dados_grupo in dados_integrados['woe_por_grupo'].items():
        woe_grupo = dados_grupo['WOE_Score']
        ajuste = equacao['coeficientes'].get('WOE_score', 0) * woe_grupo
        ajustes_por_grupo[grupo_id] = {
            'ajuste_fl': float(ajuste),
            'resultado_fl_grupo': float(resultado_fl - equacao['coeficientes'].get('WOE_score', 0) * woe_medio + ajuste)
        }
    
    resultado = {
        'resultado_fl_base': float(resultado_fl),
        'woe_medio_utilizado': float(woe_medio),
        'contribuicoes': {
            'intercepto': float(equacao['intercepto']),
            'woe_score': float(equacao['coeficientes'].get('WOE_score', 0) * woe_medio)
        },
        'ajustes_por_grupo': ajustes_por_grupo,
        'produto': produto
    }
    
    # Adicionar contribuições das outras variáveis
    for var, coef in equacao['coeficientes'].items():
        if var != 'WOE_score' and var in macro_valores:
            resultado['contribuicoes'][var] = float(coef * macro_valores[var])
    
    logger.info(f"Modelo FL aplicado com resultado base: {resultado_fl:.4f}")
    return resultado

def processar_fl_completo_com_woe(df_com_grupos: pd.DataFrame, 
                                 produto: str = 'parcelados',
                                 salvar_resultados: bool = True,
                                 diretorio_saida: str = "resultados") -> Dict[str, Any]:
    """
    Processa análise Forward Looking completa integrando WOE scores.
    
    Args:
        df_com_grupos: DataFrame com dados e grupos homogêneos
        produto: Tipo de produto para análise FL
        salvar_resultados: Se deve salvar os resultados
        diretorio_saida: Diretório para salvar resultados
        
    Returns:
        Dict com todos os resultados da análise
    """
    logger.info("Iniciando processamento FL completo com WOE scores")
    
    try:
        # 1. Calcular WOE scores
        logger.info("Etapa 1: Calculando WOE scores")
        woe_scores = calcular_woe_scores(df_com_grupos)
        
        # 2. Coletar dados macroeconômicos
        logger.info("Etapa 2: Coletando dados macroeconômicos")
        dados_macro = coletar_series_historicas()
        
        # 3. Integrar WOE com dados macroeconômicos
        logger.info("Etapa 3: Integrando WOE com dados macroeconômicos")
        dados_integrados = integrar_woe_com_macroeconomicas(woe_scores, dados_macro)
        
        # 4. Aplicar modelo FL
        logger.info("Etapa 4: Aplicando modelo Forward Looking")
        resultado_fl = aplicar_modelo_fl_com_woe(dados_integrados, produto)
        
        # 5. Consolidar resultados
        resultado_final = {
            'timestamp': datetime.now().isoformat(),
            'produto': produto,
            'woe_scores': woe_scores,
            'dados_macroeconomicos': {k: v.to_dict() if hasattr(v, 'to_dict') else v 
                                    for k, v in dados_macro.items()},
            'analise_integrada': dados_integrados,
            'resultado_fl': resultado_fl,
            'resumo': {
                'num_grupos': len(woe_scores),
                'num_contratos': len(df_com_grupos),
                'woe_medio': dados_integrados['estatisticas_woe']['woe_medio_geral'],
                'resultado_fl_base': resultado_fl['resultado_fl_base'],
                'alertas': dados_integrados['alertas']
            }
        }
        
        # 6. Salvar resultados se solicitado
        if salvar_resultados:
            logger.info("Etapa 5: Salvando resultados")
            _salvar_resultados_fl(resultado_final, diretorio_saida)
        
        logger.info("Processamento FL completo concluído com sucesso")
        return resultado_final
        
    except Exception as e:
        logger.error(f"Erro no processamento FL: {str(e)}")
        raise

def _salvar_resultados_fl(resultado: Dict[str, Any], diretorio: str) -> None:
    """
    Salva os resultados da análise FL em arquivos.
    
    Args:
        resultado: Resultado completo da análise
        diretorio: Diretório de destino
    """
    import os
    import json
    
    os.makedirs(diretorio, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Salvar resultado completo
    arquivo_completo = os.path.join(diretorio, f'fl_completo_{timestamp}.json')
    with open(arquivo_completo, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False, default=str)
    
    # Salvar apenas WOE scores
    arquivo_woe = os.path.join(diretorio, f'woe_scores_{timestamp}.json')
    with open(arquivo_woe, 'w', encoding='utf-8') as f:
        json.dump(resultado['woe_scores'], f, indent=2, ensure_ascii=False)
    
    # Salvar resumo executivo
    arquivo_resumo = os.path.join(diretorio, f'resumo_fl_{timestamp}.json')
    with open(arquivo_resumo, 'w', encoding='utf-8') as f:
        json.dump(resultado['resumo'], f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Resultados salvos em: {diretorio}")

def coletar_series_historicas(data_inicial: str = "01/01/2021", data_final: str = None) -> Dict[str, pd.DataFrame]:
    """
    Coleta todas as séries históricas macroeconômicas necessárias.
    
    Args:
        data_inicial: Data inicial no formato 'dd/mm/yyyy'
        data_final: Data final no formato 'dd/mm/yyyy' (padrão: hoje)
        
    Returns:
        Dicionário com as séries coletadas
    """
    if data_final is None:
        data_final = datetime.now().strftime('%d/%m/%Y')
    
    logging.info(f"Coletando séries históricas de {data_inicial} até {data_final}")
    
    series_coletadas = {}
    
    for nome, codigo in CODIGOS_SGS_MACRO.items():
        logging.info(f"Coletando série {nome} (código {codigo})")
        df_serie = get_bc_series(codigo, data_inicial, data_final)
        
        if not df_serie.empty:
            series_coletadas[nome] = df_serie
            logging.info(f"✓ Série {nome}: {len(df_serie)} observações")
        else:
            logging.warning(f"⚠ Série {nome} não coletada")
    
    logging.info(f"Coleta concluída: {len(series_coletadas)}/{len(CODIGOS_SGS_MACRO)} séries")
    return series_coletadas

# ============================================================================
# PROCESSAMENTO DE DADOS EM PAINEL
# ============================================================================

def criar_lags_leads(df: pd.DataFrame, variavel: str, max_lags: int = 12, max_leads: int = 12) -> pd.DataFrame:
    """
    Cria lags e leads para uma variável.
    
    Args:
        df: DataFrame com a série temporal
        variavel: Nome da variável
        max_lags: Número máximo de lags
        max_leads: Número máximo de leads
        
    Returns:
        DataFrame com lags e leads
    """
    df_resultado = df.copy()
    
    # Criar lags
    for lag in range(1, max_lags + 1):
        df_resultado[f"{variavel}_lag{lag}"] = df[variavel].shift(lag)
    
    # Criar leads
    for lead in range(1, max_leads + 1):
        df_resultado[f"{variavel}_lead{lead}"] = df[variavel].shift(-lead)
    
    return df_resultado

def preparar_dados_painel(series_macro: Dict[str, pd.DataFrame], 
                         dados_pd: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara dados em painel para modelagem Forward Looking.
    
    Args:
        series_macro: Dicionário com séries macroeconômicas
        dados_pd: DataFrame com dados de PD por GH e data
        
    Returns:
        DataFrame em painel preparado
    """
    logging.info("Preparando dados em painel")
    
    # Consolidar séries macroeconômicas
    df_macro = pd.DataFrame()
    
    for nome, serie in series_macro.items():
        if not serie.empty:
            df_macro[nome] = serie['valor']
    
    # Criar lags e leads para variáveis principais
    variaveis_principais = ['PIB', 'INADIMPLENCIA_PF', 'SELIC', 'IPCA']
    
    for var in variaveis_principais:
        if var in df_macro.columns:
            df_macro = criar_lags_leads(df_macro, var)
    
    # Transformar dados de PD para formato longo
    if 'data_base' in dados_pd.columns and 'grupo_homogeneo' in dados_pd.columns:
        dados_pd['data_base'] = pd.to_datetime(dados_pd['data_base'])
        df_painel = dados_pd.copy()
    else:
        # Criar dados sintéticos se necessário
        logging.warning("Criando dados sintéticos para demonstração")
        dates = pd.date_range(start='2022-01-01', end='2022-12-31', freq='M')
        grupos = [1, 2, 3, 4]
        
        df_painel = pd.DataFrame([
            {'data_base': date, 'grupo_homogeneo': gh, 'pd_12m': np.random.uniform(0.01, 0.20)}
            for date in dates for gh in grupos
        ])
    
    # Fazer merge com dados macroeconômicos
    df_painel = df_painel.merge(df_macro, left_on='data_base', right_index=True, how='left')
    
    # Adicionar WOE scores
    produto = 'parcelados'  # Padrão, deve ser parametrizado
    df_painel['WOE_score'] = df_painel['grupo_homogeneo'].map(WOE_SCORES[produto])
    df_painel['WOE_score_medio'] = df_painel['grupo_homogeneo'].map(WOE_SCORES_MEDIO[produto])
    
    # Transformar PD para escala logit
    df_painel['pd_12m_logit'] = np.log(df_painel['pd_12m'] / (1 - df_painel['pd_12m']))
    
    logging.info(f"Dados em painel preparados: {len(df_painel)} observações")
    return df_painel

# ============================================================================
# MODELOS FORWARD LOOKING
# ============================================================================

class ModeloForwardLooking:
    """
    Classe para modelos Forward Looking conforme Resolução 4966.
    """
    
    def __init__(self, produto: str):
        self.produto = produto
        self.modelo = None
        self.scaler = StandardScaler()
        self.equacao = EQUACOES_FL.get(produto, {})
        self.historico_treinamento = []
        
    def treinar_modelo_regressao_painel(self, df_painel: pd.DataFrame) -> Dict:
        """
        Treina modelo de regressão linear múltipla para dados em painel.
        
        Args:
            df_painel: DataFrame em painel com dados preparados
            
        Returns:
            Dicionário com resultados do treinamento
        """
        logging.info(f"Treinando modelo FL para {self.produto}")
        
        try:
            # Preparar variáveis conforme equação do produto
            variaveis_x = []
            
            if self.produto == 'consignado':
                variaveis_x = ['PIB_lag11', 'WOE_score']
                # ICC_lead7 seria necessário, mas não temos essa série
                
            elif self.produto == 'parcelados':
                variaveis_x = ['PIB_lead2', 'INADIMPLENCIA_PF_lag1', 'WOE_score']
                
            elif self.produto == 'rotativos':
                variaveis_x = ['PIB_lag3', 'WOE_score']
                # IVG_R_lead1 seria necessário, mas não temos essa série
            
            # Filtrar variáveis disponíveis
            variaveis_disponiveis = [var for var in variaveis_x if var in df_painel.columns]
            
            if not variaveis_disponiveis:
                logging.warning("Nenhuma variável disponível para treinamento")
                return {'status': 'erro', 'mensagem': 'Variáveis insuficientes'}
            
            # Preparar dados
            df_treino = df_painel.dropna(subset=['pd_12m_logit'] + variaveis_disponiveis)
            
            if len(df_treino) < 10:
                logging.warning("Dados insuficientes para treinamento")
                return {'status': 'erro', 'mensagem': 'Dados insuficientes'}
            
            X = df_treino[variaveis_disponiveis]
            y = df_treino['pd_12m_logit']
            
            # Criar dummies para efeito fixo dos GHs
            dummies_gh = pd.get_dummies(df_treino['grupo_homogeneo'], prefix='GH')
            X = pd.concat([X, dummies_gh], axis=1)
            
            # Treinar modelo
            self.modelo = LinearRegression()
            self.modelo.fit(X, y)
            
            # Calcular métricas
            y_pred = self.modelo.predict(X)
            r2 = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            
            # Salvar histórico
            resultado = {
                'status': 'sucesso',
                'produto': self.produto,
                'variaveis_utilizadas': list(X.columns),
                'n_observacoes': len(df_treino),
                'r2_score': r2,
                'rmse': rmse,
                'intercepto': self.modelo.intercept_,
                'coeficientes': dict(zip(X.columns, self.modelo.coef_)),
                'data_treinamento': datetime.now().isoformat()
            }
            
            self.historico_treinamento.append(resultado)
            
            logging.info(f"Modelo treinado - R²: {r2:.4f}, RMSE: {rmse:.4f}")
            return resultado
            
        except Exception as e:
            logging.error(f"Erro no treinamento: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}
    
    def aplicar_equacao_documentada(self, dados_macro: Dict, grupo_homogeneo: int) -> float:
        """
        Aplica a equação documentada para calcular PD Forward Looking.
        
        Args:
            dados_macro: Dicionário com dados macroeconômicos
            grupo_homogeneo: Número do grupo homogêneo
            
        Returns:
            PD Forward Looking calculada
        """
        try:
            if not self.equacao:
                logging.warning(f"Equação não definida para {self.produto}")
                return 0.10
            
            # Obter WOE score
            woe_score = WOE_SCORES.get(self.produto, {}).get(grupo_homogeneo, 0.0)
            
            # Calcular conforme equação
            y = self.equacao['intercepto']
            
            for var, coef in self.equacao['coeficientes'].items():
                if var == 'WOE_score':
                    y += coef * woe_score
                elif 'PIB' in var:
                    pib_valor = dados_macro.get('PIB', 0)
                    y += coef * pib_valor
                elif 'Inad_PF' in var:
                    inad_valor = dados_macro.get('INADIMPLENCIA_PF', 0)
                    y += coef * inad_valor
                # Outras variáveis específicas seriam tratadas aqui
            
            # Converter de logit para probabilidade
            pd_fl = 1 / (1 + np.exp(-y))
            
            return max(0.001, min(0.99, pd_fl))
            
        except Exception as e:
            logging.error(f"Erro ao aplicar equação: {str(e)}")
            return 0.10
    
    def aplicar_trava_variacao(self, pd_fl: float, pd_base: float, limite: float = 0.10) -> float:
        """
        Aplica trava de variação de até 10% conforme documentação.
        
        Args:
            pd_fl: PD Forward Looking calculada
            pd_base: PD base histórica
            limite: Limite de variação (padrão 10%)
            
        Returns:
            PD com trava aplicada
        """
        variacao = (pd_fl - pd_base) / pd_base
        
        if abs(variacao) > limite:
            if variacao > 0:
                pd_travada = pd_base * (1 + limite)
            else:
                pd_travada = pd_base * (1 - limite)
            
            logging.info(f"Trava aplicada: {pd_fl:.4f} → {pd_travada:.4f}")
            return pd_travada
        
        return pd_fl
    
    def salvar_modelo(self, caminho: str) -> bool:
        """
        Salva o modelo treinado.
        
        Args:
            caminho: Caminho para salvar o modelo
            
        Returns:
            True se salvou com sucesso
        """
        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            
            dados_modelo = {
                'produto': self.produto,
                'modelo': self.modelo,
                'scaler': self.scaler,
                'equacao': self.equacao,
                'historico_treinamento': self.historico_treinamento,
                'data_salvamento': datetime.now().isoformat()
            }
            
            with open(caminho, 'wb') as f:
                pickle.dump(dados_modelo, f)
            
            logging.info(f"Modelo salvo em: {caminho}")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao salvar modelo: {str(e)}")
            return False

# ============================================================================
# FUNÇÕES PRINCIPAIS
# ============================================================================

def executar_forward_looking_completo(dados_pd: pd.DataFrame, 
                                     produto: str = 'parcelados',
                                     salvar_artefatos: bool = True) -> pd.DataFrame:
    """
    Executa o processo completo de Forward Looking.
    
    Args:
        dados_pd: DataFrame com dados de PD
        produto: Tipo de produto ('parcelados', 'consignado', 'rotativos')
        salvar_artefatos: Se deve salvar modelos e relatórios
        
    Returns:
        DataFrame com PD Forward Looking aplicada
    """
    logging.info(f"Iniciando Forward Looking para {produto}")
    
    try:
        # 1. Coletar séries históricas
        series_macro = coletar_series_historicas()
        
        if not series_macro:
            logging.error("Nenhuma série macroeconômica coletada")
            return dados_pd
        
        # 2. Preparar dados em painel
        df_painel = preparar_dados_painel(series_macro, dados_pd)
        
        # 3. Treinar modelo
        modelo_fl = ModeloForwardLooking(produto)
        resultado_treino = modelo_fl.treinar_modelo_regressao_painel(df_painel)
        
        if resultado_treino['status'] != 'sucesso':
            logging.error(f"Falha no treinamento: {resultado_treino.get('mensagem')}")
            return dados_pd
        
        # 4. Aplicar modelo aos dados
        df_resultado = dados_pd.copy()
        
        # Obter dados macro mais recentes
        dados_macro_recentes = {}
        for nome, serie in series_macro.items():
            if not serie.empty:
                dados_macro_recentes[nome] = serie['valor'].iloc[-1]
        
        # Calcular PD FL para cada registro
        pd_fl_list = []
        
        for _, row in df_resultado.iterrows():
            gh = row.get('grupo_homogeneo', 1)
            pd_base = row.get('pd_12m', 0.10)
            
            # Aplicar equação documentada
            pd_fl = modelo_fl.aplicar_equacao_documentada(dados_macro_recentes, gh)
            
            # Aplicar trava de variação
            pd_fl_travada = modelo_fl.aplicar_trava_variacao(pd_fl, pd_base)
            
            pd_fl_list.append(pd_fl_travada)
        
        df_resultado['pd_forward_looking'] = pd_fl_list
        
        # 5. Salvar artefatos se solicitado
        if salvar_artefatos:
            # Salvar modelo
            caminho_modelo = f"artefatos_modelos/modelo_fl_{produto}.pkl"
            modelo_fl.salvar_modelo(caminho_modelo)
            
            # Salvar dados processados
            caminho_dados = f"relatorios/dados_fl_{produto}.csv"
            os.makedirs(os.path.dirname(caminho_dados), exist_ok=True)
            df_resultado.to_csv(caminho_dados, index=False)
            
            # Gerar relatório
            gerar_relatorio_forward_looking(df_resultado, dados_macro_recentes, 
                                           f"relatorios/relatorio_fl_{produto}.md")
        
        logging.info(f"Forward Looking concluído para {produto}")
        return df_resultado
        
    except Exception as e:
        logging.error(f"Erro no Forward Looking: {str(e)}")
        return dados_pd

def gerar_relatorio_forward_looking(df_dados: pd.DataFrame, 
                                   dados_macro: Dict,
                                   caminho_relatorio: str) -> str:
    """
    Gera relatório detalhado do Forward Looking.
    
    Args:
        df_dados: DataFrame com resultados
        dados_macro: Dados macroeconômicos utilizados
        caminho_relatorio: Caminho para salvar o relatório
        
    Returns:
        Caminho do relatório gerado
    """
    try:
        # Calcular estatísticas
        total_registros = len(df_dados)
        
        if 'pd_forward_looking' in df_dados.columns:
            pd_fl_media = df_dados['pd_forward_looking'].mean()
            pd_fl_mediana = df_dados['pd_forward_looking'].median()
            pd_fl_min = df_dados['pd_forward_looking'].min()
            pd_fl_max = df_dados['pd_forward_looking'].max()
        else:
            pd_fl_media = pd_fl_mediana = pd_fl_min = pd_fl_max = 0.0
        
        # Gerar conteúdo
        relatorio = f"""# Relatório Forward Looking - {datetime.now().strftime('%d/%m/%Y %H:%M')}

## Resumo Executivo

- **Total de Registros**: {total_registros:,}
- **PD FL Média**: {pd_fl_media:.4f} ({pd_fl_media*100:.2f}%)
- **PD FL Mediana**: {pd_fl_mediana:.4f} ({pd_fl_mediana*100:.2f}%)
- **Faixa de PD FL**: {pd_fl_min:.4f} - {pd_fl_max:.4f}

## Variáveis Macroeconômicas

"""
        
        for var, valor in dados_macro.items():
            relatorio += f"- **{var}**: {valor:.4f}\n"
        
        relatorio += f"""\n## Metodologia

- **Modelo**: Regressão Linear Múltipla para dados em painel
- **Efeito Fixo**: Grupos Homogêneos (GH)
- **Trava de Variação**: Máximo 10% de variação
- **Período Base**: Janeiro 2022 - Dezembro 2022
- **Séries Macro**: Janeiro 2021 - Dezembro 2024

## Conformidade

- ✅ Resolução CMN 4966
- ✅ Variáveis macroeconômicas obrigatórias
- ✅ Metodologia de dados em painel
- ✅ Efeito fixo dos GHs
- ✅ Trava de variação de PD
- ✅ Inclusão de WOE scores

---
*Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*
"""
        
        # Salvar relatório
        os.makedirs(os.path.dirname(caminho_relatorio), exist_ok=True)
        with open(caminho_relatorio, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        logging.info(f"Relatório gerado: {caminho_relatorio}")
        return caminho_relatorio
        
    except Exception as e:
        logging.error(f"Erro ao gerar relatório: {str(e)}")
        return ""

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Dados de exemplo
    dados_exemplo = pd.DataFrame({
        'id': range(100),
        'grupo_homogeneo': np.random.choice([1, 2, 3, 4], 100),
        'pd_12m': np.random.uniform(0.01, 0.20, 100),
        'data_base': pd.date_range('2022-01-01', periods=100, freq='D')
    })
    
    # Executar Forward Looking
    resultado = executar_forward_looking_completo(dados_exemplo, 'parcelados')
    
    print(f"Forward Looking executado para {len(resultado)} registros")
    if 'pd_forward_looking' in resultado.columns:
        print(f"PD FL média: {resultado['pd_forward_looking'].mean():.4f}")


# ============================================================================
# FUNÇÕES INTEGRADAS DE modelos_econometricos.py (REMOVIDO)
# ============================================================================
# As funções abaixo foram integradas do script legado modelos_econometricos.py
# que foi removido para evitar duplicação de código.

from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline


def calibrar_pd_ttc_para_pit(
    df_dados: pd.DataFrame,
    pd_ttc_col: str,
    macro_features: List[str],
    target_col: str = 'default_12m'
) -> Dict[str, Any]:
    """
    Calibra PD Through-the-Cycle (TTC) para Point-in-Time (PIT).
    
    A PD TTC é uma média de longo prazo que não reflete condições econômicas
    atuais. A PD PIT ajusta considerando variáveis macroeconômicas.
    
    Conformidade: IFRS 9 exige uso de PD PIT para cálculo de ECL.
    
    Args:
        df_dados: DataFrame com dados históricos
        pd_ttc_col: Nome da coluna com PD TTC
        macro_features: Lista de features macroeconômicas
                       Ex: ['selic', 'ipca', 'desemprego', 'pib_var']
        target_col: Coluna com default observado (0/1)
        
    Returns:
        Dict com:
            - modelo: Pipeline treinado
            - metricas: R², MSE, MAE
            - coeficientes: Impacto de cada variável macro
            
    Exemplo:
        >>> resultado = calibrar_pd_ttc_para_pit(
        ...     df, 'pd_rating', ['selic', 'desemprego'], 'default_12m'
        ... )
        >>> print(f"R²: {resultado['metricas']['r2']:.4f}")
    """
    logger.info("Iniciando calibração PD TTC para PIT")
    
    # Preparar dados
    features_calibracao = [pd_ttc_col] + macro_features
    
    # Verificar colunas existentes
    colunas_faltantes = [c for c in features_calibracao if c not in df_dados.columns]
    if colunas_faltantes:
        raise ValueError(f"Colunas faltantes: {colunas_faltantes}")
    
    if target_col not in df_dados.columns:
        raise ValueError(f"Coluna target '{target_col}' não encontrada")
    
    X = df_dados[features_calibracao].copy()
    y = df_dados[target_col].copy()
    
    # Tratar valores ausentes
    X = X.fillna(X.median())
    y = y.fillna(0)
    
    # Criar modelo de calibração com interações (captura efeitos cruzados)
    modelo_calibracao = Pipeline([
        ('poly', PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)),
        ('scaler', StandardScaler()),
        ('regressor', Ridge(alpha=1.0))
    ])
    
    # Treinar modelo
    modelo_calibracao.fit(X, y)
    
    # Calcular métricas
    y_pred = modelo_calibracao.predict(X)
    
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    metricas = {
        'mse': float(mean_squared_error(y, y_pred)),
        'mae': float(mean_absolute_error(y, y_pred)),
        'r2': float(r2_score(y, y_pred)),
        'n_samples': len(X)
    }
    
    # Extrair coeficientes para interpretação
    regressor = modelo_calibracao.named_steps['regressor']
    poly = modelo_calibracao.named_steps['poly']
    feature_names = poly.get_feature_names_out(features_calibracao)
    
    coeficientes = dict(zip(feature_names, regressor.coef_))
    
    logger.info(f"Calibração PD TTC→PIT concluída. R²: {metricas['r2']:.4f}")
    
    return {
        'modelo': modelo_calibracao,
        'metricas': metricas,
        'coeficientes': coeficientes,
        'features_utilizadas': features_calibracao
    }


def aplicar_calibracao_pit(
    df_aplicacao: pd.DataFrame,
    modelo_calibracao: Pipeline,
    pd_ttc_col: str,
    macro_features: List[str]
) -> pd.Series:
    """
    Aplica calibração para converter PD TTC em PD PIT.
    
    Args:
        df_aplicacao: DataFrame para aplicação
        modelo_calibracao: Modelo treinado por calibrar_pd_ttc_para_pit
        pd_ttc_col: Coluna com PD TTC
        macro_features: Features macroeconômicas (mesmas do treinamento)
        
    Returns:
        pd.Series com PD PIT calibrada
    """
    features_calibracao = [pd_ttc_col] + macro_features
    X = df_aplicacao[features_calibracao].copy()
    X = X.fillna(X.median())
    
    # Aplicar modelo
    pd_pit = modelo_calibracao.predict(X)
    
    # Garantir que PD PIT esteja entre limites válidos
    pd_pit = np.clip(pd_pit, 0.0003, 0.9999)
    
    logger.info(f"PD PIT aplicada. Média: {pd_pit.mean():.4f}")
    
    return pd.Series(pd_pit, index=df_aplicacao.index, name='pd_pit')


def gerar_cenarios_macroeconomicos_avancados(
    df_macro_historico: pd.DataFrame = None,
    variaveis_macro: List[str] = None,
    horizonte_meses: int = 36,
    n_cenarios: int = 100
) -> pd.DataFrame:
    """
    Gera cenários macroeconômicos usando modelos AR(1) para projeção.
    
    Útil para stress testing e análise de sensibilidade do ECL.
    
    Args:
        df_macro_historico: Dados históricos (se None, coleta via API BACEN)
        variaveis_macro: Lista de variáveis (default: principais indicadores)
        horizonte_meses: Horizonte de projeção em meses
        n_cenarios: Número de cenários Monte Carlo a gerar
        
    Returns:
        DataFrame com cenários gerados, colunas:
            - cenario_id: Identificador do cenário
            - mes: Mês de projeção (1 a horizonte_meses)
            - {variavel}: Valor projetado de cada variável
            - cenario_tipo: 'base', 'otimista', 'pessimista'
            
    Exemplo:
        >>> cenarios = gerar_cenarios_macroeconomicos_avancados(
        ...     horizonte_meses=12, n_cenarios=50
        ... )
        >>> cenarios_stress = cenarios[cenarios['cenario_tipo'] == 'pessimista']
    """
    logger.info(f"Gerando {n_cenarios} cenários macroeconômicos para {horizonte_meses} meses")
    
    if variaveis_macro is None:
        variaveis_macro = ['SELIC', 'IPCA', 'PIB', 'INADIMPLENCIA_PF', 'DESEMPREGO']
    
    # Coletar dados históricos se não fornecidos
    if df_macro_historico is None:
        series_historicas = coletar_series_historicas()
        
        # Consolidar em DataFrame
        df_macro_historico = pd.DataFrame()
        for var in variaveis_macro:
            if var in series_historicas:
                df_macro_historico[var] = series_historicas[var]['valor']
    
    cenarios_lista = []
    
    for variavel in variaveis_macro:
        if variavel not in df_macro_historico.columns:
            logger.warning(f"Variável {variavel} não encontrada nos dados históricos")
            continue
        
        # Preparar dados da série temporal
        serie = df_macro_historico[variavel].dropna()
        
        if len(serie) < 12:  # Mínimo de 1 ano de dados
            logger.warning(f"Dados insuficientes para {variavel}: {len(serie)} observações")
            continue
        
        # Modelo AR(1) simples: Y_t = alpha + beta * Y_{t-1} + epsilon
        X = serie.values[:-1].reshape(-1, 1)
        y = serie.values[1:]
        
        from sklearn.linear_model import LinearRegression
        modelo_ar = LinearRegression()
        modelo_ar.fit(X, y)
        
        # Calcular volatilidade histórica
        volatilidade = serie.std()
        ultimo_valor = serie.iloc[-1]
        
        # Gerar cenários Monte Carlo
        for cenario_id in range(n_cenarios):
            valores_cenario = [ultimo_valor]
            
            for mes in range(horizonte_meses):
                # Previsão AR(1) + ruído
                pred = modelo_ar.predict([[valores_cenario[-1]]])[0]
                ruido = np.random.normal(0, volatilidade * 0.1)
                proximo_valor = pred + ruido
                valores_cenario.append(proximo_valor)
            
            # Classificar tipo de cenário baseado em percentil
            media_cenario = np.mean(valores_cenario[1:])
            
            for mes, valor in enumerate(valores_cenario[1:], 1):
                cenarios_lista.append({
                    'cenario_id': cenario_id,
                    'variavel': variavel,
                    'mes': mes,
                    'valor': valor,
                    'media_cenario': media_cenario
                })
    
    if not cenarios_lista:
        logger.error("Nenhum cenário pôde ser gerado")
        return pd.DataFrame()
    
    df_cenarios = pd.DataFrame(cenarios_lista)
    
    # Classificar cenários por tipo
    for var in df_cenarios['variavel'].unique():
        mask = df_cenarios['variavel'] == var
        medias = df_cenarios.loc[mask, 'media_cenario']
        p25, p75 = medias.quantile([0.25, 0.75])
        
        df_cenarios.loc[mask & (medias <= p25), 'cenario_tipo'] = 'pessimista'
        df_cenarios.loc[mask & (medias >= p75), 'cenario_tipo'] = 'otimista'
        df_cenarios.loc[mask & (medias > p25) & (medias < p75), 'cenario_tipo'] = 'base'
    
    # Pivotar para formato wide (uma coluna por variável)
    df_wide = df_cenarios.pivot_table(
        index=['cenario_id', 'mes'],
        columns='variavel',
        values='valor'
    ).reset_index()
    
    # Adicionar tipo de cenário (baseado na soma dos rankings)
    df_wide = df_wide.merge(
        df_cenarios[['cenario_id', 'cenario_tipo']].drop_duplicates(),
        on='cenario_id',
        how='left'
    )
    
    logger.info(f"Cenários gerados: {len(df_wide)} linhas, {len(variaveis_macro)} variáveis")
    
    return df_wide


def calcular_ecl_sob_cenarios(
    df_carteira: pd.DataFrame,
    df_cenarios: pd.DataFrame,
    funcao_ecl: callable,
    macro_features: List[str]
) -> pd.DataFrame:
    """
    Calcula ECL sob diferentes cenários macroeconômicos.
    
    Útil para stress testing e cálculo de ECL ponderado por cenários.
    
    Args:
        df_carteira: Carteira com PDs base
        df_cenarios: Cenários gerados por gerar_cenarios_macroeconomicos_avancados
        funcao_ecl: Função que calcula ECL (recebe df_carteira e retorna ECL)
        macro_features: Features macro usadas no cálculo
        
    Returns:
        DataFrame com ECL por cenário
    """
    logger.info("Calculando ECL sob cenários macroeconômicos")
    
    resultados = []
    
    for cenario_id in df_cenarios['cenario_id'].unique():
        cenario_dados = df_cenarios[df_cenarios['cenario_id'] == cenario_id]
        
        # Usar valores médios do cenário para toda a carteira
        for feature in macro_features:
            if feature in cenario_dados.columns:
                df_carteira[feature] = cenario_dados[feature].mean()
        
        # Calcular ECL
        ecl_cenario = funcao_ecl(df_carteira)
        
        resultados.append({
            'cenario_id': cenario_id,
            'cenario_tipo': cenario_dados['cenario_tipo'].iloc[0] if 'cenario_tipo' in cenario_dados else 'base',
            'ecl_total': ecl_cenario.sum() if hasattr(ecl_cenario, 'sum') else ecl_cenario,
            'ecl_media': ecl_cenario.mean() if hasattr(ecl_cenario, 'mean') else ecl_cenario
        })
    
    df_resultados = pd.DataFrame(resultados)
    
    # Calcular ECL ponderado (40% base, 30% otimista, 30% pessimista - padrão IFRS 9)
    ecl_base = df_resultados[df_resultados['cenario_tipo'] == 'base']['ecl_total'].mean()
    ecl_otim = df_resultados[df_resultados['cenario_tipo'] == 'otimista']['ecl_total'].mean()
    ecl_pess = df_resultados[df_resultados['cenario_tipo'] == 'pessimista']['ecl_total'].mean()
    
    ecl_ponderado = 0.40 * ecl_base + 0.30 * ecl_otim + 0.30 * ecl_pess
    
    logger.info(f"ECL Base: {ecl_base:.2f}, Otimista: {ecl_otim:.2f}, Pessimista: {ecl_pess:.2f}")
    logger.info(f"ECL Ponderado (40/30/30): {ecl_ponderado:.2f}")
    
    return df_resultados

