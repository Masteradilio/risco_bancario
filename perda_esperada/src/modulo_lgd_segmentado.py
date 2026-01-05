#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LGD SEGMENTADO POR ÁRVORE DE DECISÃO
===================================

Implementa cálculo de Loss Given Default (LGD) baseado em árvore de decisão
conforme documentação técnica, com segmentação específica por características
do contrato e tipo de produto.

Funcionalidades principais:
- Segmentação de LGD para produtos rotativos
- Segmentação de LGD para produtos parcelados  
- Segmentação de LGD para produtos consignados
- Incorporação de custos de recuperação por grupo homogêneo

Baseado na documentação técnica "Documentação Técnica de Perda 4966 - BIP.pdf"
e nas especificações das Resoluções CMN nº 4.966 e BCB nº 352.

Autor: Sistema ECL - Expected Credit Loss
Data: 31 de maio de 2025
"""

import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LGDSegmentado:
    """
    Classe para implementar LGD segmentado por árvore de decisão.
    
    Implementa segmentação específica por modalidade de crédito,
    faixa de atraso, valor original e outras características relevantes.
    """
    
    def __init__(self):
        """Inicializa o sistema de LGD segmentado."""
        self.lgd_rotativos = self._definir_lgd_rotativos()
        self.lgd_parcelados = self._definir_lgd_parcelados()
        self.lgd_consignado = self._definir_lgd_consignado()
        self.custos_recuperacao = self._definir_custos_recuperacao()
        
        logger.info("Sistema LGD Segmentado inicializado")
        
    def _definir_lgd_rotativos(self) -> Dict:
        """
        Define matriz de LGD para produtos rotativos conforme documentação técnica.
        
        Segmentação por:
        - Faixa de atraso: 0-120, 120-210, >210 dias
        - Valor original: <R$500, ≥R$500
        
        Valores conforme Tabela 33 da documentação técnica.
        """
        return {
            "0-120": {
                "menor_500": 0.1951,    # 19,51% - GH 10
                "maior_igual_500": 0.2942  # 29,42% - GH 11
            },
            "120-210": {
                "menor_500": 0.2731,    # 27,31% - GH 12
                "maior_igual_500": 0.4052  # 40,52% - GH 13
            },
            "maior_210": 0.5720         # 57,20% - GH 14 (independente do valor)
        }
    
    def _definir_lgd_parcelados(self) -> Dict:
        """
        Define matriz de LGD para produtos parcelados conforme documentação técnica.
        
        Segmentação por:
        - Faixa de atraso: 0-120, 120-210, >210 dias
        - Prazo: <360 dias, ≥360 dias
        
        Valores conforme Tabela 33 da documentação técnica.
        """
        return {
            "0-120": {
                "menor_360_dias": 0.4780,    # 47,80% - GH 6
                "maior_igual_360_dias": 0.6332  # 63,32% - GH 7
            },
            "120-210": 0.7891,    # 78,91% - GH 8 (independente do prazo)
            "maior_210": 0.9050   # 90,50% - GH 9 (independente do prazo)
        }
    
    def _definir_lgd_consignado(self) -> Dict:
        """
        Define matriz de LGD para produtos consignados conforme documentação técnica.
        
        Segmentação por:
        - Faixa de atraso: 0-120, 120-210, >210 dias
        - Ocupação: Servidor Público vs. Outras
        
        Valores conforme Tabela 33 da documentação técnica.
        """
        return {
            "0-120": 0.4251,    # 42,51% - GH 1 (independente da ocupação)
            "120-210": {
                "servidor_publico": 0.7185,    # 71,85% - GH 3
                "outras_ocupacoes": 0.8002      # 80,02% - GH 2
            },
            "maior_210": {
                "servidor_publico": 0.8820,    # 88,20% - GH 5
                "outras_ocupacoes": 0.9058      # 90,58% - GH 4
            }
        }
    
    def _definir_custos_recuperacao(self) -> Dict:
        """
        Define fatores de custo de recuperação por grupo homogêneo.
        
        Custos incluem: SMS, chamadas, comissões de cobrança.
        Fatores conforme tabela de custos da documentação técnica.
        """
        return {
            1: 1.007,   # GH 1 - Consignado 0-120
            2: 1.007,   # GH 2 - Consignado 120-210 Outras Ocupações
            3: 1.005,   # GH 3 - Consignado 120-210 Servidor Público
            4: 1.005,   # GH 4 - Consignado >210 Outras Ocupações
            5: 1.005,   # GH 5 - Consignado >210 Servidor Público
            6: 1.006,   # GH 6 - Parcelados 0-120 <360 dias
            7: 1.006,   # GH 7 - Parcelados 0-120 >=360 dias
            8: 1.009,   # GH 8 - Parcelados 120-210
            9: 1.007,   # GH 9 - Parcelados >210
            10: 1.005,  # GH 10 - Rotativos 0-120 <500
            11: 1.005,  # GH 11 - Rotativos 0-120 >=500
            12: 1.007,  # GH 12 - Rotativos 120-210 <500
            13: 1.007,  # GH 13 - Rotativos 120-210 >=500
            14: 1.007   # GH 14 - Rotativos >210
        }
    
    def segmentar_lgd_rotativos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Segmenta LGD para produtos rotativos.
        
        Args:
            df: DataFrame com contratos rotativos
            
        Returns:
            DataFrame com coluna 'lgd_segmentado' adicionada
        """
        logger.info("Iniciando segmentação de LGD para produtos rotativos...")
        
        df_resultado = df.copy()
        
        # Definir faixa de atraso
        df_resultado['faixa_atraso'] = df_resultado['dias_em_atraso'].apply(
            self._classificar_faixa_atraso
        )
        
        # Definir faixa de valor
        df_resultado['faixa_valor'] = df_resultado['valor_original'].apply(
            lambda x: 'menor_500' if x < 500 else 'maior_igual_500'
        )
        
        # Aplicar LGD específico
        def aplicar_lgd_rotativo(row):
            faixa_atraso = row['faixa_atraso']
            faixa_valor = row['faixa_valor']
            
            if faixa_atraso == 'maior_210':
                return self.lgd_rotativos[faixa_atraso]
            else:
                return self.lgd_rotativos[faixa_atraso][faixa_valor]
        
        df_resultado['lgd_segmentado'] = df_resultado.apply(aplicar_lgd_rotativo, axis=1)
        
        # Estatísticas
        stats = self._calcular_estatisticas_lgd(df_resultado, 'rotativos')
        logger.info(f"Segmentação rotativos concluída: {stats}")
        
        return df_resultado
    
    def segmentar_lgd_parcelados(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Segmenta LGD para produtos parcelados.
        
        Args:
            df: DataFrame com contratos parcelados
            
        Returns:
            DataFrame com coluna 'lgd_segmentado' adicionada
        """
        logger.info("Iniciando segmentação de LGD para produtos parcelados...")
        
        df_resultado = df.copy()
        
        # Definir faixa de atraso
        df_resultado['faixa_atraso'] = df_resultado['dias_em_atraso'].apply(
            self._classificar_faixa_atraso
        )
        
        # Definir faixa de prazo
        df_resultado['faixa_prazo'] = df_resultado['prazo_original_dias'].apply(
            lambda x: 'menor_360_dias' if x < 360 else 'maior_igual_360_dias'
        )
        
        # Aplicar LGD específico
        def aplicar_lgd_parcelado(row):
            faixa_atraso = row['faixa_atraso']
            faixa_prazo = row['faixa_prazo']
            
            if faixa_atraso == '0-120':
                return self.lgd_parcelados[faixa_atraso][faixa_prazo]
            else:
                # Para 120-210 e >210, LGD é independente do prazo
                return self.lgd_parcelados[faixa_atraso]
        
        df_resultado['lgd_segmentado'] = df_resultado.apply(aplicar_lgd_parcelado, axis=1)
        
        # Estatísticas
        stats = self._calcular_estatisticas_lgd(df_resultado, 'parcelados')
        logger.info(f"Segmentação parcelados concluída: {stats}")
        
        return df_resultado
    
    def segmentar_lgd_consignado(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Segmenta LGD para produtos consignados.
        
        Args:
            df: DataFrame com contratos consignados
            
        Returns:
            DataFrame com coluna 'lgd_segmentado' adicionada
        """
        logger.info("Iniciando segmentação de LGD para produtos consignados...")
        
        df_resultado = df.copy()
        
        # Definir faixa de atraso
        df_resultado['faixa_atraso'] = df_resultado['dias_em_atraso'].apply(
            self._classificar_faixa_atraso
        )
        
        # Definir tipo de ocupação
        df_resultado['tipo_ocupacao'] = df_resultado['ocupacao'].apply(
            lambda x: 'servidor_publico' if 'servidor' in str(x).lower() or 'publico' in str(x).lower() 
            else 'outras_ocupacoes'
        )
        
        # Aplicar LGD específico
        def aplicar_lgd_consignado(row):
            faixa_atraso = row['faixa_atraso']
            tipo_ocupacao = row['tipo_ocupacao']
            
            if faixa_atraso == '0-120':
                # Para 0-120, LGD é independente da ocupação
                return self.lgd_consignado[faixa_atraso]
            else:
                # Para 120-210 e >210, LGD depende da ocupação
                return self.lgd_consignado[faixa_atraso][tipo_ocupacao]
        
        df_resultado['lgd_segmentado'] = df_resultado.apply(aplicar_lgd_consignado, axis=1)
        
        # Estatísticas
        stats = self._calcular_estatisticas_lgd(df_resultado, 'consignado')
        logger.info(f"Segmentação consignado concluída: {stats}")
        
        return df_resultado
    
    def incorporar_custos_recuperacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Incorpora custos de recuperação baseados no grupo homogêneo determinado
        pelas características do contrato (tipo produto, faixa atraso, etc.).
        
        Args:
            df: DataFrame com LGD segmentado e características
            
        Returns:
            DataFrame com 'lgd_final' incluindo custos
        """
        logger.info("Incorporando custos de recuperação por grupo homogêneo...")
        
        df_resultado = df.copy()
        
        # Determinar grupo homogêneo baseado nas características
        def determinar_grupo_homogeneo(row):
            tipo_produto = row['tipo_produto']
            faixa_atraso = row['faixa_atraso']
            
            if tipo_produto == 'consignado':
                if faixa_atraso == '0-120':
                    return 1  # GH 1
                elif faixa_atraso == '120-210':
                    if row.get('tipo_ocupacao') == 'servidor_publico':
                        return 3  # GH 3
                    else:
                        return 2  # GH 2
                else:  # maior_210
                    if row.get('tipo_ocupacao') == 'servidor_publico':
                        return 5  # GH 5
                    else:
                        return 4  # GH 4
            elif tipo_produto in ['parcelado', 'financiamento']:
                if faixa_atraso == '0-120':
                    if row.get('faixa_prazo') == 'menor_360_dias':
                        return 6  # GH 6
                    else:
                        return 7  # GH 7
                elif faixa_atraso == '120-210':
                    return 8  # GH 8
                else:  # maior_210
                    return 9  # GH 9
            else:  # rotativos
                if faixa_atraso == '0-120':
                    if row.get('faixa_valor') == 'menor_500':
                        return 10  # GH 10
                    else:
                        return 11  # GH 11
                elif faixa_atraso == '120-210':
                    if row.get('faixa_valor') == 'menor_500':
                        return 12  # GH 12
                    else:
                        return 13  # GH 13
                else:  # maior_210
                    return 14  # GH 14
        
        df_resultado['grupo_homogeneo'] = df_resultado.apply(determinar_grupo_homogeneo, axis=1)
        
        # Aplicar fator de custo
        def aplicar_custo_recuperacao(row):
            grupo = int(row['grupo_homogeneo'])
            lgd_base = row['lgd_segmentado']
            fator_custo = self.custos_recuperacao.get(grupo, 1.007)  # Default para grupo médio
            
            return min(lgd_base * fator_custo, 1.0)  # LGD não pode exceder 100%
        
        df_resultado['lgd_final'] = df_resultado.apply(aplicar_custo_recuperacao, axis=1)
        
        # Estatísticas dos custos
        custo_medio = (df_resultado['lgd_final'] / df_resultado['lgd_segmentado']).mean()
        logger.info(f"Custo médio de recuperação aplicado: {custo_medio:.1%}")
        
        return df_resultado
    
    def _classificar_faixa_atraso(self, dias_atraso: int) -> str:
        """Classifica faixa de atraso conforme critérios técnicos."""
        if dias_atraso <= 120:
            return "0-120"
        elif dias_atraso <= 210:
            return "120-210"
        else:
            return "maior_210"
    
    def _calcular_estatisticas_lgd(self, df: pd.DataFrame, tipo_produto: str) -> Dict:
        """Calcula estatísticas da segmentação de LGD."""
        return {
            "contratos_processados": len(df),
            "lgd_medio": f"{df['lgd_segmentado'].mean():.2%}",
            "lgd_min": f"{df['lgd_segmentado'].min():.2%}",
            "lgd_max": f"{df['lgd_segmentado'].max():.2%}",
            "faixas_atraso": df['faixa_atraso'].value_counts().to_dict(),
            "tipo_produto": tipo_produto
        }
    
    def aplicar_lgd_completo(self, df: pd.DataFrame, grupos_homogeneos: pd.Series = None) -> pd.DataFrame:
        """
        Aplica LGD segmentado completo baseado no tipo de produto.
        
        Args:
            df: DataFrame com contratos de diferentes tipos
            grupos_homogeneos: Série com grupos homogêneos (opcional, será determinado automaticamente se não fornecido)
            
        Returns:
            DataFrame com LGD final aplicado
        """
        logger.info("Aplicando LGD segmentado completo por tipo de produto...")
        
        resultados = []
        
        # Processar cada tipo de produto
        produtos = df['tipo_produto'].unique()
        for produto in produtos:
            mask = df['tipo_produto'] == produto
            df_produto = df[mask].copy()
            
            if produto in ['cartao', 'cheque_especial', 'conta_garantia']:
                # Produtos rotativos
                df_segmentado = self.segmentar_lgd_rotativos(df_produto)
            elif produto in ['parcelado', 'financiamento']:
                # Produtos parcelados
                df_segmentado = self.segmentar_lgd_parcelados(df_produto)
            elif produto == 'consignado':
                # Produtos consignados
                df_segmentado = self.segmentar_lgd_consignado(df_produto)
            else:
                # Produto não mapeado - usar LGD padrão
                logger.warning(f"Produto não mapeado: {produto}. Usando LGD padrão.")
                df_segmentado = df_produto.copy()
                df_segmentado['lgd_segmentado'] = 0.30  # 30% padrão
            
            # Incorporar custos de recuperação
            df_final = self.incorporar_custos_recuperacao(df_segmentado)
            resultados.append(df_final)
        
        # Consolidar resultados
        df_consolidado = pd.concat(resultados, ignore_index=True)
        
        # Estatísticas finais
        stats_finais = {
            "total_contratos": len(df_consolidado),
            "lgd_medio_final": f"{df_consolidado['lgd_final'].mean():.2%}",
            "produtos_processados": list(produtos),
            "range_lgd": f"{df_consolidado['lgd_final'].min():.2%} - {df_consolidado['lgd_final'].max():.2%}"
        }
        
        logger.info(f"LGD segmentado aplicado: {stats_finais}")
        
        return df_consolidado
    
    def salvar_resultados(self, df_resultado: pd.DataFrame, nome_arquivo: str = None) -> str:
        """
        Salva resultados da segmentação LGD em arquivo JSON.
        
        Args:
            df_resultado: DataFrame com resultados
            nome_arquivo: Nome customizado do arquivo (opcional)
            
        Returns:
            Caminho do arquivo salvo
        """
        if nome_arquivo is None:
            nome_arquivo = "lgd_segmentado_resultados.json"
        
        # Preparar dados para salvar
        resultados = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_contratos": len(df_resultado),
                "colunas": list(df_resultado.columns)
            },
            "estatisticas": {
                "lgd_medio": df_resultado['lgd_final'].mean(),
                "lgd_std": df_resultado['lgd_final'].std(),
                "lgd_min": df_resultado['lgd_final'].min(),
                "lgd_max": df_resultado['lgd_final'].max()
            },
            "distribuicao_por_produto": df_resultado.groupby('tipo_produto')['lgd_final'].agg(['mean', 'count']).to_dict(),
            "distribuicao_por_grupo": df_resultado.groupby('grupo_homogeneo')['lgd_final'].agg(['mean', 'count']).to_dict()
        }
        
        # Salvar arquivo usando estrutura padronizada
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from utils.configuracoes_globais import OUTPUT_DIR_MODULOS_JSON
        caminho_arquivo = os.path.join(OUTPUT_DIR_MODULOS_JSON, nome_arquivo)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Resultados LGD segmentado salvos em: {caminho_arquivo}")
        return str(caminho_arquivo)

def main():
    """Função principal para teste do sistema LGD segmentado."""
    print("🧪 TESTANDO SISTEMA LGD SEGMENTADO")
    print("="*50)
    
    # Instanciar sistema
    lgd_sistema = LGDSegmentado()
    
    # Gerar dados de teste
    np.random.seed(42)
    n_contratos = 1000
    
    dados_teste = {
        'id_contrato': range(1, n_contratos + 1),
        'tipo_produto': np.random.choice(['cartao', 'parcelado', 'consignado', 'cheque_especial'], n_contratos),
        'dias_em_atraso': np.random.exponential(60, n_contratos).astype(int),
        'valor_original': np.random.lognormal(6, 1, n_contratos),
        'prazo_original_dias': np.random.choice([180, 360, 720, 1080], n_contratos),
        'ocupacao': np.random.choice(['servidor_publico', 'autonomo', 'clt', 'aposentado'], n_contratos)
    }
    
    df_teste = pd.DataFrame(dados_teste)
    grupos_teste = pd.Series(np.random.randint(1, 6, n_contratos))
    
    print(f"📊 Dados de teste gerados: {len(df_teste)} contratos")
    print(f"   Produtos: {df_teste['tipo_produto'].value_counts().to_dict()}")
    
    # Aplicar LGD segmentado completo
    resultado = lgd_sistema.aplicar_lgd_completo(df_teste)
    
    # Salvar resultados
    arquivo_salvo = lgd_sistema.salvar_resultados(resultado)
    
    print(f"\n✅ Teste concluído com sucesso!")
    print(f"📁 Resultados salvos em: {arquivo_salvo}")
    
    return True

if __name__ == "__main__":
    main()
