# -*- coding: utf-8 -*-
"""
Ferramentas PRINAD - Consulta de Score de Risco
"""

from typing import Dict, Any
import logging
import random

logger = logging.getLogger(__name__)


def consultar_score_prinad(cpf_cnpj: str) -> Dict[str, Any]:
    """
    Consulta score PRINAD de um cliente.
    
    Args:
        cpf_cnpj: CPF ou CNPJ do cliente
        
    Returns:
        Dicionário com score e classificação
    """
    # Mock - Em produção, consultar API PRINAD real
    # Gerar score baseado no hash do CPF para consistência
    hash_val = hash(cpf_cnpj) % 1000
    score = 300 + (hash_val % 700)  # Score entre 300 e 999
    
    # Classificar rating
    if score >= 900:
        rating = "AAA"
        pd = 0.001
        descricao = "Risco muito baixo"
    elif score >= 800:
        rating = "AA"
        pd = 0.005
        descricao = "Risco baixo"
    elif score >= 700:
        rating = "A"
        pd = 0.02
        descricao = "Risco baixo a moderado"
    elif score >= 600:
        rating = "BBB"
        pd = 0.05
        descricao = "Risco moderado"
    elif score >= 500:
        rating = "BB"
        pd = 0.10
        descricao = "Risco moderado a alto"
    elif score >= 400:
        rating = "B"
        pd = 0.20
        descricao = "Risco alto"
    else:
        rating = "C"
        pd = 0.40
        descricao = "Risco muito alto"
    
    return {
        "cpf_cnpj": cpf_cnpj,
        "score": score,
        "rating": rating,
        "pd_estimado": f"{pd * 100:.2f}%",
        "classificacao": descricao,
        "data_consulta": "2026-01-18",
        "modelo": "PRINAD v2.5",
        "fonte_dados": ["SCR", "Cadastro Interno", "Comportamento"]
    }


def classificar_risco_cliente(dados_cliente: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classifica risco de crédito de um cliente.
    
    Args:
        dados_cliente: Dicionário com dados do cliente
        
    Returns:
        Classificação completa de risco
    """
    # Mock - Em produção, usar modelo real
    cpf_cnpj = dados_cliente.get("cpf_cnpj", "00000000000")
    renda = dados_cliente.get("renda_mensal", 5000)
    tempo_relacionamento = dados_cliente.get("tempo_relacionamento_meses", 12)
    
    # Calcular score base
    score_base = 500
    
    # Ajustes
    if renda > 10000:
        score_base += 100
    elif renda > 5000:
        score_base += 50
    
    if tempo_relacionamento > 24:
        score_base += 80
    elif tempo_relacionamento > 12:
        score_base += 40
    
    # Adicionar variação
    score_final = min(999, max(300, score_base + random.randint(-50, 50)))
    
    return {
        "cpf_cnpj": cpf_cnpj,
        "score_final": score_final,
        "componentes": {
            "renda": "alto" if renda > 10000 else "medio" if renda > 5000 else "baixo",
            "relacionamento": "longo" if tempo_relacionamento > 24 else "medio",
            "comportamento": "positivo"
        },
        "limite_sugerido": renda * 3,
        "recomendacao": "aprovado" if score_final >= 600 else "analise_manual"
    }


# Schema das ferramentas para o LLM
PRINAD_TOOLS = [
    {
        "name": "consultar_score_prinad",
        "description": "Consulta o score de risco PRINAD de um cliente pelo CPF ou CNPJ. Retorna score numérico, rating (AAA a C), probabilidade de default e classificação de risco.",
        "parameters": {
            "type": "object",
            "properties": {
                "cpf_cnpj": {
                    "type": "string",
                    "description": "CPF (11 dígitos) ou CNPJ (14 dígitos) do cliente"
                }
            },
            "required": ["cpf_cnpj"]
        }
    },
    {
        "name": "classificar_risco_cliente",
        "description": "Realiza classificação completa de risco de crédito de um cliente com base em seus dados cadastrais e comportamentais.",
        "parameters": {
            "type": "object",
            "properties": {
                "dados_cliente": {
                    "type": "object",
                    "description": "Dados do cliente incluindo cpf_cnpj, renda_mensal, tempo_relacionamento_meses",
                    "properties": {
                        "cpf_cnpj": {"type": "string"},
                        "renda_mensal": {"type": "number"},
                        "tempo_relacionamento_meses": {"type": "integer"}
                    }
                }
            },
            "required": ["dados_cliente"]
        }
    }
]


__all__ = [
    "consultar_score_prinad",
    "classificar_risco_cliente",
    "PRINAD_TOOLS"
]
