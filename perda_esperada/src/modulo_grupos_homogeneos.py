#!/usr/bin/env python3
"""
Módulo Consolidado para Sistema de Grupos Homogêneos de Risco (GHs).

Este módulo consolida as funcionalidades de criação, validação e aplicação de grupos
homogêneos de risco em dados sintéticos e reais, implementando o conceito conforme
a documentação técnica da Resolução CMN 4.966 e BCB 352.

Consolidação realizada para eliminar redundâncias entre grupos_homogeneos.py e
aplicacao_grupos_reais.py, criando um módulo unificado e otimizado.

Autor: Sistema ECL - Expected Credit Loss
Data: 2025-05-31 (Consolidação)
Versão: 2.0 - Módulo Consolidado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import logging
import joblib
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import warnings
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# Configurações
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações específicas para integração com Forward Looking
CONFIG_WOE_INTEGRATION = {
    'calcular_woe_automatico': True,
    'salvar_woe_scores': True,
    'validar_homogeneidade_woe': True,
    'threshold_woe_homogeneidade': 0.1,  # Máxima variação de WOE dentro do grupo
    'min_contratos_woe': 30  # Mínimo de contratos para cálculo confiável de WOE
}

# Diretórios para artefatos
ARTEFATOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'artefatos_modelos')
RELATORIOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'relatorios')

# Diretórios de saída (compatibilidade)
OUTPUT_DIR_MODULOS_PLANILHAS = RELATORIOS_DIR
OUTPUT_DIR_MODULOS_DIVERSOS = ARTEFATOS_DIR

os.makedirs(ARTEFATOS_DIR, exist_ok=True)
os.makedirs(RELATORIOS_DIR, exist_ok=True)

# Configurações padrão para grupos homogêneos
CONFIG_DEFAULT = {
    'num_grupos_min': 5,
    'num_grupos_max': 15,
    'tamanho_min_grupo': 50,
    'threshold_homogeneidade': 0.3,
    'threshold_heterogeneidade': 0.05,
    'metodo_agrupamento': 'percentis',  # 'percentis', 'kmeans', 'densidade'
    'revalidacao_periodos': 6,
    # Integração com WOE
    'integrar_woe': True,
    'peso_woe_agrupamento': 0.3,  # Peso do WOE no agrupamento (30%)
    'validar_woe_homogeneidade': True
}


class CalculadorPDReais:
    """
    Classe para calcular scores de PD a partir dos dados reais da instituição.
    Responsável por processar dados reais e gerar scores sintéticos quando necessário.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CalculadorPDReais")
        
    def carregar_dados_reais(self, caminho_csv: str, amostra: Optional[int] = None) -> pd.DataFrame:
        """
        Carrega dados reais do arquivo CSV da instituição.
        
        Args:
            caminho_csv: Caminho para o arquivo CSV
            amostra: Número de linhas para carregar (None = todas)
        
        Returns:
            DataFrame com os dados carregados
        """
        self.logger.info(f"Carregando dados reais de: {caminho_csv}")
        
        try:
            # Função para converter números brasileiros (vírgula como decimal)
            def converter_numero_brasileiro(valor):
                """Converte números no formato brasileiro (vírgula como decimal) para float."""
                if pd.isna(valor) or valor == '':
                    return 0.0
                if isinstance(valor, (int, float)):
                    return float(valor)
                if isinstance(valor, str):
                    # Remove espaços e substitui vírgula por ponto
                    valor_limpo = valor.strip().replace(',', '.')
                    try:
                        return float(valor_limpo)
                    except ValueError:
                        return 0.0
                return 0.0
            
            # Carregar dados com separador correto
            if amostra:
                dados = pd.read_csv(caminho_csv, nrows=amostra, sep=';')
                self.logger.info(f"Carregados {len(dados)} registros (amostra)")
            else:
                dados = pd.read_csv(caminho_csv, sep=';')
                self.logger.info(f"Carregados {len(dados)} registros (todos)")
            
            # Converter colunas numéricas essenciais
            colunas_numericas = ['saldo_devedor', 'pd_aplicada', 'lgd_aplicada', 'ead_aplicada', 
                               'pd_lifetime_calculada', 'limite_credito']
            
            for coluna in colunas_numericas:
                if coluna in dados.columns:
                    dados[coluna] = dados[coluna].apply(converter_numero_brasileiro)
                    self.logger.info(f"Coluna '{coluna}' convertida para formato numérico")
            
            self.logger.info(f"Colunas disponíveis: {list(dados.columns)}")
            return dados
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {str(e)}")
            raise
    
    def preprocessar_dados(self, dados: pd.DataFrame) -> pd.DataFrame:
        """
        Realiza pré-processamento dos dados reais para cálculo de scores.
        """
        dados_proc = dados.copy()
        
        # Limpar e converter valores numéricos
        colunas_numericas = ['Saldo Devedor', 'Valor Original Contr.', 'Qtd. Parc. a Vencer', 
                            'Qtd. Parc. Contrato', 'Qtd. Parc. Vencidas', 'Dias de Atraso']
        
        for col in colunas_numericas:
            if col in dados_proc.columns:
                dados_proc[col] = pd.to_numeric(dados_proc[col], errors='coerce').fillna(0)
        
        # Calcular métricas derivadas
        self._calcular_metricas_derivadas(dados_proc)
        
        return dados_proc
    
    def _calcular_metricas_derivadas(self, dados: pd.DataFrame):
        """Calcula métricas derivadas dos dados originais."""
        # Atraso máximo baseado em Dias de Atraso
        if 'Dias de Atraso' in dados.columns:
            dados['atraso_maximo'] = dados['Dias de Atraso'].fillna(0)
        else:
            dados['atraso_maximo'] = self._extrair_atraso_do_desempenho(dados)
        
        # Utilização do crédito
        if 'Saldo Devedor' in dados.columns and 'Valor Original Contr.' in dados.columns:
            dados['utilizacao_credito'] = dados['Saldo Devedor'] / (dados['Valor Original Contr.'] + 1e-6)
            dados['utilizacao_credito'] = dados['utilizacao_credito'].clip(0, 1)
        
        # Idade da operação
        if 'Data Contrat. Oper.' in dados.columns:
            try:
                dados['Data Contrat. Oper.'] = pd.to_datetime(dados['Data Contrat. Oper.'], errors='coerce')
                dados['idade_operacao_anos'] = (pd.Timestamp.now() - dados['Data Contrat. Oper.']).dt.days / 365.25
                dados['idade_operacao_anos'] = dados['idade_operacao_anos'].fillna(0)
            except:
                dados['idade_operacao_anos'] = 0
        
        self.logger.info("Métricas derivadas calculadas")
    
    def _extrair_atraso_do_desempenho(self, dados: pd.DataFrame) -> pd.Series:
        """Extrai informação de atraso da coluna 'Desempenho da Operação'."""
        atraso = pd.Series(0, index=dados.index)
        
        if 'Desempenho da Operação' in dados.columns:
            atraso.loc[dados['Desempenho da Operação'].str.contains('vencer', case=False, na=False)] = 0
            atraso.loc[dados['Desempenho da Operação'].str.contains('31.*60', case=False, na=False)] = 45
            atraso.loc[dados['Desempenho da Operação'].str.contains('61.*90', case=False, na=False)] = 75
            atraso.loc[dados['Desempenho da Operação'].str.contains('90', case=False, na=False)] = 120
            
        return atraso
    
    def calcular_score_credito_sintetico(self, dados: pd.DataFrame) -> pd.DataFrame:
        """Calcula score de crédito usando dados reais quando disponível, sintético como fallback."""
        dados_score = dados.copy()
        
        # Verificar se já existe score de crédito real
        if 'score_credito' in dados.columns or 'SCORE_CREDITO' in dados.columns:
            if 'SCORE_CREDITO' in dados.columns:
                dados_score['score_credito'] = dados_score['SCORE_CREDITO']
            self.logger.info("Usando score de crédito real dos dados")
            return dados_score
        
        self.logger.info("Calculando score de crédito sintético como fallback...")
        
        score_base = 500
        
        # Componente de renda (proxy baseado no valor da operação)
        if 'Valor Original Contr.' in dados.columns:
            valor_norm = (dados['Valor Original Contr.'] - dados['Valor Original Contr.'].min()) / \
                        (dados['Valor Original Contr.'].max() - dados['Valor Original Contr.'].min() + 1e-6)
            score_valor = valor_norm * 150
        else:
            score_valor = 0
        
        # Penalização por atraso
        score_atraso = -dados['atraso_maximo'] * 1.5
        
        # Penalização por utilização alta
        if 'utilizacao_credito' in dados.columns:
            score_utilizacao = -(dados['utilizacao_credito'] - 0.3) * 100
            score_utilizacao = score_utilizacao.clip(-100, 0)
        else:
            score_utilizacao = 0
        
        # Score final
        dados_score['score_credito'] = score_base + score_valor + score_atraso + score_utilizacao
        dados_score['score_credito'] = dados_score['score_credito'].clip(300, 850)
        
        self.logger.info(f"Score de crédito sintético criado - Média: {dados_score['score_credito'].mean():.0f}")
        
        return dados_score
    
    def calcular_score_pd_sintetico(self, dados: pd.DataFrame) -> pd.DataFrame:
        """Calcula score de PD usando dados reais quando disponível, sintético como fallback."""
        dados_pd = dados.copy()
        
        # Verificar se já existe PD real
        if 'pd_aplicada_para_pe' in dados.columns or 'PD_APLICADA_PARA_PE' in dados.columns:
            if 'PD_APLICADA_PARA_PE' in dados.columns:
                dados_pd['score_pd'] = dados_pd['PD_APLICADA_PARA_PE']
            else:
                dados_pd['score_pd'] = dados_pd['pd_aplicada_para_pe']
            self.logger.info("Usando PD real dos dados")
            return dados_pd
        
        self.logger.info("Calculando score de PD sintético como fallback...")
        
        # Transformar score de crédito em PD (relação inversa)
        score_norm = (dados_pd['score_credito'] - 300) / (850 - 300)
        pd_base = 1 - score_norm
        
        # Adicionar ruído realista
        ruido = np.random.normal(0, 0.05, len(dados_pd))
        pd_base = pd_base + ruido
        
        # Ajustar por atraso (maior atraso = maior PD)
        ajuste_atraso = dados_pd['atraso_maximo'] / 365 * 0.5
        pd_final = pd_base + ajuste_atraso
        
        # Normalizar para range válido
        dados_pd['score_pd'] = pd_final.clip(0.001, 0.999)
        
        self.logger.info(f"Score de PD sintético criado - Média: {dados_pd['score_pd'].mean():.4f}")
        
        return dados_pd
    
    def classificar_estagio_credito(self, dados: pd.DataFrame) -> pd.DataFrame:
        """Classifica operações em estágios de crédito baseado no atraso (IFRS 9)."""
        dados_estagio = dados.copy()
        
        # Estágio 1: Operações normais (até 30 dias)
        dados_estagio['estagio'] = 1
        
        # Estágio 2: Aumento significativo de risco (31-90 dias)
        mask_estagio2 = (dados_estagio['atraso_maximo'] > 30) & (dados_estagio['atraso_maximo'] <= 90)
        dados_estagio.loc[mask_estagio2, 'estagio'] = 2
        
        # Estágio 3: Default (> 90 dias)
        mask_estagio3 = dados_estagio['atraso_maximo'] > 90
        dados_estagio.loc[mask_estagio3, 'estagio'] = 3
        
        self.logger.info(f"Distribuição por estágio: \n{dados_estagio['estagio'].value_counts().sort_index()}")
        
        return dados_estagio
    
    def processar_dados_completo(self, caminho_csv: str, amostra: Optional[int] = None) -> pd.DataFrame:
        """Pipeline completo de processamento dos dados reais."""
        # Carregar dados
        dados = self.carregar_dados_reais(caminho_csv, amostra)
        
        # Pré-processar
        dados = self.preprocessar_dados(dados)
        
        # Calcular scores
        dados = self.calcular_score_credito_sintetico(dados)
        dados = self.calcular_score_pd_sintetico(dados)
        
        # Classificar estágios
        dados = self.classificar_estagio_credito(dados)
        
        # Criar renda sintética se não existir
        if 'Renda mês' not in dados.columns:
            dados['Renda mês'] = dados['Valor Original Contr.'] * np.random.uniform(0.1, 0.3, len(dados))
            dados['Renda mês'] = dados['Renda mês'].clip(1000, 50000)
        
        self.logger.info(f"Processamento completo finalizado. Shape final: {dados.shape}")
        
        return dados


class GruposHomogeneosConsolidado:
    """
    Classe consolidada para gerenciar Grupos Homogêneos de Risco.
    
    Esta versão consolida as funcionalidades de criação, validação e aplicação
    de grupos homogêneos tanto para dados sintéticos quanto reais.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o sistema de grupos homogêneos.
        
        Args:
            config: Dicionário com configurações personalizadas
        """
        self.config = {**CONFIG_DEFAULT, **(config or {})}
        self.grupos_mapping = {}
        self.historico_grupos = []
        self.metricas_validacao = {}
        self.calculador_pd = CalculadorPDReais()
        self.woe_scores = {}  # Armazenar WOE scores por grupo
        self.logger = logging.getLogger(f"{__name__}.GruposHomogeneosConsolidado")
        
    def criar_grupos_homogeneos(
        self, 
        df: pd.DataFrame, 
        scores_pd: pd.Series, 
        num_grupos_alvo: Optional[int] = None,
        features_adicionais: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cria grupos homogêneos de risco baseados em scores de PD.
        
        Args:
            df: DataFrame com dados dos contratos
            scores_pd: Series com scores de PD para cada contrato
            num_grupos_alvo: Número desejado de grupos (opcional)
            features_adicionais: Features adicionais para consideração no agrupamento
            
        Returns:
            Dict com mapeamento de grupos e metadados
        """
        self.logger.info("Iniciando criação de grupos homogêneos de risco")
        
        # Validações iniciais
        if len(scores_pd) != len(df):
            raise ValueError("Tamanho do DataFrame e scores_pd devem ser iguais")
            
        if scores_pd.isna().sum() > 0:
            self.logger.warning(f"Encontrados {scores_pd.isna().sum()} scores PD nulos. Preenchendo com mediana.")
            scores_pd = scores_pd.fillna(scores_pd.median())
        
        # Determinar número de grupos
        if num_grupos_alvo is None:
            num_grupos_alvo = self._determinar_num_grupos_otimo(scores_pd)
        
        num_grupos_alvo = max(self.config['num_grupos_min'], 
                             min(num_grupos_alvo, self.config['num_grupos_max']))
        
        # Criar DataFrame de trabalho
        df_trabalho = df.copy()
        df_trabalho['score_pd'] = scores_pd
        df_trabalho['indice_original'] = df_trabalho.index
        
        # Ordenar por score de risco
        df_trabalho = df_trabalho.sort_values('score_pd')
        
        # Aplicar método de agrupamento escolhido
        metodo = self.config['metodo_agrupamento']
        
        if metodo == 'percentis':
            grupos = self._criar_grupos_percentis(df_trabalho, num_grupos_alvo)
        elif metodo == 'kmeans':
            grupos = self._criar_grupos_kmeans(df_trabalho, num_grupos_alvo, features_adicionais)
        elif metodo == 'densidade':
            grupos = self._criar_grupos_densidade(df_trabalho, num_grupos_alvo)
        else:
            raise ValueError(f"Método de agrupamento '{metodo}' não reconhecido")
        
        # Validar tamanho mínimo dos grupos
        grupos = self._ajustar_tamanho_minimo_grupos(grupos, df_trabalho)
        
        # Criar mapeamento final
        self.grupos_mapping = self._criar_mapeamento_grupos(grupos, df_trabalho)
        
        # Adicionar dados temporais para histórico
        self.grupos_mapping['data_criacao'] = datetime.now().isoformat()
        self.grupos_mapping['metodo_usado'] = metodo
        self.grupos_mapping['num_grupos'] = len(grupos)
        self.grupos_mapping['config_usada'] = self.config.copy()
        
        # Calcular WOE scores automaticamente se configurado
        if self.config.get('calcular_woe_automatico', False):
            self.logger.info("Calculando WOE scores automaticamente...")
            df_com_grupos = self.aplicar_grupos_em_dados(df_trabalho, 'score_pd')
            self.calcular_woe_scores(df_com_grupos)
            
            # Validar homogeneidade WOE se configurado
            if self.config.get('validar_homogeneidade_woe', False):
                validacao_woe = self.validar_homogeneidade_woe(df_com_grupos)
                self.grupos_mapping['validacao_woe'] = validacao_woe
        
        # Salvar artefatos
        self._salvar_grupos_mapping()
        
        self.logger.info(f"Grupos homogêneos criados com sucesso: {len(grupos)} grupos")
        return self.grupos_mapping
    
    def _determinar_num_grupos_otimo(self, scores_pd: pd.Series) -> int:
        """Determina o número ótimo de grupos baseado na distribuição dos scores."""
        n_observacoes = len(scores_pd)
        
        if n_observacoes < 500:
            return 5
        elif n_observacoes < 2000:
            return 7
        elif n_observacoes < 10000:
            return 10
        else:
            return 12
    
    def _criar_grupos_percentis(self, df_trabalho: pd.DataFrame, num_grupos: int) -> List[pd.DataFrame]:
        """Cria grupos baseado em percentis dos scores de PD."""
        self.logger.info(f"Criando {num_grupos} grupos usando método de percentis")
        
        percentis = np.linspace(0, 100, num_grupos + 1)
        cortes = np.percentile(df_trabalho['score_pd'], percentis)
        
        grupos = []
        for i in range(num_grupos):
            if i == 0:
                mask = df_trabalho['score_pd'] <= cortes[i + 1]
            elif i == num_grupos - 1:
                mask = df_trabalho['score_pd'] > cortes[i]
            else:
                mask = (df_trabalho['score_pd'] > cortes[i]) & (df_trabalho['score_pd'] <= cortes[i + 1])
            
            grupo = df_trabalho[mask].copy()
            if len(grupo) > 0:
                grupo['grupo_id'] = i + 1
                grupo['score_min'] = cortes[i] if i > 0 else df_trabalho['score_pd'].min()
                grupo['score_max'] = cortes[i + 1] if i < num_grupos - 1 else df_trabalho['score_pd'].max()
                grupos.append(grupo)
        
        return grupos
    
    def _criar_grupos_kmeans(self, df_trabalho: pd.DataFrame, num_grupos: int, features_adicionais: Optional[List[str]] = None) -> List[pd.DataFrame]:
        """Cria grupos usando algoritmo K-means."""
        self.logger.info(f"Criando {num_grupos} grupos usando método K-means")
        
        # Preparar features para clustering
        features_cluster = ['score_pd']
        if features_adicionais:
            features_disponiveis = [f for f in features_adicionais if f in df_trabalho.columns]
            features_cluster.extend(features_disponiveis)
        
        # Normalizar features
        scaler = StandardScaler()
        X = scaler.fit_transform(df_trabalho[features_cluster])
        
        # Aplicar K-means
        kmeans = KMeans(n_clusters=num_grupos, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        # Criar grupos
        grupos = []
        df_trabalho['cluster_temp'] = labels
        
        for i in range(num_grupos):
            grupo = df_trabalho[df_trabalho['cluster_temp'] == i].copy()
            if len(grupo) > 0:
                grupo['grupo_id'] = i + 1
                grupo['score_min'] = grupo['score_pd'].min()
                grupo['score_max'] = grupo['score_pd'].max()
                grupos.append(grupo)
        
        # Remover coluna temporária
        for grupo in grupos:
            grupo.drop('cluster_temp', axis=1, inplace=True)
        
        return grupos
    
    def _criar_grupos_densidade(self, df_trabalho: pd.DataFrame, num_grupos: int) -> List[pd.DataFrame]:
        """Cria grupos baseado na densidade dos scores."""
        self.logger.info(f"Criando {num_grupos} grupos usando método de densidade")
        
        # Usar análise de densidade para encontrar pontos de corte naturais
        try:
            densidade = stats.gaussian_kde(df_trabalho['score_pd'])
            x_range = np.linspace(df_trabalho['score_pd'].min(), df_trabalho['score_pd'].max(), 1000)
            densidade_valores = densidade(x_range)
            
            # Encontrar mínimos locais (vales na densidade)
            from scipy.signal import find_peaks
            picos, _ = find_peaks(-densidade_valores)
            
            if len(picos) >= num_grupos - 1:
                cortes_indices = picos[:num_grupos-1]
                cortes = x_range[cortes_indices]
            else:
                # Fallback para percentis se não encontrar suficientes vales
                percentis = np.linspace(0, 100, num_grupos + 1)
                cortes = np.percentile(df_trabalho['score_pd'], percentis[1:-1])
            
        except:
            # Fallback para percentis em caso de erro
            self.logger.warning("Erro na análise de densidade. Usando percentis como fallback.")
            percentis = np.linspace(0, 100, num_grupos + 1)
            cortes = np.percentile(df_trabalho['score_pd'], percentis[1:-1])
        
        # Criar grupos usando os cortes
        grupos = []
        cortes_completos = [df_trabalho['score_pd'].min()] + list(cortes) + [df_trabalho['score_pd'].max()]
        
        for i in range(num_grupos):
            if i == 0:
                mask = df_trabalho['score_pd'] <= cortes_completos[i + 1]
            elif i == num_grupos - 1:
                mask = df_trabalho['score_pd'] > cortes_completos[i]
            else:
                mask = (df_trabalho['score_pd'] > cortes_completos[i]) & (df_trabalho['score_pd'] <= cortes_completos[i + 1])
            
            grupo = df_trabalho[mask].copy()
            if len(grupo) > 0:
                grupo['grupo_id'] = i + 1
                grupo['score_min'] = cortes_completos[i]
                grupo['score_max'] = cortes_completos[i + 1]
                grupos.append(grupo)
        
        return grupos
    
    def _ajustar_tamanho_minimo_grupos(self, grupos: List[pd.DataFrame], df_trabalho: pd.DataFrame) -> List[pd.DataFrame]:
        """Ajusta grupos para garantir tamanho mínimo."""
        tamanho_min = self.config['tamanho_min_grupo']
        grupos_ajustados = []
        
        for grupo in grupos:
            if len(grupo) >= tamanho_min:
                grupos_ajustados.append(grupo)
            else:
                self.logger.warning(f"Grupo {grupo['grupo_id'].iloc[0]} muito pequeno ({len(grupo)} < {tamanho_min}). Será mesclado.")
        
        # Se houver grupos muito pequenos, mesclar com vizinhos
        if len(grupos_ajustados) < len(grupos):
            self.logger.info("Reagrupando para atender tamanho mínimo...")
            # Simplificação: recriar com menos grupos
            num_grupos_novo = len(grupos_ajustados)
            if num_grupos_novo < self.config['num_grupos_min']:
                num_grupos_novo = self.config['num_grupos_min']
            grupos_ajustados = self._criar_grupos_percentis(df_trabalho, num_grupos_novo)
        
        return grupos_ajustados
    
    def _criar_mapeamento_grupos(self, grupos: List[pd.DataFrame], df_trabalho: pd.DataFrame) -> Dict[str, Any]:
        """Cria o mapeamento final dos grupos com metadados."""
        mapeamento = {
            'grupos': {},
            'estatisticas': {},
            'ranges_score': {}
        }
        
        for grupo in grupos:
            grupo_id = int(grupo['grupo_id'].iloc[0])
            
            # Informações do grupo
            info_grupo = {
                'tamanho': len(grupo),
                'score_min': float(grupo['score_min'].iloc[0]),
                'score_max': float(grupo['score_max'].iloc[0]),
                'score_medio': float(grupo['score_pd'].mean()),
                'score_mediano': float(grupo['score_pd'].median()),
                'score_std': float(grupo['score_pd'].std()),
                'coef_variacao': float(grupo['score_pd'].std() / grupo['score_pd'].mean()) if grupo['score_pd'].mean() != 0 else 0
            }
            
            mapeamento['grupos'][grupo_id] = info_grupo
            mapeamento['ranges_score'][grupo_id] = (info_grupo['score_min'], info_grupo['score_max'])
        mapeamento['estatisticas'] = {
            'num_grupos': len(grupos),
            'total_observacoes': len(df_trabalho),
            'score_range_total': (float(df_trabalho['score_pd'].min()), float(df_trabalho['score_pd'].max())),
            'homogeneidade_media': np.mean([info['coef_variacao'] for info in mapeamento['grupos'].values()]),
            'heterogeneidade_grupos': self._calcular_heterogeneidade(mapeamento['grupos'])
        }
        
        return mapeamento
    
    def _calcular_heterogeneidade(self, grupos_info: Dict) -> float:
        """Calcula heterogeneidade entre grupos."""
        scores_medios = [info['score_medio'] for info in grupos_info.values()]
        if len(scores_medios) <= 1:
            return 0.0
        return float(np.std(scores_medios))
    
    def aplicar_grupos_em_dados(self, df: pd.DataFrame, coluna_score: str = 'score_pd') -> pd.DataFrame:
        """
        Aplica classificação de grupos homogêneos em novos dados.
        
        Args:
            df: DataFrame para classificar
            coluna_score: Nome da coluna com scores de PD
            
        Returns:
            DataFrame com coluna 'grupo_homogeneo' adicionada
        """
        if not self.grupos_mapping:
            raise ValueError("Nenhum grupo foi criado ainda. Execute criar_grupos_homogeneos primeiro.")
        
        df_resultado = df.copy()
        df_resultado['grupo_homogeneo'] = 0  # Grupo padrão para não classificados
        
        if coluna_score not in df_resultado.columns:
            self.logger.warning(f"Coluna '{coluna_score}' não encontrada. Retornando com grupo padrão.")
            return df_resultado
        
        # Aplicar classificação baseada nos ranges de score
        for grupo_id, range_score in self.grupos_mapping['ranges_score'].items():
            score_min, score_max = range_score
            
            if grupo_id == 1:  # Primeiro grupo inclui o mínimo
                mask = (df_resultado[coluna_score] >= score_min) & (df_resultado[coluna_score] <= score_max)
            else:  # Outros grupos excluem o mínimo para evitar sobreposição
                mask = (df_resultado[coluna_score] > score_min) & (df_resultado[coluna_score] <= score_max)
            
            df_resultado.loc[mask, 'grupo_homogeneo'] = grupo_id
        
        # Log de estatísticas
        distribuicao = df_resultado['grupo_homogeneo'].value_counts().sort_index()
        self.logger.info(f"Distribuição por grupos: {distribuicao.to_dict()}")
        
        return df_resultado
    
    def classificar_contratos(self, df: pd.DataFrame, coluna_score: str = 'score_pd') -> np.ndarray:
        """
        Classifica contratos em grupos homogêneos existentes.
        
        Args:
            df: DataFrame com contratos para classificar
            coluna_score: Nome da coluna com scores de PD
            
        Returns:
            Array com IDs dos grupos para cada contrato
        """
        if not self.grupos_mapping:
            raise ValueError("Nenhum grupo foi criado ainda. Execute criar_grupos_homogeneos primeiro.")
        
        if coluna_score not in df.columns:
            self.logger.warning(f"Coluna '{coluna_score}' não encontrada. Retornando grupo padrão (1).")
            return np.ones(len(df), dtype=int)
        
        grupos_atribuidos = np.ones(len(df), dtype=int)  # Grupo padrão
        
        # Classificar baseado nos ranges de score
        for grupo_id, range_score in self.grupos_mapping['ranges_score'].items():
            score_min, score_max = range_score
            
            if grupo_id == 1:  # Primeiro grupo inclui o mínimo
                mask = (df[coluna_score] >= score_min) & (df[coluna_score] <= score_max)
            else:  # Outros grupos excluem o mínimo para evitar sobreposição
                mask = (df[coluna_score] > score_min) & (df[coluna_score] <= score_max)
            
            grupos_atribuidos[mask] = grupo_id
        
        return grupos_atribuidos

    def reagrupar_dinamicamente(self, df: pd.DataFrame, threshold_homogeneidade: Optional[float] = None) -> Dict[str, Any]:
        """
        Reagrupa automaticamente se a homogeneidade dos grupos atuais está comprometida.
        
        Args:
            df: DataFrame com dados atuais para análise
            threshold_homogeneidade: Limite customizado de homogeneidade
            
        Returns:
            Dict com resultados do reagrupamento
        """
        if not self.grupos_mapping:
            raise ValueError("Nenhum grupo foi criado ainda. Execute criar_grupos_homogeneos primeiro.")
        
        # Validar homogeneidade atual
        validacao = self.validar_homogeneidade_grupos(df)
        
        # Usar threshold específico ou padrão
        if threshold_homogeneidade is None:
            threshold_homogeneidade = self.config['threshold_homogeneidade']
        
        # Identificar grupos problemáticos
        grupos_problematicos = []
        for grupo_id, metricas in validacao['homogeneidade_atual'].items():
            if not metricas['conforme']:
                grupos_problematicos.append(grupo_id)
        
        # Se não há problemas e ordenação está correta, não reagrupar
        if not grupos_problematicos and validacao['ordenacao_risco']['ordenacao_correta']:
            self.logger.info("Grupos mantêm homogeneidade. Reagrupamento não necessário.")
            return {'reagrupamento_realizado': False, 'motivo': 'Grupos em conformidade'}
        
        # Salvar grupos atuais no histórico
        self.historico_grupos.append({
            'data': datetime.now().isoformat(),
            'grupos_mapping': self.grupos_mapping.copy(),
            'motivo_mudanca': f"Reagrupamento automático - grupos problemáticos: {grupos_problematicos}"
        })
        
        # Aplicar grupos atuais no DataFrame e recriar
        df_com_grupos = self.aplicar_grupos_em_dados(df)
        
        if 'score_pd' in df_com_grupos.columns:
            # Recriar grupos com configurações atuais
            novo_mapping = self.criar_grupos_homogeneos(
                df_com_grupos, 
                df_com_grupos['score_pd']
            )
            
            self.logger.info(f"Reagrupamento concluído. Novos grupos: {novo_mapping['num_grupos']}")
            
            return {
                'reagrupamento_realizado': True,
                'grupos_anteriores': len(grupos_problematicos),
                'grupos_novos': novo_mapping['num_grupos'],
                'grupos_problematicos': grupos_problematicos
            }
        else:
            self.logger.error("Coluna 'score_pd' não encontrada para reagrupamento")
            return {'reagrupamento_realizado': False, 'motivo': 'Score PD não disponível'}

    def gerar_relatorio(self) -> Optional[Dict[str, Any]]:
        """
        Gera relatório básico dos grupos criados.
        
        Returns:
            Dict com informações dos grupos ou None se não houver grupos
        """
        if not self.grupos_mapping:
            self.logger.warning("Nenhum grupo foi criado ainda.")
            return None
        
        relatorio = {
            'num_grupos': self.grupos_mapping.get('num_grupos', 0),
            'total_observacoes': self.grupos_mapping.get('estatisticas', {}).get('total_observacoes', 0),
            'homogeneidade_media': self.grupos_mapping.get('estatisticas', {}).get('homogeneidade_media', 0),
            'heterogeneidade_grupos': self.grupos_mapping.get('estatisticas', {}).get('heterogeneidade_grupos', 0),
            'metricas_qualidade': self.metricas_validacao if self.metricas_validacao else {}
        }
        
        return relatorio

    def validar_homogeneidade_grupos(self, df: pd.DataFrame, historico_periodos: Optional[int] = None) -> Dict[str, Any]:
        """
        Valida a homogeneidade dos grupos ao longo do tempo.
        
        Args:
            df: DataFrame com dados históricos incluindo período/data
            historico_periodos: Número de períodos históricos para análise
            
        Returns:
            Dict com métricas de validação
        """
        self.logger.info("Iniciando validação de homogeneidade dos grupos")
        
        if not self.grupos_mapping:
            raise ValueError("Nenhum grupo foi criado ainda. Execute criar_grupos_homogeneos primeiro.")
        
        # Aplicar grupos no DataFrame
        df_com_grupos = self.aplicar_grupos_em_dados(df)
        
        validacao = {
            'homogeneidade_atual': {},
            'estabilidade_temporal': {},
            'ordenacao_risco': {},
            'alertas': []
        }
        
        # Validar homogeneidade atual
        for grupo_id in self.grupos_mapping['grupos'].keys():
            dados_grupo = df_com_grupos[df_com_grupos['grupo_homogeneo'] == grupo_id]
            
            if len(dados_grupo) > 0 and 'score_pd' in dados_grupo.columns:
                coef_var = dados_grupo['score_pd'].std() / dados_grupo['score_pd'].mean() if dados_grupo['score_pd'].mean() != 0 else 0
                validacao['homogeneidade_atual'][grupo_id] = {
                    'coef_variacao': float(coef_var),
                    'conforme': bool(coef_var <= self.config['threshold_homogeneidade']),
                    'tamanho_atual': int(len(dados_grupo))
                }
                
                if coef_var > self.config['threshold_homogeneidade']:
                    validacao['alertas'].append(f"Grupo {grupo_id} perdeu homogeneidade (CV: {coef_var:.3f})")
        
        # Validar ordenação de risco (não deve haver cruzamento)
        scores_medios_grupos = []
        for grupo_id in sorted(self.grupos_mapping['grupos'].keys()):
            dados_grupo = df_com_grupos[df_com_grupos['grupo_homogeneo'] == grupo_id]
            if len(dados_grupo) > 0 and 'score_pd' in dados_grupo.columns:
                scores_medios_grupos.append(dados_grupo['score_pd'].mean())
        
        ordenacao_correta = all(scores_medios_grupos[i] <= scores_medios_grupos[i+1] 
                               for i in range(len(scores_medios_grupos)-1))
        
        validacao['ordenacao_risco'] = {
            'ordenacao_correta': bool(ordenacao_correta),
            'scores_medios': [float(score) for score in scores_medios_grupos]
        }
        
        if not ordenacao_correta:
            validacao['alertas'].append("Detectado cruzamento na ordenação de risco entre grupos")
        
        # Salvar métricas
        self.metricas_validacao = validacao
        self._salvar_metricas_validacao()
        
        return validacao
    
    def validar_homogeneidade_woe(self, df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
        """
        Valida a homogeneidade dos grupos baseada em WOE scores.
        
        Args:
            df: DataFrame com dados para validação
            target_col: Coluna target para cálculo do WOE (detectada automaticamente se None)
            
        Returns:
            Dict com métricas de validação WOE
        """
        self.logger.info("Iniciando validação de homogeneidade baseada em WOE")
        
        if not self.grupos_mapping:
            raise ValueError("Nenhum grupo foi criado ainda. Execute criar_grupos_homogeneos primeiro.")
        
        # Aplicar grupos no DataFrame
        df_com_grupos = self.aplicar_grupos_em_dados(df)
        
        # Calcular WOE scores se não existirem
        if not self.woe_scores:
            self.calcular_woe_scores(df_com_grupos, target_col)
        
        validacao_woe = {
            'homogeneidade_woe': {},
            'estabilidade_woe': {},
            'ordenacao_woe': {},
            'alertas_woe': []
        }
        
        # Validar homogeneidade WOE por grupo
        woe_scores_grupos = []
        for grupo_id in sorted(self.grupos_mapping['grupos'].keys()):
            if grupo_id in self.woe_scores:
                woe_info = self.woe_scores[grupo_id]
                woe_score = woe_info.get('WOE_Score', 0)
                total_contratos = woe_info.get('Total_Contratos', 0)
                
                # Verificar se o grupo tem contratos suficientes
                conforme_tamanho = total_contratos >= self.config.get('min_contratos_woe', 30)
                
                validacao_woe['homogeneidade_woe'][grupo_id] = {
                    'woe_score': float(woe_score),
                    'total_contratos': int(total_contratos),
                    'conforme_tamanho': bool(conforme_tamanho)
                }
                
                woe_scores_grupos.append(woe_score)
                
                if not conforme_tamanho:
                    validacao_woe['alertas_woe'].append(
                        f"Grupo {grupo_id} tem poucos contratos para WOE confiável ({total_contratos})"
                    )
        
        # Validar ordenação WOE (deve ser crescente com o risco)
        if len(woe_scores_grupos) > 1:
            ordenacao_woe_correta = all(
                woe_scores_grupos[i] <= woe_scores_grupos[i+1] 
                for i in range(len(woe_scores_grupos)-1)
            )
            
            validacao_woe['ordenacao_woe'] = {
                'ordenacao_correta': bool(ordenacao_woe_correta),
                'woe_scores': [float(score) for score in woe_scores_grupos]
            }
            
            if not ordenacao_woe_correta:
                validacao_woe['alertas_woe'].append(
                    "Detectado cruzamento na ordenação WOE entre grupos"
                )
        
        # Calcular estabilidade WOE (variação entre grupos)
        if len(woe_scores_grupos) > 1:
            variacao_woe = np.std(woe_scores_grupos)
            threshold_variacao = self.config.get('threshold_woe_homogeneidade', 0.5)
            
            validacao_woe['estabilidade_woe'] = {
                'variacao_woe': float(variacao_woe),
                'threshold': float(threshold_variacao),
                'estavel': bool(variacao_woe >= threshold_variacao)
            }
            
            if variacao_woe < threshold_variacao:
                validacao_woe['alertas_woe'].append(
                    f"Baixa variação WOE entre grupos ({variacao_woe:.3f})"
                )
        
        self.logger.info(f"Validação WOE concluída. Alertas: {len(validacao_woe['alertas_woe'])}")
        return validacao_woe
    
    def gerar_relatorio_grupos(self, df: pd.DataFrame, salvar_arquivo: bool = True) -> Dict[str, Any]:
        """
        Gera relatório completo sobre os grupos homogêneos.
        
        Args:
            df: DataFrame com dados para análise
            salvar_arquivo: Se True, salva relatório em arquivo
            
        Returns:
            Dict com relatório completo
        """
        if not self.grupos_mapping:
            raise ValueError("Nenhum grupo foi criado ainda.")
        
        # Aplicar grupos nos dados
        df_com_grupos = self.aplicar_grupos_em_dados(df)
        
        relatorio = {
            'resumo_geral': self.grupos_mapping['estatisticas'].copy(),
            'detalhes_grupos': {},
            'distribuicao_carteira': {},
            'metricas_qualidade': {}
        }
        
        # Análise detalhada por grupo
        for grupo_id in sorted(self.grupos_mapping['grupos'].keys()):
            dados_grupo = df_com_grupos[df_com_grupos['grupo_homogeneo'] == grupo_id]
            
            detalhes = {
                'tamanho': len(dados_grupo),
                'percentual_carteira': len(dados_grupo) / len(df_com_grupos) * 100,
                'score_estatisticas': {},
                'caracteristicas': {}
            }
            
            if len(dados_grupo) > 0:
                # Estatísticas de score
                if 'score_pd' in dados_grupo.columns:
                    detalhes['score_estatisticas'] = {
                        'media': float(dados_grupo['score_pd'].mean()),
                        'mediana': float(dados_grupo['score_pd'].median()),
                        'desvio_padrao': float(dados_grupo['score_pd'].std()),
                        'minimo': float(dados_grupo['score_pd'].min()),
                        'maximo': float(dados_grupo['score_pd'].max()),
                        'coef_variacao': float(dados_grupo['score_pd'].std() / dados_grupo['score_pd'].mean()) if dados_grupo['score_pd'].mean() != 0 else 0
                    }
                
                # Características adicionais (se disponíveis)
                colunas_numericas = dados_grupo.select_dtypes(include=[np.number]).columns
                for col in colunas_numericas:
                    if col not in ['score_pd', 'grupo_homogeneo', 'indice_original']:
                        detalhes['caracteristicas'][col] = {
                            'media': float(dados_grupo[col].mean()) if not dados_grupo[col].isna().all() else None,
                            'mediana': float(dados_grupo[col].median()) if not dados_grupo[col].isna().all() else None
                        }
            
            relatorio['detalhes_grupos'][grupo_id] = detalhes
        
        # Métricas de qualidade
        if self.metricas_validacao:
            relatorio['metricas_qualidade'] = self.metricas_validacao.copy()
        
        # Salvar relatório se solicitado
        if salvar_arquivo:
            from utils.configuracoes_globais import obter_caminho_relatorio_sem_timestamp
            caminho_arquivo = obter_caminho_relatorio_sem_timestamp("relatorio_grupos_homogeneos", "json", is_test=False)
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Relatório salvo em: {caminho_arquivo}")
        
        return relatorio
    
    def processar_dados_reais_completo(
        self, 
        caminho_csv: str, 
        amostra: Optional[int] = None,
        auto_criar_grupos: bool = True,
        config_grupos: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Optional[Dict]]:
        """
        Pipeline completo para processar dados reais e criar grupos homogêneos.
        
        Args:
            caminho_csv: Caminho para arquivo CSV dos dados reais
            amostra: Número de registros para processar
            auto_criar_grupos: Se True, cria grupos automaticamente
            config_grupos: Configuração específica para grupos
            
        Returns:
            Tupla com (dados_processados, grupos_mapping)
        """
        self.logger.info("Iniciando pipeline completo para dados reais")
        
        # Processar dados reais
        dados_processados = self.calculador_pd.processar_dados_completo(caminho_csv, amostra)
        
        grupos_resultado = None
        
        if auto_criar_grupos:
            # Configuração específica para dados reais
            if config_grupos:
                self.config.update(config_grupos)
            
            # Criar grupos homogêneos
            self.logger.info("Criando grupos homogêneos com dados reais...")
            grupos_resultado = self.criar_grupos_homogeneos(dados_processados, dados_processados['score_pd'])
            
            if grupos_resultado:
                self.logger.info(f"✅ {grupos_resultado['num_grupos']} grupos criados com sucesso!")
                
                # Aplicar grupos aos dados
                dados_processados = self.aplicar_grupos_em_dados(dados_processados, 'score_pd')
                
                # Validar homogeneidade
                self.logger.info("Validando homogeneidade dos grupos...")
                metricas = self.validar_homogeneidade_grupos(dados_processados)
                
                # Gerar relatório
                self.logger.info("Gerando relatório dos grupos...")
                relatorio = self.gerar_relatorio_grupos(dados_processados)
                
                # Salvar resultados consolidados
                self._salvar_resultados_completos(dados_processados, grupos_resultado, metricas, relatorio, caminho_csv)
        
        return dados_processados, grupos_resultado
    
    def _salvar_resultados_completos(
        self, 
        dados: pd.DataFrame, 
        grupos: Dict, 
        metricas: Dict, 
        relatorio: Dict,
        arquivo_origem: str
    ):
        """Salva todos os resultados de forma consolidada."""
        from utils.configuracoes_globais import obter_caminho_relatorio_sem_timestamp
        
        # Salvar dados com grupos
        arquivo_dados = obter_caminho_relatorio_sem_timestamp("dados_reais_com_grupos", "csv", is_test=False)
        dados.to_csv(arquivo_dados, index=False)
        self.logger.info(f"Dados com grupos salvos em: {arquivo_dados}")
        
        # Salvar relatório consolidado em texto
        arquivo_relatorio_txt = obter_caminho_relatorio_sem_timestamp("relatorio_grupos_reais", "txt", is_test=False)
        with open(arquivo_relatorio_txt, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE GRUPOS HOMOGÊNEOS - DADOS REAIS (CONSOLIDADO)\n")
            f.write("="*70 + "\n\n")
            f.write(f"Data/Hora: {datetime.now()}\n")
            f.write(f"Arquivo processado: {arquivo_origem}\n")
            f.write(f"Registros processados: {len(dados)}\n")
            f.write(f"Grupos criados: {grupos.get('num_grupos', 0)}\n\n")
            
            f.write("MÉTRICAS DE VALIDAÇÃO:\n")
            f.write("-" * 30 + "\n")
            for metrica, valor in metricas.items():
                f.write(f"{metrica}: {valor}\n")
            
            f.write("\nRELATÓRIO DETALHADO:\n")
            f.write("-" * 30 + "\n")
            f.write(json.dumps(relatorio, indent=2, ensure_ascii=False))
        
        self.logger.info(f"Relatório consolidado salvo em: {arquivo_relatorio_txt}")
    
    def _salvar_grupos_mapping(self):
        """Salva o mapeamento de grupos como artefato."""
        # Salvar como arquivo principal (sem timestamp)
        caminho_arquivo = os.path.join(ARTEFATOS_DIR, 'grupos_homogeneos_mapping.json')
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.grupos_mapping, f, indent=2, ensure_ascii=False)
        
        # Também salvar como 'latest' para compatibilidade
        caminho_latest = os.path.join(ARTEFATOS_DIR, 'grupos_homogeneos_mapping_latest.json')
        with open(caminho_latest, 'w', encoding='utf-8') as f:
            json.dump(self.grupos_mapping, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Mapeamento de grupos salvo em: {caminho_arquivo}")
    
    def _salvar_metricas_validacao(self):
        """Salva métricas de validação como artefato."""
        # Salvar como arquivo principal (sem timestamp)
        caminho_arquivo = os.path.join(ARTEFATOS_DIR, 'metricas_validacao_grupos.json')
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.metricas_validacao, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Métricas de validação salvas em: {caminho_arquivo}")
    
    def calcular_woe_scores(self, dados: pd.DataFrame, grupos: pd.Series, target_col: str = None) -> pd.DataFrame:
        """
        Calcula Weight of Evidence (WOE) por grupo homogêneo conforme documentação técnica.
        
        WOE = ln(% contratos bons / % contratos maus) por grupo homogêneo.
        Usado para suavização dos efeitos de impacto no resultado da PE.
        
        Args:
            dados: DataFrame com os dados dos contratos
            grupos: Series com a classificação de grupos homogêneos
            target_col: Nome da coluna target (default: detecta automaticamente)
            
        Returns:
            DataFrame com colunas WOE_Score e WOE_Score_medio por grupo
        """
        self.logger.info("Calculando Weight of Evidence (WOE) scores por grupo homogêneo...")
        
        try:
            # Preparar dados
            dados_woe = dados.copy()
            dados_woe['grupo_homogeneo'] = grupos
            
            # Definir target de default
            if target_col and target_col in dados_woe.columns:
                target_col_final = target_col
            elif 'default_12m' in dados_woe.columns:
                target_col_final = 'default_12m'
            elif 'estagio' in dados_woe.columns:
                # Usar estágio como proxy (estágio >= 3 = default)
                dados_woe['default_12m'] = (dados_woe['estagio'] >= 3).astype(int)
                target_col_final = 'default_12m'
            else:
                # Criar target sintético baseado em score/atraso
                target_criado = False
                
                # Tentar usar score_credito se disponível
                if 'score_credito' in dados_woe.columns:
                    try:
                        dados_woe['default_12m'] = (dados_woe['score_credito'] < 450).astype(int)
                        target_criado = True
                    except Exception:
                        pass
                
                # Tentar usar atraso_maximo se disponível
                if not target_criado and 'atraso_maximo' in dados_woe.columns:
                    try:
                        dados_woe['default_12m'] = (dados_woe['atraso_maximo'] > 30).astype(int)
                        target_criado = True
                    except Exception:
                        pass
                
                # Último recurso: distribuição aleatória realista
                if not target_criado:
                    np.random.seed(42)  # Para reprodutibilidade
                    dados_woe['default_12m'] = np.random.binomial(1, 0.15, len(dados_woe))
                
                target_col_final = 'default_12m'
            
            resultados_woe = []
            
            # Calcular WOE para cada grupo homogêneo
            for grupo in sorted(dados_woe['grupo_homogeneo'].unique()):
                mask_grupo = dados_woe['grupo_homogeneo'] == grupo
                dados_grupo = dados_woe[mask_grupo]
                
                # Contar bons e maus
                total_grupo = len(dados_grupo)
                maus_grupo = dados_grupo[target_col_final].sum()
                bons_grupo = total_grupo - maus_grupo
                
                # Totais gerais
                total_geral = len(dados_woe)
                maus_geral = dados_woe[target_col_final].sum()
                bons_geral = total_geral - maus_geral
                
                # Evitar divisão por zero
                if bons_grupo == 0:
                    bons_grupo = 0.5
                if maus_grupo == 0:
                    maus_grupo = 0.5
                if bons_geral == 0:
                    bons_geral = 0.5
                if maus_geral == 0:
                    maus_geral = 0.5
                
                # Calcular WOE = ln((% bons grupo / % bons total) / (% maus grupo / % maus total))
                perc_bons_grupo = bons_grupo / bons_geral
                perc_maus_grupo = maus_grupo / maus_geral
                
                if perc_maus_grupo > 0:
                    woe_score = np.log(perc_bons_grupo / perc_maus_grupo)
                else:
                    woe_score = 0.0
                
                # Calcular PD média do grupo (WOE_Score_medio)
                if 'pd_aplicada_para_pe' in dados_grupo.columns:
                    pd_media = dados_grupo['pd_aplicada_para_pe'].mean()
                else:
                    # Usar target como proxy para PD média
                    pd_media = dados_grupo[target_col_final].mean()
                
                resultados_woe.append({
                    'grupo_homogeneo': grupo,
                    'total_contratos': total_grupo,
                    'contratos_bons': bons_grupo,
                    'contratos_maus': maus_grupo,
                    'WOE_Score': woe_score,
                    'WOE_Score_medio': pd_media,
                    'perc_default': maus_grupo / total_grupo if total_grupo > 0 else 0
                })
                
                self.logger.info(f"Grupo {grupo}: WOE_Score={woe_score:.4f}, WOE_Score_medio={pd_media:.4f}")
            
            # Converter para DataFrame
            df_woe = pd.DataFrame(resultados_woe)
            
            # Armazenar WOE scores na instância
            self.woe_scores = df_woe.set_index('grupo_homogeneo').to_dict('index')
            
            # Salvar WOE scores se configurado
            if CONFIG_WOE_INTEGRATION['salvar_woe_scores']:
                self._salvar_woe_scores(df_woe)
            
            self.logger.info(f"WOE scores calculados para {len(df_woe)} grupos homogêneos")
            return df_woe
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular WOE scores: {str(e)}")
            return pd.DataFrame()
    
    def _salvar_woe_scores(self, df_woe: pd.DataFrame):
        """Salva WOE scores como artefato."""
        caminho_arquivo = os.path.join(ARTEFATOS_DIR, 'woe_scores_grupos_homogeneos.json')
        
        # Converter para formato JSON serializável
        woe_dict = df_woe.to_dict('records')
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(woe_dict, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"WOE scores salvos em: {caminho_arquivo}")
    
    def carregar_grupos_existentes(self, caminho_arquivo: Optional[str] = None) -> bool:
        """
        Carrega grupos homogêneos salvos anteriormente.
        
        Args:
            caminho_arquivo: Caminho específico do arquivo. Se None, carrega o mais recente.
            
        Returns:
            True se carregamento foi bem-sucedido
        """
        if caminho_arquivo is None:
            caminho_arquivo = os.path.join(ARTEFATOS_DIR, 'grupos_homogeneos_mapping_latest.json')
        
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                self.grupos_mapping = json.load(f)
            
            self.logger.info(f"Grupos homogêneos carregados de: {caminho_arquivo}")
            return True
        
        except FileNotFoundError:
            self.logger.warning(f"Arquivo de grupos não encontrado: {caminho_arquivo}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao carregar grupos: {str(e)}")
            return False


# Funções de conveniência para compatibilidade
def criar_grupos_homogeneos(
    df: pd.DataFrame, 
    scores_pd: pd.Series, 
    num_grupos_alvo: Optional[int] = None,
    config: Optional[Dict] = None
) -> 'GruposHomogeneosConsolidado':
    """
    Função de conveniência para criar grupos homogêneos.
    
    Args:
        df: DataFrame com dados dos contratos
        scores_pd: Series com scores de PD
        num_grupos_alvo: Número desejado de grupos
        config: Configurações personalizadas
        
    Returns:
        Instância de GruposHomogeneosConsolidado configurada
    """
    sistema_grupos = GruposHomogeneosConsolidado(config)
    sistema_grupos.criar_grupos_homogeneos(df, scores_pd, num_grupos_alvo)
    return sistema_grupos


def validar_homogeneidade_grupos(df: pd.DataFrame, grupos_mapping: Dict) -> Dict[str, Any]:
    """
    Função de conveniência para validar homogeneidade.
    
    Args:
        df: DataFrame com dados
        grupos_mapping: Mapeamento de grupos existente
        
    Returns:
        Dict com métricas de validação
    """
    sistema_grupos = GruposHomogeneosConsolidado()
    sistema_grupos.grupos_mapping = grupos_mapping
    return sistema_grupos.validar_homogeneidade_grupos(df)


def reagrupar_dinamicamente(
    df: pd.DataFrame, 
    grupos_atuais: Dict,
    threshold_homogeneidade: Optional[float] = None
) -> Dict[str, Any]:
    """
    Função de conveniência para reagrupamento dinâmico.
    
    Args:
        df: DataFrame com dados atuais
        grupos_atuais: Mapeamento de grupos existente
        threshold_homogeneidade: Limite para considerar necessário reagrupamento
        
    Returns:
        Dict com resultado do reagrupamento
    """
    sistema_grupos = GruposHomogeneosConsolidado()
    sistema_grupos.grupos_mapping = grupos_atuais
    return sistema_grupos.reagrupar_dinamicamente(df, threshold_homogeneidade)


def aplicar_grupos_homogeneos_dados_reais(caminho_csv: str, amostra: int = 10000) -> None:
    """
    Aplica o sistema de grupos homogêneos aos dados reais da instituição.
    
    Args:
        caminho_csv: Caminho para o arquivo CSV dos dados reais
        amostra: Número de registros para processar (para teste inicial)
    """
    logger = logging.getLogger(__name__)
    
    logger.info("="*80)
    logger.info("APLICAÇÃO DO SISTEMA DE GRUPOS HOMOGÊNEOS EM DADOS REAIS")
    logger.info("="*80)
    
    # Usar a classe consolidada
    sistema_grupos = GruposHomogeneosConsolidado()
    
    # Aplicar grupos nos dados reais usando o pipeline já existente na classe
    logger.info(f"Processando {amostra} registros dos dados reais...")
    
    # Usar o método já existente na classe
    try:
        # Criar dados de teste temporários para demonstração
        import tempfile
        import pandas as pd
        import numpy as np
        
        # Se o arquivo não existir, criar dados sintéticos
        if not os.path.exists(caminho_csv):
            logger.warning(f"Arquivo {caminho_csv} não encontrado. Criando dados sintéticos para demonstração.")
            np.random.seed(42)
            dados_teste = pd.DataFrame({
                'codigo_contrato': range(amostra),
                'limite_pre_aprovado': np.random.uniform(1000, 50000, amostra),
                'renda_comprovada': np.random.uniform(2000, 15000, amostra),
                'idade': np.random.randint(18, 80, amostra),
                'tempo_relacionamento': np.random.randint(1, 240, amostra),
                'numero_operacoes': np.random.randint(1, 50, amostra)
            })
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                dados_teste.to_csv(f.name, index=False)
                caminho_csv = f.name
        
        resultado = sistema_grupos.aplicar_grupos_dados_reais(caminho_csv, amostra)
        logger.info("✅ Aplicação de grupos homogêneos em dados reais concluída!")
        return resultado
        
    except Exception as e:
        logger.error(f"Erro ao aplicar grupos: {e}")
        return None
