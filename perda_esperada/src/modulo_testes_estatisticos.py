# -*- coding: utf-8 -*-
"""
Módulo de Testes Estatísticos para Modelos de Risco de Crédito

Este módulo implementa uma bateria completa de testes estatísticos para validação
dos modelos de risco de crédito, garantindo conformidade com as exigências do BCB
e robustez na estimativa de parâmetros.

Testes implementados:
- Teste de Normalidade (Shapiro-Wilk, Anderson-Darling, Kolmogorov-Smirnov)
- Teste de Homocedasticidade (Breusch-Pagan, White)
- Teste de Autocorrelação (Durbin-Watson, Ljung-Box)

Autor: Sistema de Perda Esperada
Data: 2025
"""

import numpy as np
import pandas as pd
from scipy import stats

# Statsmodels é opcional (algumas funcionalidades avançadas ficam indisponíveis)
try:
    from statsmodels.stats.diagnostic import het_breuschpagan, het_white
    from statsmodels.stats.stattools import durbin_watson
    from statsmodels.tsa.stattools import acf
    from statsmodels.stats.diagnostic import acorr_ljungbox
    STATSMODELS_DISPONIVEL = True
except ImportError:
    STATSMODELS_DISPONIVEL = False
    het_breuschpagan = het_white = durbin_watson = acf = acorr_ljungbox = None

import warnings
from typing import Dict, Any, Tuple, Optional
import logging
import os
import sys

# Tentar importar configurações (opcional)
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))
    from configuracoes_globais import get_arquivo_operacoes_mais_recente, get_arquivo_limites_mais_recente
    CONFIG_DISPONIVEL = True
except ImportError:
    CONFIG_DISPONIVEL = False
    def get_arquivo_operacoes_mais_recente():
        return None
    def get_arquivo_limites_mais_recente():
        return None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestesEstatisticos:
    """
    Classe para execução de testes estatísticos em modelos de risco de crédito.
    """
    
    def __init__(self):
        """
        Inicializa a classe de testes estatísticos.
        """
        self.criterios_aprovacao = {
            'normalidade_p_value_min': 0.01,  # Mais tolerante para normalidade
            'homocedasticidade_p_value_min': 0.05,
            'durbin_watson_min': 1.5,
            'durbin_watson_max': 2.5,
            'ljung_box_p_value_min': 0.05
        }
    
    def teste_normalidade(self, residuos_modelo: np.ndarray) -> Dict[str, Any]:
        """
        Testa a normalidade dos resíduos do modelo usando múltiplos testes.
        
        Args:
            residuos_modelo: Array com os resíduos do modelo
            
        Returns:
            Dict com resultados dos testes de normalidade
        """
        try:
            # Remover valores NaN e infinitos
            residuos_limpos = self._limpar_residuos(residuos_modelo)
            
            if len(residuos_limpos) < 3:
                logger.warning("Número insuficiente de resíduos para teste de normalidade")
                return self._resultado_teste_invalido("normalidade")
            
            resultados = {}
            
            # Teste de Shapiro-Wilk (limitado a 5000 observações)
            if len(residuos_limpos) <= 5000:
                try:
                    stat_shapiro, p_value_shapiro = stats.shapiro(residuos_limpos)
                    resultados['shapiro_wilk'] = {
                        'estatistica': float(stat_shapiro),
                        'p_value': float(p_value_shapiro),
                        'aprovado': p_value_shapiro > self.criterios_aprovacao['normalidade_p_value_min']
                    }
                except Exception as e:
                    logger.warning(f"Erro no teste Shapiro-Wilk: {e}")
                    resultados['shapiro_wilk'] = {'erro': str(e)}
            else:
                logger.info("Amostra muito grande para Shapiro-Wilk, usando apenas outros testes")
            
            # Teste de Anderson-Darling
            try:
                resultado_anderson = stats.anderson(residuos_limpos, dist='norm')
                # Usar nível de significância de 5% (índice 2)
                valor_critico_5pct = resultado_anderson.critical_values[2]
                aprovado_anderson = resultado_anderson.statistic < valor_critico_5pct
                
                resultados['anderson_darling'] = {
                    'estatistica': float(resultado_anderson.statistic),
                    'valor_critico_5pct': float(valor_critico_5pct),
                    'aprovado': aprovado_anderson
                }
            except Exception as e:
                logger.warning(f"Erro no teste Anderson-Darling: {e}")
                resultados['anderson_darling'] = {'erro': str(e)}
            
            # Teste de Kolmogorov-Smirnov
            try:
                # Normalizar os resíduos
                residuos_normalizados = (residuos_limpos - np.mean(residuos_limpos)) / np.std(residuos_limpos)
                stat_ks, p_value_ks = stats.kstest(residuos_normalizados, 'norm')
                
                resultados['kolmogorov_smirnov'] = {
                    'estatistica': float(stat_ks),
                    'p_value': float(p_value_ks),
                    'aprovado': p_value_ks > self.criterios_aprovacao['normalidade_p_value_min']
                }
            except Exception as e:
                logger.warning(f"Erro no teste Kolmogorov-Smirnov: {e}")
                resultados['kolmogorov_smirnov'] = {'erro': str(e)}
            
            # Avaliação geral
            testes_validos = [teste for teste in resultados.values() if 'erro' not in teste]
            if testes_validos:
                aprovacoes = [teste.get('aprovado', False) for teste in testes_validos]
                resultados['aprovacao_geral'] = {
                    'aprovado': any(aprovacoes),  # Pelo menos um teste deve aprovar
                    'testes_aprovados': sum(aprovacoes),
                    'total_testes': len(aprovacoes)
                }
            else:
                resultados['aprovacao_geral'] = {'aprovado': False, 'erro': 'Nenhum teste válido'}
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro geral no teste de normalidade: {e}")
            return {'erro': str(e)}
    
    def teste_homocedasticidade(self, residuos_modelo: np.ndarray, 
                               valores_ajustados: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Testa a homocedasticidade dos resíduos usando testes de Breusch-Pagan e White.
        
        Args:
            residuos_modelo: Array com os resíduos do modelo
            valores_ajustados: Array com valores ajustados (opcional)
            
        Returns:
            Dict com resultados dos testes de homocedasticidade
        """
        try:
            # Limpar resíduos
            residuos_limpos = self._limpar_residuos(residuos_modelo)
            
            if len(residuos_limpos) < 10:
                logger.warning("Número insuficiente de resíduos para teste de homocedasticidade")
                return self._resultado_teste_invalido("homocedasticidade")
            
            resultados = {}
            
            # Se não temos valores ajustados, usar índices como proxy
            if valores_ajustados is None:
                valores_ajustados = np.arange(len(residuos_limpos))
            else:
                valores_ajustados = self._limpar_residuos(valores_ajustados)
                # Garantir mesmo tamanho
                min_len = min(len(residuos_limpos), len(valores_ajustados))
                residuos_limpos = residuos_limpos[:min_len]
                valores_ajustados = valores_ajustados[:min_len]
            
            # Criar DataFrame para os testes
            df_teste = pd.DataFrame({
                'residuos': residuos_limpos,
                'valores_ajustados': valores_ajustados
            })
            
            # Teste de Breusch-Pagan
            try:
                # Adicionar constante à matriz de variáveis exógenas
                import statsmodels.api as sm
                X = sm.add_constant(df_teste[['valores_ajustados']])
                y_residuos_quad = df_teste['residuos'] ** 2
                
                lm_stat, p_value_bp, f_stat, p_value_f = het_breuschpagan(
                    y_residuos_quad, X
                )
                
                resultados['breusch_pagan'] = {
                    'estatistica_lm': float(lm_stat),
                    'p_value': float(p_value_bp),
                    'estatistica_f': float(f_stat),
                    'p_value_f': float(p_value_f),
                    'aprovado': p_value_bp > self.criterios_aprovacao['homocedasticidade_p_value_min']
                }
            except Exception as e:
                logger.warning(f"Erro no teste Breusch-Pagan: {e}")
                resultados['breusch_pagan'] = {'erro': str(e)}
            
            # Teste de White
            try:
                # Adicionar constante à matriz de variáveis exógenas
                import statsmodels.api as sm
                X = sm.add_constant(df_teste[['valores_ajustados']])
                y_residuos_quad = df_teste['residuos'] ** 2
                
                lm_stat_white, p_value_white, f_stat_white, p_value_f_white = het_white(
                    y_residuos_quad, X
                )
                
                resultados['white'] = {
                    'estatistica_lm': float(lm_stat_white),
                    'p_value': float(p_value_white),
                    'estatistica_f': float(f_stat_white),
                    'p_value_f': float(p_value_f_white),
                    'aprovado': p_value_white > self.criterios_aprovacao['homocedasticidade_p_value_min']
                }
            except Exception as e:
                logger.warning(f"Erro no teste White: {e}")
                resultados['white'] = {'erro': str(e)}
            
            # Avaliação geral
            testes_validos = [teste for teste in resultados.values() if 'erro' not in teste]
            if testes_validos:
                aprovacoes = [teste.get('aprovado', False) for teste in testes_validos]
                resultados['aprovacao_geral'] = {
                    'aprovado': any(aprovacoes),
                    'testes_aprovados': sum(aprovacoes),
                    'total_testes': len(aprovacoes)
                }
            else:
                resultados['aprovacao_geral'] = {'aprovado': False, 'erro': 'Nenhum teste válido'}
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro geral no teste de homocedasticidade: {e}")
            return {'erro': str(e)}
    
    def teste_autocorrelacao(self, residuos_modelo: np.ndarray) -> Dict[str, Any]:
        """
        Testa a autocorrelação dos resíduos usando testes de Durbin-Watson e Ljung-Box.
        
        Args:
            residuos_modelo: Array com os resíduos do modelo
            
        Returns:
            Dict com resultados dos testes de autocorrelação
        """
        try:
            # Limpar resíduos
            residuos_limpos = self._limpar_residuos(residuos_modelo)
            
            if len(residuos_limpos) < 10:
                logger.warning("Número insuficiente de resíduos para teste de autocorrelação")
                return self._resultado_teste_invalido("autocorrelacao")
            
            resultados = {}
            
            # Teste de Durbin-Watson
            try:
                dw_stat = durbin_watson(residuos_limpos)
                aprovado_dw = (self.criterios_aprovacao['durbin_watson_min'] <= dw_stat <= 
                              self.criterios_aprovacao['durbin_watson_max'])
                
                resultados['durbin_watson'] = {
                    'estatistica': float(dw_stat),
                    'aprovado': aprovado_dw,
                    'interpretacao': self._interpretar_durbin_watson(dw_stat)
                }
            except Exception as e:
                logger.warning(f"Erro no teste Durbin-Watson: {e}")
                resultados['durbin_watson'] = {'erro': str(e)}
            
            # Teste de Ljung-Box
            try:
                # Usar até 10 lags ou 10% do tamanho da amostra, o que for menor
                max_lags = min(10, max(1, len(residuos_limpos) // 10))
                
                ljung_box_result = acorr_ljungbox(
                    residuos_limpos, 
                    lags=max_lags, 
                    return_df=True
                )
                
                # Usar o p-value do último lag
                p_value_ljung = ljung_box_result['lb_pvalue'].iloc[-1]
                estatistica_ljung = ljung_box_result['lb_stat'].iloc[-1]
                
                resultados['ljung_box'] = {
                    'estatistica': float(estatistica_ljung),
                    'p_value': float(p_value_ljung),
                    'lags_testados': int(max_lags),
                    'aprovado': p_value_ljung > self.criterios_aprovacao['ljung_box_p_value_min']
                }
            except Exception as e:
                logger.warning(f"Erro no teste Ljung-Box: {e}")
                resultados['ljung_box'] = {'erro': str(e)}
            
            # Avaliação geral
            testes_validos = [teste for teste in resultados.values() if 'erro' not in teste]
            if testes_validos:
                aprovacoes = [teste.get('aprovado', False) for teste in testes_validos]
                resultados['aprovacao_geral'] = {
                    'aprovado': all(aprovacoes),  # Todos os testes devem aprovar para autocorrelação
                    'testes_aprovados': sum(aprovacoes),
                    'total_testes': len(aprovacoes)
                }
            else:
                resultados['aprovacao_geral'] = {'aprovado': False, 'erro': 'Nenhum teste válido'}
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro geral no teste de autocorrelação: {e}")
            return {'erro': str(e)}
    
    def executar_bateria_completa(self, residuos_modelo: np.ndarray, 
                                 valores_ajustados: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Executa a bateria completa de testes estatísticos.
        
        Args:
            residuos_modelo: Array com os resíduos do modelo
            valores_ajustados: Array com valores ajustados (opcional)
            
        Returns:
            Dict com resultados de todos os testes
        """
        logger.info("Iniciando bateria completa de testes estatísticos")
        
        resultados_completos = {
            'normalidade': self.teste_normalidade(residuos_modelo),
            'homocedasticidade': self.teste_homocedasticidade(residuos_modelo, valores_ajustados),
            'autocorrelacao': self.teste_autocorrelacao(residuos_modelo)
        }
        
        # Avaliação geral de todos os testes
        aprovacoes_gerais = []
        for categoria, resultado in resultados_completos.items():
            if 'aprovacao_geral' in resultado:
                aprovacoes_gerais.append(resultado['aprovacao_geral'].get('aprovado', False))
        
        resultados_completos['avaliacao_final'] = {
            'modelo_aprovado': all(aprovacoes_gerais),
            'categorias_aprovadas': sum(aprovacoes_gerais),
            'total_categorias': len(aprovacoes_gerais),
            'recomendacao': self._gerar_recomendacao(resultados_completos)
        }
        
        logger.info(f"Bateria de testes concluída. Modelo aprovado: {resultados_completos['avaliacao_final']['modelo_aprovado']}")
        
        return resultados_completos
    
    def _limpar_residuos(self, residuos: np.ndarray) -> np.ndarray:
        """
        Remove valores NaN e infinitos dos resíduos.
        """
        residuos_array = np.asarray(residuos)
        mask = np.isfinite(residuos_array)
        return residuos_array[mask]
    
    def _resultado_teste_invalido(self, tipo_teste: str) -> Dict[str, Any]:
        """
        Retorna resultado padrão para teste inválido.
        """
        return {
            'erro': f'Dados insuficientes para teste de {tipo_teste}',
            'aprovacao_geral': {'aprovado': False, 'erro': 'Teste inválido'}
        }
    
    def _interpretar_durbin_watson(self, dw_stat: float) -> str:
        """
        Interpreta o resultado do teste Durbin-Watson.
        """
        if dw_stat < 1.5:
            return "Autocorrelação positiva detectada"
        elif dw_stat > 2.5:
            return "Autocorrelação negativa detectada"
        else:
            return "Sem evidência de autocorrelação"
    
    def _gerar_recomendacao(self, resultados: Dict[str, Any]) -> str:
        """
        Gera recomendação baseada nos resultados dos testes.
        """
        problemas = []
        
        if not resultados.get('normalidade', {}).get('aprovacao_geral', {}).get('aprovado', False):
            problemas.append("normalidade dos resíduos")
        
        if not resultados.get('homocedasticidade', {}).get('aprovacao_geral', {}).get('aprovado', False):
            problemas.append("homocedasticidade")
        
        if not resultados.get('autocorrelacao', {}).get('aprovacao_geral', {}).get('aprovado', False):
            problemas.append("autocorrelação")
        
        if not problemas:
            return "Modelo atende a todos os critérios estatísticos. Aprovado para uso."
        else:
            return f"Modelo apresenta problemas em: {', '.join(problemas)}. Revisar especificação do modelo."


def carregar_dados_reais_clientes() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carrega dados reais dos clientes das bases de dados configuradas.
    
    Returns:
        Tuple contendo (dados_operacoes, dados_limites)
    """
    try:
        # Carregar arquivo de operações mais recente
        arquivo_operacoes = get_arquivo_operacoes_mais_recente()
        if not arquivo_operacoes or not os.path.exists(arquivo_operacoes):
            logger.warning("Arquivo de operações não encontrado, usando dados sintéticos")
            return None, None
        
        logger.info(f"Carregando dados de operações: {arquivo_operacoes}")
        # Tentar diferentes encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                dados_operacoes = pd.read_csv(arquivo_operacoes, encoding=encoding, sep=';')
                logger.info(f"Dados de operações carregados com encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        else:
            logger.error("Não foi possível carregar dados de operações com nenhum encoding")
            return None, None
        
        # Carregar arquivo de limites mais recente
        arquivo_limites = get_arquivo_limites_mais_recente()
        dados_limites = None
        if arquivo_limites and os.path.exists(arquivo_limites):
            logger.info(f"Carregando dados de limites: {arquivo_limites}")
            # Tentar diferentes encodings para limites também
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    dados_limites = pd.read_csv(arquivo_limites, encoding=encoding, sep=';')
                    logger.info(f"Dados de limites carregados com encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                logger.warning("Não foi possível carregar dados de limites com nenhum encoding")
        else:
            logger.warning("Arquivo de limites não encontrado")
        
        logger.info(f"Dados carregados - Operações: {len(dados_operacoes)} registros")
        if dados_limites is not None:
            logger.info(f"Dados carregados - Limites: {len(dados_limites)} registros")
        
        return dados_operacoes, dados_limites
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados reais: {e}")
        return None, None

def gerar_residuos_de_dados_reais(dados_operacoes: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gera resíduos e valores ajustados a partir de dados reais de clientes.
    
    Args:
        dados_operacoes: DataFrame com dados de operações dos clientes
        
    Returns:
        Tuple contendo (residuos, valores_ajustados)
    """
    try:
        # Selecionar colunas numéricas relevantes para análise
        colunas_numericas = dados_operacoes.select_dtypes(include=[np.number]).columns
        
        if len(colunas_numericas) == 0:
            logger.warning("Nenhuma coluna numérica encontrada nos dados")
            return None, None
        
        # Usar as primeiras colunas numéricas disponíveis
        coluna_y = colunas_numericas[0]  # Variável dependente
        coluna_x = colunas_numericas[1] if len(colunas_numericas) > 1 else colunas_numericas[0]
        
        # Remover valores nulos
        dados_limpos = dados_operacoes[[coluna_y, coluna_x]].dropna()
        
        if len(dados_limpos) < 100:
            logger.warning("Dados insuficientes após limpeza")
            return None, None
        
        # Ajustar um modelo linear simples para gerar resíduos
        from sklearn.linear_model import LinearRegression
        
        X = dados_limpos[[coluna_x]].values
        y = dados_limpos[coluna_y].values
        
        modelo = LinearRegression()
        modelo.fit(X, y)
        
        valores_ajustados = modelo.predict(X)
        residuos = y - valores_ajustados
        
        logger.info(f"Resíduos gerados a partir de {len(residuos)} observações")
        logger.info(f"Variáveis utilizadas: {coluna_y} (dependente) e {coluna_x} (independente)")
        
        return residuos, valores_ajustados
        
    except Exception as e:
        logger.error(f"Erro ao gerar resíduos de dados reais: {e}")
        return None, None

def validar_modelo_estatisticamente(residuos_modelo: np.ndarray, 
                                   valores_ajustados: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Função de conveniência para validar um modelo estatisticamente.
    
    Args:
        residuos_modelo: Array com os resíduos do modelo
        valores_ajustados: Array com valores ajustados (opcional)
        
    Returns:
        Dict com resultados completos dos testes
    """
    testes = TestesEstatisticos()
    return testes.executar_bateria_completa(residuos_modelo, valores_ajustados)

def validar_modelo_com_dados_reais() -> Dict[str, Any]:
    """
    Valida modelo estatisticamente usando dados reais dos clientes.
    
    Returns:
        Dict com resultados completos dos testes usando dados reais
    """
    logger.info("Iniciando validação com dados reais dos clientes")
    
    # Carregar dados reais
    dados_operacoes, dados_limites = carregar_dados_reais_clientes()
    
    if dados_operacoes is None:
        logger.warning("Não foi possível carregar dados reais, usando dados sintéticos")
        # Fallback para dados sintéticos
        np.random.seed(42)
        residuos = np.random.normal(0, 1, 1000)
        valores_ajustados = np.random.normal(5, 2, 1000)
        resultados = validar_modelo_estatisticamente(residuos, valores_ajustados)
        # Adicionar informações sobre a fonte dos dados
        resultados['fonte_dados'] = {
            'tipo': 'dados_sinteticos',
            'num_observacoes': len(residuos),
            'arquivo_operacoes': None
        }
        return resultados
    
    # Gerar resíduos dos dados reais
    residuos, valores_ajustados = gerar_residuos_de_dados_reais(dados_operacoes)
    
    if residuos is None:
        logger.warning("Não foi possível gerar resíduos dos dados reais, usando dados sintéticos")
        # Fallback para dados sintéticos
        np.random.seed(42)
        residuos = np.random.normal(0, 1, 1000)
        valores_ajustados = np.random.normal(5, 2, 1000)
        dados_operacoes = None  # Marcar que não conseguiu usar dados reais
    
    # Executar testes estatísticos
    resultados = validar_modelo_estatisticamente(residuos, valores_ajustados)
    
    # Adicionar informações sobre a fonte dos dados
    resultados['fonte_dados'] = {
        'tipo': 'dados_reais' if dados_operacoes is not None else 'dados_sinteticos',
        'num_observacoes': len(residuos),
        'arquivo_operacoes': get_arquivo_operacoes_mais_recente() if dados_operacoes is not None else None
    }
    
    return resultados


if __name__ == "__main__":
    # Exemplo de uso com dados reais
    print("=== TESTE DE VALIDAÇÃO ESTATÍSTICA COM DADOS REAIS ====")
    print("Executando testes estatísticos com dados reais dos clientes...\n")
    
    # Testar com dados reais dos clientes
    resultado_dados_reais = validar_modelo_com_dados_reais()
    
    print(f"Fonte dos dados: {resultado_dados_reais['fonte_dados']['tipo']}")
    print(f"Número de observações: {resultado_dados_reais['fonte_dados']['num_observacoes']}")
    if resultado_dados_reais['fonte_dados']['arquivo_operacoes']:
        print(f"Arquivo utilizado: {resultado_dados_reais['fonte_dados']['arquivo_operacoes']}")
    
    print(f"\nModelo aprovado: {resultado_dados_reais['avaliacao_final']['modelo_aprovado']}")
    print(f"Categorias aprovadas: {resultado_dados_reais['avaliacao_final']['categorias_aprovadas']}/{resultado_dados_reais['avaliacao_final']['total_categorias']}")
    print(f"Recomendação: {resultado_dados_reais['avaliacao_final']['recomendacao']}")
    
    # Mostrar detalhes dos testes
    print("\n=== DETALHES DOS TESTES ====")
    
    # Teste de normalidade
    if 'normalidade' in resultado_dados_reais:
        normalidade = resultado_dados_reais['normalidade']
        if 'aprovacao_geral' in normalidade:
            print(f"Normalidade: {'[OK] APROVADO' if normalidade['aprovacao_geral']['aprovado'] else '[X] REPROVADO'}")
    
    # Teste de homocedasticidade
    if 'homocedasticidade' in resultado_dados_reais:
        homoced = resultado_dados_reais['homocedasticidade']
        if 'aprovacao_geral' in homoced:
            print(f"Homocedasticidade: {'[OK] APROVADO' if homoced['aprovacao_geral']['aprovado'] else '[X] REPROVADO'}")
    
    # Teste de autocorrelação
    if 'autocorrelacao' in resultado_dados_reais:
        autocorr = resultado_dados_reais['autocorrelacao']
        if 'aprovacao_geral' in autocorr:
            print(f"Autocorrelação: {'[OK] APROVADO' if autocorr['aprovacao_geral']['aprovado'] else '[X] REPROVADO'}")
    
    print("\n=== TESTE ADICIONAL COM DADOS SINTÉTICOS (COMPARAÇÃO) ====")
    
    # Comparar com dados sintéticos para validação
    np.random.seed(42)
    residuos_sinteticos = np.random.normal(0, 1, 1000)
    valores_ajustados_sinteticos = np.random.normal(5, 2, 1000)
    
    resultado_sintetico = validar_modelo_estatisticamente(residuos_sinteticos, valores_ajustados_sinteticos)
    print(f"Modelo sintético aprovado: {resultado_sintetico['avaliacao_final']['modelo_aprovado']}")
    print(f"Recomendação sintética: {resultado_sintetico['avaliacao_final']['recomendacao']}")