# -*- coding: utf-8 -*-
"""
Dados Mock para demonstração do Agente IA
Contém dados fictícios de 1 ano para ECL, PRINAD e Propensão
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# Seed para reprodutibilidade
# Seed removida para garantir variabilidade a cada chamada
# random.seed(42)
# np.random.seed(42)


def gerar_dados_ecl_mensal(meses: int = 12) -> pd.DataFrame:
    """
    Gera dados mensais de ECL (Expected Credit Loss) para 1 ano.
    
    Returns:
        DataFrame com colunas: data, ecl_total, stage_1, stage_2, stage_3, provisao
    """
    base_date = datetime.now().replace(day=1)
    dados = []
    
    # Valores base com tendência e sazonalidade
    ecl_base = random.uniform(2_200_000, 2_800_000)  # Valor base variável
    
    for i in range(meses, 0, -1):
        data = base_date - timedelta(days=30 * i)
        
        # Tendência de crescimento leve
        tendencia = 1 + (random.uniform(0.01, 0.05) * (meses - i) / meses)
        
        # Sazonalidade (mais risco no final do ano)
        mes = data.month
        sazonalidade = 1 + (0.1 if mes in [11, 12, 1] else 0)
        
        # Ruído aleatório
        ruido = random.uniform(0.95, 1.05)
        
        ecl_total = ecl_base * tendencia * sazonalidade * ruido
        
        # Distribuição por stage (baseado em padrões típicos)
        stage_1_pct = random.uniform(0.70, 0.78)
        stage_2_pct = random.uniform(0.15, 0.22)
        stage_3_pct = 1 - stage_1_pct - stage_2_pct
        
        dados.append({
            "data": data.strftime("%Y-%m-%d"),
            "mes_ano": data.strftime("%b/%Y"),
            "ecl_total": round(ecl_total, 2),
            "stage_1": round(ecl_total * stage_1_pct, 2),
            "stage_2": round(ecl_total * stage_2_pct, 2),
            "stage_3": round(ecl_total * stage_3_pct, 2),
            "provisao": round(ecl_total * random.uniform(1.0, 1.15), 2),
            "cobertura_pct": round(random.uniform(100, 115), 1)
        })
    
    return pd.DataFrame(dados)


def gerar_dados_prinad(n_clientes: int = 1000) -> pd.DataFrame:
    """
    Gera dados de classificação PRINAD para clientes.
    
    Returns:
        DataFrame com classificações de risco
    """
    ratings = ["A1-A3", "B1-B3", "C1-C3", "D-H"]
    
    # Randomiza levemente a distribuição
    dist_base = [0.45, 0.30, 0.18, 0.07]
    dist_variation = [random.uniform(0.9, 1.1) for _ in dist_base]
    total = sum(d*v for d, v in zip(dist_base, dist_variation))
    
    distribuicao = {
        "A1-A3": (dist_base[0] * dist_variation[0]) / total,
        "B1-B3": (dist_base[1] * dist_variation[1]) / total,
        "C1-C3": (dist_base[2] * dist_variation[2]) / total,
        "D-H": (dist_base[3] * dist_variation[3]) / total
    }
    
    dados = []
    for rating, pct in distribuicao.items():
        quantidade = int(n_clientes * pct)
        
        # Score médio por rating
        score_ranges = {
            "A1-A3": (800, 900),
            "B1-B3": (650, 799),
            "C1-C3": (500, 649),
            "D-H": (300, 499)
        }
        
        score_min, score_max = score_ranges[rating]
        
        dados.append({
            "rating": rating,
            "quantidade": quantidade,
            "percentual": round(pct * 100, 1),
            "score_medio": round(random.uniform(score_min, score_max), 0),
            "pd_medio": round(random.uniform(0.001, 0.15) if rating != "D-H" else random.uniform(0.15, 0.45), 4),
            "lgd_medio": round(random.uniform(0.30, 0.55), 2),
            "ead_total": round(random.uniform(10_000_000, 50_000_000), 2)
        })
    
    return pd.DataFrame(dados)


def gerar_dados_propensao_mensal(meses: int = 12) -> pd.DataFrame:
    """
    Gera dados mensais de propensão por produto.
    
    Returns:
        DataFrame com propensão por produto e mês
    """
    produtos = ["Crédito Pessoal", "Consignado", "Imobiliário", "Veículos", "Capital de Giro"]
    base_date = datetime.now().replace(day=1)
    dados = []
    
    for i in range(meses, 0, -1):
        data = base_date - timedelta(days=30 * i)
        
        for produto in produtos:
            # Propensão base por produto
            base_propensao = {
                "Crédito Pessoal": 0.72,
                "Consignado": 0.85,
                "Imobiliário": 0.45,
                "Veículos": 0.58,
                "Capital de Giro": 0.65
            }
            
            propensao = base_propensao[produto] * random.uniform(0.90, 1.10)
            
            dados.append({
                "data": data.strftime("%Y-%m-%d"),
                "mes_ano": data.strftime("%b/%Y"),
                "produto": produto,
                "propensao_media": round(propensao * 100, 1),
                "conversao": round(propensao * random.uniform(0.25, 0.40) * 100, 1),
                "clientes_elegíveis": random.randint(500, 3000),
                "receita_potencial": round(random.uniform(100_000, 500_000), 2)
            })
    
    return pd.DataFrame(dados)


def gerar_resumo_portfolio() -> Dict[str, Any]:
    """
    Gera resumo dinâmico do portfólio de crédito.
    """
    return {
        "total_clientes": random.randint(12000, 18000),
        "total_exposicao": round(random.uniform(800_000_000, 950_000_000), 2),
        "ecl_total": round(random.uniform(2_500_000, 3_500_000), 2),
        "cobertura": round(random.uniform(105.0, 125.0), 1),
        "pd_medio": round(random.uniform(0.025, 0.045), 3),
        "lgd_medio": round(random.uniform(0.38, 0.45), 2),
        "auc_roc_prinad": round(random.uniform(0.9900, 0.9999), 4),
        "score_medio": random.randint(720, 760),
        "concentracao_top10": round(random.uniform(0.15, 0.22), 2),
        "inadimplencia_90d": round(random.uniform(0.020, 0.035), 3)
    }


def gerar_clientes_amostra(n: int = 50) -> pd.DataFrame:
    """
    Gera amostra de clientes para análise.
    """
    dados = []
    
    for i in range(n):
        rating = random.choices(
            ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "D", "E", "F", "G", "H"],
            weights=[15, 12, 10, 10, 8, 7, 6, 5, 5, 5, 5, 4, 4, 4]
        )[0]
        
        dados.append({
            "cliente_id": f"CLI{10000 + i}",
            "nome": f"Cliente {i + 1}",
            "rating_prinad": rating,
            "score": random.randint(350, 900),
            "pd": round(random.uniform(0.001, 0.25), 4),
            "lgd": round(random.uniform(0.25, 0.65), 2),
            "ead": round(random.uniform(5000, 500000), 2),
            "ecl": round(random.uniform(100, 50000), 2),
            "stage": random.choices([1, 2, 3], weights=[75, 18, 7])[0],
            "dias_atraso": random.choices([0, 15, 30, 60, 90], weights=[80, 8, 5, 4, 3])[0],
            "propensao": round(random.uniform(0.2, 0.95), 2)
        })
    
    return pd.DataFrame(dados)


# Funções get_ agora chamam diretamente o gerador para garantir dados frescos
# sem cache estático que causava repetição em demonstrações

def get_dados_ecl() -> pd.DataFrame:
    """Retorna dados de ECL frescos."""
    return gerar_dados_ecl_mensal()


def get_dados_prinad() -> pd.DataFrame:
    """Retorna dados de PRINAD frescos."""
    return gerar_dados_prinad()


def get_dados_propensao() -> pd.DataFrame:
    """Retorna dados de Propensão frescos."""
    return gerar_dados_propensao_mensal()


def get_resumo_portfolio() -> Dict[str, Any]:
    """Retorna resumo do portfólio fresco."""
    return gerar_resumo_portfolio()


def get_clientes_amostra(n: int = 50) -> pd.DataFrame:
    """Retorna amostra de clientes fresca."""
    return gerar_clientes_amostra(n)


__all__ = [
    "get_dados_ecl",
    "get_dados_prinad", 
    "get_dados_propensao",
    "get_resumo_portfolio",
    "get_clientes_amostra"
]

__all__ = [
    "get_dados_ecl",
    "get_dados_prinad", 
    "get_dados_propensao",
    "get_resumo_portfolio",
    "get_clientes_amostra"
]
