"""
Shared utilities for risco_bancario project.
Common functions used by both PRINAD and PROPENSAO modules.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"
PRINAD_DIR = BASE_DIR / "prinad"
PROPENSAO_DIR = BASE_DIR / "propensao"

# Products configuration - Complete catalog for Pessoa Física
PRODUTOS_CREDITO = [
    'consignado',
    'banparacard', 
    'cartao_credito_parcelado',
    'cartao_credito_rotativo',
    'imobiliario',
    'cred_veiculo',
    'energia_solar',
    'cheque_especial',
    'credito_sazonal'
]

# Complete product configuration for Pessoa Física
# Includes rates (monthly and annual) and maximum terms
PRODUTOS_PF = {
    'consignado': {
        'nome': 'Crédito Consignado',
        'taxa_mensal': 0.0178,      # 1.78% a.m.
        'taxa_anual': 0.2351,       # 23.51% a.a.
        'prazo_maximo': 180,        # meses
        'tipo': 'parcelado',
        'garantia': 'consignacao',
        'lgd': 0.35
    },
    'cartao_credito_rotativo': {
        'nome': 'Cartão de Crédito Rotativo',
        'taxa_mensal': 0.1737,      # 17.37% a.m.
        'taxa_anual': 5.8313,       # 583.13% a.a.
        'prazo_maximo': 1,          # rotativo
        'tipo': 'rotativo',
        'garantia': 'nenhuma',
        'lgd': 0.70
    },
    'cartao_credito_parcelado': {
        'nome': 'Cartão de Crédito Parcelado',
        'taxa_mensal': 0.0897,      # 8.97% a.m.
        'taxa_anual': 1.8041,       # 180.41% a.a.
        'prazo_maximo': 12,         # meses
        'tipo': 'parcelado',
        'garantia': 'nenhuma',
        'lgd': 0.70
    },
    'banparacard': {
        'nome': 'Banparacard',
        'taxa_mensal': 0.0658,      # 6.58% a.m.
        'taxa_anual': 1.1471,       # 114.71% a.a.
        'prazo_maximo': 80,         # meses
        'tipo': 'parcelado',
        'garantia': 'nenhuma',
        'lgd': 0.45
    },
    'imobiliario': {
        'nome': 'Financiamento Imobiliário',
        'taxa_mensal': 0.0083,      # 0.83% a.m.
        'taxa_anual': 0.1040,       # 10.40% a.a.
        'prazo_maximo': 420,        # meses (35 anos)
        'tipo': 'parcelado',
        'garantia': 'imovel_residencial',
        'lgd': 0.12
    },
    'cred_veiculo': {
        'nome': 'Crédito Veículos',
        'taxa_mensal': 0.0165,      # 1.65% a.m.
        'taxa_anual': 0.2174,       # 21.74% a.a.
        'prazo_maximo': 84,         # meses
        'tipo': 'parcelado',
        'garantia': 'veiculo',
        'lgd': 0.30
    },
    'energia_solar': {
        'nome': 'Energia Solar',
        'taxa_mensal': 0.0165,      # 1.65% a.m.
        'taxa_anual': 0.2174,       # 21.74% a.a.
        'prazo_maximo': 84,         # meses
        'tipo': 'parcelado',
        'garantia': 'equipamento',
        'lgd': 0.35
    },
    'cheque_especial': {
        'nome': 'Cheque Especial',
        'taxa_mensal': 0.0739,      # 7.39% a.m.
        'taxa_anual': 1.3538,       # 135.38% a.a.
        'prazo_maximo': 1,          # rotativo
        'tipo': 'rotativo',
        'garantia': 'nenhuma',
        'lgd': 0.65
    },
    'credito_sazonal': {
        'nome': 'Crédito Sazonal (Antecipação 13º/IR)',
        'taxa_mensal': 0.0200,      # 2.00% a.m.
        'taxa_anual': 0.2682,       # 26.82% a.a.
        'prazo_maximo': 1,          # parcela única
        'tipo': 'parcelado',
        'garantia': 'consignacao',
        'lgd': 0.18
    }
}

# LGD by product (Basel III Foundation IRB) - derived from PRODUTOS_PF
LGD_POR_PRODUTO = {k: v['lgd'] for k, v in PRODUTOS_PF.items()}

# Maximum credit limit multipliers (vs. gross salary)
LIMITE_MAXIMO_MULTIPLO = {
    'consignado': 15,
    'banparacard': 5,
    'cartao_credito_rotativo': 1.5,
    'cartao_credito_parcelado': 1.5,
    'imobiliario': 30,
    'credito_sazonal': 1,
    'cred_veiculo': 10,
    'energia_solar': 8,
    'cheque_especial': 2
}

# Maximum installment terms (months) - derived from PRODUTOS_PF
PRAZO_MAXIMO_MESES = {k: v['prazo_maximo'] for k, v in PRODUTOS_PF.items()}

# =============================================================================
# CONFIGURATION: LGD CALCULATION BY GUARANTEE TYPE
# =============================================================================
# These parameters are used for DYNAMIC LGD calculation per operation
# LGD = f(guarantee_type, LTV, remaining_term, recovery_cost, economic_cycle)

TIPOS_GARANTIA = [
    'imovel_residencial',
    'imovel_comercial', 
    'veiculo',
    'equipamento',
    'consignacao',
    'recebivel',
    'financeiro',
    'nenhuma'
]

# Impact of each guarantee type on LGD
IMPACTO_GARANTIA = {
    'imovel_residencial': {
        'lgd_min': 0.10,           # Best case: excellent property, low LTV
        'lgd_max': 0.25,           # Worst case: bad location, high LTV
        'lgd_base': 0.12,          # Average LGD
        'ltv_max': 0.80,           # Maximum LTV accepted
        'depreciacao_anual': 0.00, # Real estate appreciates
        'custo_recuperacao': 0.08, # Auction, legal fees
        'tempo_recuperacao_meses': 24,  # Average time to recover
        'haircut_downturn': 0.20   # Extra discount in crisis
    },
    'imovel_comercial': {
        'lgd_min': 0.12,
        'lgd_max': 0.30,
        'lgd_base': 0.15,
        'ltv_max': 0.70,
        'depreciacao_anual': 0.02,
        'custo_recuperacao': 0.10,
        'tempo_recuperacao_meses': 30,
        'haircut_downturn': 0.25
    },
    'veiculo': {
        'lgd_min': 0.20,
        'lgd_max': 0.40,
        'lgd_base': 0.30,
        'ltv_max': 0.80,
        'depreciacao_anual': 0.15,  # Vehicles depreciate ~15%/year
        'custo_recuperacao': 0.10,
        'tempo_recuperacao_meses': 6,
        'haircut_downturn': 0.15
    },
    'equipamento': {  # Solar panels, machinery - same impact as vehicles
        'lgd_min': 0.20,
        'lgd_max': 0.40,
        'lgd_base': 0.30,
        'ltv_max': 0.80,
        'depreciacao_anual': 0.10,
        'custo_recuperacao': 0.12,
        'tempo_recuperacao_meses': 8,
        'haircut_downturn': 0.15
    },
    'consignacao': {  # Payroll deduction - same impact as real estate
        'lgd_min': 0.08,
        'lgd_max': 0.20,
        'lgd_base': 0.12,
        'ltv_max': 0.35,  # Max 35% of salary commitment
        'depreciacao_anual': 0.00,
        'custo_recuperacao': 0.03,  # Very low - automatic deduction
        'tempo_recuperacao_meses': 3,
        'haircut_downturn': 0.05
    },
    'recebivel': {
        'lgd_min': 0.08,
        'lgd_max': 0.25,
        'lgd_base': 0.15,
        'ltv_max': 0.90,
        'depreciacao_anual': 0.00,
        'custo_recuperacao': 0.05,
        'tempo_recuperacao_meses': 3,
        'haircut_downturn': 0.10
    },
    'financeiro': {  # CDB, cash deposit
        'lgd_min': 0.00,
        'lgd_max': 0.05,
        'lgd_base': 0.02,
        'ltv_max': 1.00,
        'depreciacao_anual': 0.00,
        'custo_recuperacao': 0.01,
        'tempo_recuperacao_meses': 1,
        'haircut_downturn': 0.02
    },
    'nenhuma': {  # Unsecured
        'lgd_min': 0.45,
        'lgd_max': 0.75,
        'lgd_base': 0.60,
        'ltv_max': 0.00,  # N/A
        'depreciacao_anual': 0.00,
        'custo_recuperacao': 0.15,  # Legal collection costs
        'tempo_recuperacao_meses': 18,
        'haircut_downturn': 0.15
    }
}

# Map product to guarantee type for LGD calculation
GARANTIA_POR_PRODUTO = {
    'consignado': 'consignacao',           # Same impact as real estate
    'credito_sazonal': 'consignacao',      # Same impact as real estate
    'imobiliario': 'imovel_residencial',
    'cred_veiculo': 'veiculo',
    'energia_solar': 'equipamento',        # Same impact as vehicles
    'banparacard': 'nenhuma',
    'cartao_credito_rotativo': 'nenhuma',
    'cartao_credito_parcelado': 'nenhuma',
    'cheque_especial': 'nenhuma'
}

# =============================================================================
# BUSINESS RULES: INCOME COMMITMENT LIMITS PER PRODUCT
# =============================================================================
# Maximum percentage of gross income that can be committed per product
# Note: Some products (cartão, sazonal) do NOT count toward the 70% total limit

COMPROMETIMENTO_POR_PRODUTO = {
    'consignado': {
        'limite_comprometimento': 0.35,    # Max 35% of income
        'conta_no_total': True,            # Counts in 70% total
        'observacao': 'Desconto em folha'
    },
    'imobiliario': {
        'limite_comprometimento': 0.30,    # Max 30% of income
        'conta_no_total': True,
        'observacao': 'Financiamento longo prazo'
    },
    'banparacard': {
        'limite_comprometimento': 0.20,    # Max 20% of income
        'conta_no_total': True,
        'observacao': 'Cartão loja própria'
    },
    'cred_veiculo': {
        'limite_comprometimento': 0.25,    # Max 25% of income
        'conta_no_total': True,
        'observacao': 'Financiamento veículo'
    },
    'energia_solar': {
        'limite_comprometimento': 0.25,    # Max 25% of income
        'conta_no_total': True,
        'observacao': 'Financiamento equipamento'
    },
    'cheque_especial': {
        'limite_comprometimento': 0.10,    # Max 10% of income
        'conta_no_total': True,
        'observacao': 'Emergência'
    },
    # Products that do NOT count toward 70% total
    'cartao_credito_rotativo': {
        'limite_comprometimento': None,    # No fixed limit
        'conta_no_total': False,           # Does NOT count in 70%
        'observacao': 'Rotativo - não entra na conta'
    },
    'cartao_credito_parcelado': {
        'limite_comprometimento': None,
        'conta_no_total': False,
        'observacao': 'Parcelado fatura - não entra na conta'
    },
    'credito_sazonal': {
        'limite_comprometimento': 0.80,    # Max 80% of 13th salary or tax refund
        'conta_no_total': False,           # Does NOT count in 70%
        'observacao': 'Antecipação 13º/IR - limitado a 80% do valor'
    }
}

# =============================================================================
# BUSINESS RULES: PRODUCT DISTRIBUTION FOR CLIENTS
# =============================================================================
# Used for synthetic data generation

DISTRIBUICAO_PRODUTOS = {
    'minimo': 1,       # Minimum products per client (usually consignado)
    'media': 3,        # Average products (consignado, banparacard, cartão)
    'maximo': 5,       # Maximum products
    
    # Probability of having each product (used for synthetic generation)
    'probabilidade': {
        'consignado': 0.85,             # Most common - 85% of clients
        'banparacard': 0.65,            # 65% of clients
        'cartao_credito_rotativo': 0.50, # 50% of clients
        'cartao_credito_parcelado': 0.35, # 35% of clients
        'imobiliario': 0.15,            # 15% of clients
        'credito_sazonal': 0.12,        # 12% of clients
        'energia_solar': 0.05,          # 5% of clients
        'cred_veiculo': 0.08,           # 8% of clients
        'cheque_especial': 0.03         # 3% of clients (least common)
    },
    
    # Common product combinations (for realistic generation)
    'combinacoes_tipicas': [
        ['consignado'],                                            # 1 product
        ['consignado', 'banparacard'],                             # 2 products
        ['consignado', 'banparacard', 'cartao_credito_rotativo'],  # 3 products (most common)
        ['consignado', 'banparacard', 'cartao_credito_rotativo', 'imobiliario'],  # 4 products
        ['consignado', 'banparacard', 'cartao_credito_rotativo', 'imobiliario', 'credito_sazonal'],  # 5 products
    ]
}

# Products automatically granted vs client-requested
PRODUTOS_AUTOMATICOS = [
    'consignado',
    'banparacard',
    'cartao_credito_rotativo',
    'cartao_credito_parcelado',
    'imobiliario'
]

PRODUTOS_SOB_DEMANDA = [
    'energia_solar',
    'cred_veiculo',
    'credito_sazonal',
    'cheque_especial'
]

# =============================================================================
# GLOBAL CONSTANTS
# =============================================================================

# Constants
COMPROMETIMENTO_MAXIMO_RENDA = 0.70  # Max 70% of income (total)
LIMITE_MINIMO_PERCENTUAL = 0.30  # Min 30% of original limit
COMPROMETIMENTO_GATILHO_MAXDEBT = 0.69  # Trigger for max-debt rule


def setup_logging(name: str) -> logging.Logger:
    """Configure logging for a module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)


def parse_month_from_filename(filename: str) -> Optional[str]:
    """
    Extract month reference from filename.
    Example: 'limites_012025.csv' -> '2025-01'
    """
    import re
    match = re.search(r'(\d{2})(\d{4})\.csv$', filename)
    if match:
        month, year = match.groups()
        return f"{year}-{month}"
    return None


def calcular_comprometimento_renda(
    parcelas_mensais: float, 
    renda_bruta: float
) -> float:
    """Calculate income commitment ratio."""
    if renda_bruta <= 0:
        return 1.0  # Maximum commitment if no income
    return min(1.0, parcelas_mensais / renda_bruta)


def calcular_limite_maximo_produto(
    produto: str, 
    renda_bruta: float
) -> float:
    """Calculate maximum credit limit for a product based on income."""
    multiplo = LIMITE_MAXIMO_MULTIPLO.get(produto, 1)
    return renda_bruta * multiplo


def get_lgd(produto: str) -> float:
    """Get Loss Given Default for a product."""
    return LGD_POR_PRODUTO.get(produto, 0.45)  # Default to 45% (unsecured)


def calcular_ecl(pd: float, lgd: float, ead: float) -> float:
    """
    Calculate Expected Credit Loss.
    
    Args:
        pd: Probability of Default (0-1)
        lgd: Loss Given Default (0-1)
        ead: Exposure at Default (credit limit)
    
    Returns:
        ECL value
    """
    return pd * lgd * ead


def get_ifrs9_stage(prinad: float) -> int:
    """
    Determine IFRS 9 stage based on PRINAD rating.
    
    Args:
        prinad: PRINAD score (0-100)
    
    Returns:
        Stage 1, 2, or 3
    """
    if prinad < 20:  # A1-B1
        return 1
    elif prinad < 70:  # B2-C1
        return 2
    else:  # C2-D
        return 3


def calcular_comprometimento_por_produto(
    parcelas_por_produto: Dict[str, float],
    renda_bruta: float
) -> Dict[str, Dict]:
    """
    Calculate income commitment for each product and total.
    
    Args:
        parcelas_por_produto: Dict of produto -> monthly payment
        renda_bruta: Gross monthly income
        
    Returns:
        Dict with per-product commitment and total (only products that count)
    """
    if renda_bruta <= 0:
        return {'total': 1.0, 'por_produto': {}}
    
    resultado = {'por_produto': {}, 'total': 0.0}
    total_comprometimento = 0.0
    
    for produto, parcela in parcelas_por_produto.items():
        config = COMPROMETIMENTO_POR_PRODUTO.get(produto, {})
        limite_produto = config.get('limite_comprometimento')
        conta_no_total = config.get('conta_no_total', True)
        
        comprometimento = parcela / renda_bruta
        
        resultado['por_produto'][produto] = {
            'parcela': parcela,
            'comprometimento': comprometimento,
            'limite': limite_produto,
            'excede_limite': limite_produto and comprometimento > limite_produto,
            'conta_no_total': conta_no_total
        }
        
        if conta_no_total:
            total_comprometimento += comprometimento
    
    resultado['total'] = min(1.0, total_comprometimento)
    resultado['margem_disponivel'] = max(0, COMPROMETIMENTO_MAXIMO_RENDA - total_comprometimento) * renda_bruta
    
    return resultado


def verificar_limite_produto(
    produto: str,
    parcela_proposta: float,
    renda_bruta: float,
    parcelas_atuais: Dict[str, float] = None
) -> Dict:
    """
    Check if a proposed installment respects product limit and total limit.
    
    Args:
        produto: Product name
        parcela_proposta: Proposed monthly payment
        renda_bruta: Gross monthly income
        parcelas_atuais: Current payments by product
        
    Returns:
        Dict with validation result
    """
    if renda_bruta <= 0:
        return {'aprovado': False, 'motivo': 'Renda inválida'}
    
    config = COMPROMETIMENTO_POR_PRODUTO.get(produto, {})
    limite_produto = config.get('limite_comprometimento')
    conta_no_total = config.get('conta_no_total', True)
    
    # Check per-product limit
    comprometimento_proposto = parcela_proposta / renda_bruta
    
    if limite_produto and comprometimento_proposto > limite_produto:
        return {
            'aprovado': False,
            'motivo': f'Excede limite do produto ({limite_produto:.0%})',
            'comprometimento_proposto': comprometimento_proposto,
            'limite_produto': limite_produto
        }
    
    # Check total limit (only if product counts)
    if conta_no_total and parcelas_atuais:
        total_atual = sum(
            v for p, v in parcelas_atuais.items()
            if COMPROMETIMENTO_POR_PRODUTO.get(p, {}).get('conta_no_total', True)
        )
        total_com_nova = (total_atual + parcela_proposta) / renda_bruta
        
        if total_com_nova > COMPROMETIMENTO_MAXIMO_RENDA:
            return {
                'aprovado': False,
                'motivo': f'Excede comprometimento total ({COMPROMETIMENTO_MAXIMO_RENDA:.0%})',
                'comprometimento_atual': total_atual / renda_bruta,
                'comprometimento_com_nova': total_com_nova
            }
    
    return {
        'aprovado': True,
        'motivo': 'Dentro dos limites',
        'comprometimento_proposto': comprometimento_proposto
    }


def get_produtos_para_cliente(n_produtos: int = None) -> List[str]:
    """
    Get a realistic list of products for a client.
    
    Args:
        n_produtos: Number of products (1-5). If None, uses distribution.
        
    Returns:
        List of product names
    """
    import random
    
    if n_produtos is None:
        # Use realistic distribution: mostly 2-3 products
        n_produtos = random.choices(
            [1, 2, 3, 4, 5],
            weights=[0.10, 0.25, 0.40, 0.20, 0.05]
        )[0]
    
    n_produtos = max(1, min(5, n_produtos))
    
    # Always start with consignado
    produtos = ['consignado']
    
    if n_produtos >= 2:
        produtos.append('banparacard')
    if n_produtos >= 3:
        produtos.append('cartao_credito_rotativo')
    if n_produtos >= 4:
        produtos.append('imobiliario')
    if n_produtos >= 5:
        produtos.append('credito_sazonal')
    
    return produtos[:n_produtos]
