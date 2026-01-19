# -*- coding: utf-8 -*-
"""
Ferramentas ECL - Cálculo de Perda Esperada
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
import random

logger = logging.getLogger(__name__)


def calcular_ecl_individual(
    contrato_id: str,
    saldo: float = None,
    pd: float = None,
    lgd: float = None,
    estagio: int = None
) -> Dict[str, Any]:
    """
    Calcula ECL para um contrato individual.
    
    Args:
        contrato_id: ID do contrato
        saldo: Saldo do contrato (opcional, busca do sistema)
        pd: Probabilidade de default (opcional)
        lgd: Loss Given Default (opcional)
        estagio: Estágio IFRS 9 (1, 2 ou 3)
        
    Returns:
        Cálculo detalhado de ECL
    """
    # Mock - Em produção, buscar dados reais
    saldo = saldo or random.uniform(10000, 500000)
    pd = pd or random.uniform(0.01, 0.15)
    lgd = lgd or 0.45  # LGD padrão
    estagio = estagio or (1 if pd < 0.05 else 2 if pd < 0.15 else 3)
    
    # Calcular horizonte
    if estagio == 1:
        horizonte = "12m"
        pd_aplicado = pd
    else:
        horizonte = "lifetime"
        pd_aplicado = min(pd * 3, 1.0)  # PD lifetime simplificado
    
    # CCF (Credit Conversion Factor)
    ccf = 0.75
    ead = saldo * ccf
    
    # Calcular ECL
    ecl = ead * pd_aplicado * lgd
    
    # Aplicar piso mínimo CMN 4966
    piso_minimo = saldo * 0.005  # 0.5% como piso
    ecl_final = max(ecl, piso_minimo)
    piso_aplicado = ecl < piso_minimo
    
    return {
        "contrato_id": contrato_id,
        "estagio": estagio,
        "horizonte": horizonte,
        "saldo": round(saldo, 2),
        "ead": round(ead, 2),
        "pd": f"{pd * 100:.2f}%",
        "pd_aplicado": f"{pd_aplicado * 100:.2f}%",
        "lgd": f"{lgd * 100:.0f}%",
        "ccf": ccf,
        "ecl_calculado": round(ecl, 2),
        "ecl_final": round(ecl_final, 2),
        "piso_aplicado": piso_aplicado,
        "provisao_percentual": f"{(ecl_final/saldo)*100:.2f}%",
        "data_calculo": datetime.now().isoformat(),
        "conformidade": "CMN 4966 / IFRS 9"
    }


def calcular_ecl_portfolio(
    carteira: str = None,
    data_base: str = None
) -> Dict[str, Any]:
    """
    Calcula ECL agregado do portfólio.
    
    Args:
        carteira: Tipo de carteira (PF, PJ, Consignado, etc)
        data_base: Data base do cálculo
        
    Returns:
        ECL agregado do portfólio
    """
    # Mock de portfólio
    carteira = carteira or "Consolidado"
    data_base = data_base or datetime.now().strftime("%Y-%m-%d")
    
    saldo_total = random.uniform(100_000_000, 500_000_000)
    
    # Distribuição por estágio
    stage1_pct = 0.85 + random.uniform(-0.05, 0.05)
    stage2_pct = 0.12 + random.uniform(-0.03, 0.03)
    stage3_pct = 1 - stage1_pct - stage2_pct
    
    # ECL por estágio
    ecl_stage1 = saldo_total * stage1_pct * 0.005
    ecl_stage2 = saldo_total * stage2_pct * 0.08
    ecl_stage3 = saldo_total * stage3_pct * 0.45
    ecl_total = ecl_stage1 + ecl_stage2 + ecl_stage3
    
    return {
        "carteira": carteira,
        "data_base": data_base,
        "saldo_total": round(saldo_total, 2),
        "ecl_total": round(ecl_total, 2),
        "cobertura_ecl": f"{(ecl_total/saldo_total)*100:.2f}%",
        "distribuicao_estagios": {
            "stage_1": {
                "percentual": f"{stage1_pct*100:.1f}%",
                "saldo": round(saldo_total * stage1_pct, 2),
                "ecl": round(ecl_stage1, 2)
            },
            "stage_2": {
                "percentual": f"{stage2_pct*100:.1f}%",
                "saldo": round(saldo_total * stage2_pct, 2),
                "ecl": round(ecl_stage2, 2)
            },
            "stage_3": {
                "percentual": f"{stage3_pct*100:.1f}%",
                "saldo": round(saldo_total * stage3_pct, 2),
                "ecl": round(ecl_stage3, 2)
            }
        },
        "total_contratos": random.randint(50000, 150000),
        "metodologia": "IFRS 9 / CMN 4966"
    }


def consultar_ecl_contrato(contrato_id: str) -> Dict[str, Any]:
    """
    Consulta ECL já calculado de um contrato.
    
    Args:
        contrato_id: ID do contrato
        
    Returns:
        Dados de ECL do contrato
    """
    # Mock
    return calcular_ecl_individual(contrato_id)


def simular_cenario_forward_looking(
    cenario: str,
    variacao_pib: float = None,
    variacao_selic: float = None,
    variacao_desemprego: float = None
) -> Dict[str, Any]:
    """
    Simula impacto de cenário macroeconômico no ECL.
    
    Args:
        cenario: Nome do cenário (base, otimista, pessimista, stress)
        variacao_pib: Variação do PIB em pontos percentuais
        variacao_selic: Variação da Selic em pontos percentuais
        variacao_desemprego: Variação do desemprego em pontos percentuais
        
    Returns:
        Impacto no ECL
    """
    cenarios_padrao = {
        "base": {"pib": 2.5, "selic": 11.25, "desemprego": 7.5, "peso": 0.50},
        "otimista": {"pib": 4.0, "selic": 9.50, "desemprego": 6.0, "peso": 0.20},
        "pessimista": {"pib": 0.5, "selic": 14.00, "desemprego": 10.0, "peso": 0.25},
        "stress": {"pib": -2.0, "selic": 18.00, "desemprego": 14.0, "peso": 0.05}
    }
    
    cenario_lower = cenario.lower()
    if cenario_lower in cenarios_padrao:
        params = cenarios_padrao[cenario_lower]
    else:
        params = {"pib": variacao_pib or 2.0, "selic": variacao_selic or 11.0, "desemprego": variacao_desemprego or 8.0, "peso": 0.25}
    
    # Calcular fator de ajuste
    # Piora com menor PIB, maior Selic, maior desemprego
    fator_pib = 1 + (2.5 - params["pib"]) * 0.03
    fator_selic = 1 + (params["selic"] - 11.25) * 0.01
    fator_desemprego = 1 + (params["desemprego"] - 7.5) * 0.02
    
    k_fl = fator_pib * fator_selic * fator_desemprego
    
    # ECL base simulado
    ecl_base = 50_000_000
    ecl_ajustado = ecl_base * k_fl
    
    return {
        "cenario": cenario,
        "parametros": {
            "pib": f"{params['pib']:.1f}%",
            "selic": f"{params['selic']:.2f}%",
            "desemprego": f"{params['desemprego']:.1f}%"
        },
        "peso_cenario": f"{params['peso']*100:.0f}%",
        "fator_ajuste_fl": round(k_fl, 4),
        "componentes_k": {
            "k_pib": round(fator_pib, 4),
            "k_selic": round(fator_selic, 4),
            "k_desemprego": round(fator_desemprego, 4)
        },
        "ecl_base": round(ecl_base, 2),
        "ecl_ajustado": round(ecl_ajustado, 2),
        "variacao_ecl": f"{((ecl_ajustado/ecl_base)-1)*100:.2f}%",
        "metodologia": "Forward Looking CMN 4966 Art. 21"
    }


# Schema das ferramentas
ECL_TOOLS = [
    {
        "name": "calcular_ecl_individual",
        "description": "Calcula a Perda Esperada (ECL) para um contrato individual conforme IFRS 9 e CMN 4966. Considera estágio, PD, LGD, EAD e aplica pisos mínimos regulatórios.",
        "parameters": {
            "type": "object",
            "properties": {
                "contrato_id": {
                    "type": "string",
                    "description": "ID do contrato"
                },
                "saldo": {
                    "type": "number",
                    "description": "Saldo do contrato (opcional)"
                },
                "pd": {
                    "type": "number",
                    "description": "Probabilidade de default entre 0 e 1 (opcional)"
                },
                "lgd": {
                    "type": "number",
                    "description": "Loss Given Default entre 0 e 1 (opcional, padrão 0.45)"
                },
                "estagio": {
                    "type": "integer",
                    "description": "Estágio IFRS 9: 1, 2 ou 3 (opcional)"
                }
            },
            "required": ["contrato_id"]
        }
    },
    {
        "name": "calcular_ecl_portfolio",
        "description": "Calcula ECL agregado do portfólio de crédito, com distribuição por estágios (Stage 1, 2, 3) e cobertura de provisão.",
        "parameters": {
            "type": "object",
            "properties": {
                "carteira": {
                    "type": "string",
                    "description": "Tipo de carteira: PF, PJ, Consignado, Imobiliário, etc"
                },
                "data_base": {
                    "type": "string",
                    "description": "Data base do cálculo (YYYY-MM-DD)"
                }
            },
            "required": []
        }
    },
    {
        "name": "consultar_ecl_contrato",
        "description": "Consulta o ECL já calculado de um contrato específico.",
        "parameters": {
            "type": "object",
            "properties": {
                "contrato_id": {
                    "type": "string",
                    "description": "ID do contrato"
                }
            },
            "required": ["contrato_id"]
        }
    },
    {
        "name": "simular_cenario_forward_looking",
        "description": "Simula o impacto de cenários macroeconômicos no ECL, aplicando fatores de ajuste Forward Looking conforme CMN 4966.",
        "parameters": {
            "type": "object",
            "properties": {
                "cenario": {
                    "type": "string",
                    "description": "Nome do cenário: base, otimista, pessimista ou stress"
                },
                "variacao_pib": {
                    "type": "number",
                    "description": "Variação do PIB em pontos percentuais"
                },
                "variacao_selic": {
                    "type": "number",
                    "description": "Taxa Selic em pontos percentuais"
                },
                "variacao_desemprego": {
                    "type": "number",
                    "description": "Taxa de desemprego em pontos percentuais"
                }
            },
            "required": ["cenario"]
        }
    }
]


__all__ = [
    "calcular_ecl_individual",
    "calcular_ecl_portfolio",
    "consultar_ecl_contrato",
    "simular_cenario_forward_looking",
    "ECL_TOOLS"
]
