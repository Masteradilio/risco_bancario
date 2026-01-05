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

# =============================================================================
# BACEN 4966 COMPLIANCE: PD (Probability of Default) BY RATING
# =============================================================================
# Calibrated PD values per rating band for 12-month and lifetime horizons
# PD_12m: Probability of default within 12 months
# PD_lifetime_multiplier: Factor to convert 12m PD to lifetime PD
# Floor: 0.03% (BACEN minimum)

PD_POR_RATING = {
    # Rating: (PD_12m_min, PD_12m_max, maturity_years)
    # PD Lifetime is calculated using formula: 1 - (1 - PD_12m)^n
    # where n = maturity_years (average remaining maturity)
    'A1': (0.0003, 0.0050, 5),      # 0-4.99% PRINAD
    'A2': (0.0050, 0.0100, 5),      # 5-14.99% PRINAD
    'A3': (0.0100, 0.0200, 5),      # 15-24.99% PRINAD
    'B1': (0.0200, 0.0350, 5),      # 25-34.99% PRINAD
    'B2': (0.0350, 0.0500, 5),      # 35-44.99% PRINAD
    'B3': (0.0500, 0.0700, 5),      # 45-54.99% PRINAD
    'C1': (0.0700, 0.1000, 5),      # 55-64.99% PRINAD
    'C2': (0.1000, 0.1500, 5),      # 65-74.99% PRINAD
    'C3': (0.1500, 0.2500, 5),      # 75-84.99% PRINAD
    'D':  (0.2500, 0.5000, 5),      # 85-94.99% PRINAD
    'DEFAULT': (0.5000, 1.0000, 5)  # 95-100% PRINAD (capped at 100%)
}

# PRINAD to Rating mapping
PRINAD_TO_RATING = [
    (5.0, 'A1'),
    (15.0, 'A2'),
    (25.0, 'A3'),
    (35.0, 'B1'),
    (45.0, 'B2'),
    (55.0, 'B3'),
    (65.0, 'C1'),
    (75.0, 'C2'),
    (85.0, 'C3'),
    (95.0, 'D'),
    (float('inf'), 'DEFAULT')
]

# =============================================================================
# BACEN 4966 COMPLIANCE: LGD BY GUARANTEE TYPE (UPDATED)
# =============================================================================
# Updated LGD parameters per BACEN 4966 guidelines

LGD_POR_GARANTIA = {
    # tipo: (LGD_base, LGD_downturn_multiplier)
    'consignacao': (0.25, 1.25),          # Payroll deduction
    'imovel_residencial': (0.15, 1.30),   # Residential property
    'imovel_comercial': (0.20, 1.35),     # Commercial property
    'veiculo': (0.35, 1.40),              # Vehicle
    'equipamento': (0.40, 1.45),          # Equipment (solar, machinery)
    'recebivel': (0.45, 1.30),            # Receivables
    'nenhuma': (0.60, 1.50),              # Unsecured
}

# Regulatory minimums (BACEN)
LGD_MINIMO_PF_SEM_COLATERAL = 0.35  # 35% minimum for unsecured PF
LGD_MINIMO_PF_COM_IMOVEL = 0.15     # 15% minimum with real estate

# =============================================================================
# EAD CALCULATION: CREDIT CONVERSION FACTORS (CCF)
# =============================================================================
# CCF represents how much of unused limit will be drawn before default
# Used in formula: EAD = saldo_utilizado + (limite_disponivel × CCF)

CCF_POR_PRODUTO = {
    'consignado': 1.00,           # Amortized - already fully drawn
    'imobiliario': 1.00,          # Amortized
    'cred_veiculo': 1.00,         # Amortized
    'energia_solar': 1.00,        # Amortized
    'cartao_credito_rotativo': 0.75,   # Revolving - high CCF
    'cartao_credito_parcelado': 0.75,  # Card installments
    'banparacard': 0.75,          # Revolving
    'cheque_especial': 0.70,      # Overdraft
    'credito_sazonal': 0.50,      # Seasonal - lower CCF
    'pessoal': 1.00,              # Amortized
}

# =============================================================================
# GLOBAL LIMIT CALCULATION: GROUP PARAMETERS
# =============================================================================
# The Global Limit is FIXED based on maximum theoretical credit capacity
# Only changes when income changes (not affected by propensity)

PARAMS_LIMITE_GLOBAL = {
    'grupo_a': {
        'pct': 0.35,           # 35% income commitment
        'prazo': 180,          # 180 months (consignado)
        'taxa': 0.018,         # 1.8% monthly rate
        'produtos': ['consignado', 'banparacard', 'pessoal'],
        'descricao': 'Crédito pessoal/consignado'
    },
    'grupo_b': {
        'pct': 0.30,           # 30% income commitment
        'prazo': 420,          # 420 months (35 years - mortgage)
        'taxa': 0.0085,        # 0.85% monthly rate (TR+8.5%)
        'produtos': ['imobiliario'],
        'descricao': 'Financiamento imobiliário'
    },
    'grupo_c': {
        'pct': 0.05,           # 5% income commitment (remaining from 70%)
        'prazo': 60,           # 60 months
        'taxa': 0.018,         # 1.8% monthly rate
        'produtos': ['cred_veiculo', 'energia_solar'],
        'descricao': 'Bens e equipamentos'
    }
}

# Maximum commitment per product (cliente can allocate within 70% total)
MAX_COMPROMETIMENTO_PRODUTO = {
    'consignado':     0.35,   # LEGAL limit - cannot exceed
    'banparacard':    0.35,   # Can receive from other groups
    'pessoal':        0.35,   # Can receive from other groups
    'imobiliario':    0.30,   # Product maximum
    'cred_veiculo':   0.35,   # Can receive from other groups
    'energia_solar':  0.25,   # Product maximum
}

# Products outside global limit (independent limits)
PRODUTOS_FORA_LIMITE_GLOBAL = {
    'limite_rotativo': {
        'limite_total': 'renda_bruta',  # 100% of income
        'produtos_concorrentes': ['cartao_credito_rotativo', 'cartao_credito_parcelado', 'cheque_especial'],
        'descricao': 'Cliente decide proporção entre cartão e cheque',
    },
    'credito_sazonal': {
        'limite': 0.80,  # 80% of 13th salary or tax refund
        'descricao': '80% do 13º ou restituição IR',
    },
}

# =============================================================================
# IFRS 9 / BACEN 4966: STAGE CLASSIFICATION CRITERIA
# =============================================================================
# Stage 1: Normal risk - ECL horizon = 12 months
# Stage 2: Significant increase in risk - ECL horizon = Lifetime
# Stage 3: Default/Impairment - ECL horizon = Lifetime with max LGD

CRITERIOS_STAGE = {
    'STAGE_1': {
        'descricao': 'Risco Normal',
        'ecl_horizonte': '12_meses',
        'condicoes': {
            'dias_atraso_max': 30,
            'rating_minimo': 'B3',  # Must be B3 or better
            'downgrade_max': 1,     # Max 1 notch downgrade
        }
    },
    'STAGE_2': {
        'descricao': 'Aumento Significativo de Risco',
        'ecl_horizonte': 'lifetime',
        'gatilhos': {
            'dias_atraso_min': 31,
            'dias_atraso_max': 90,
            'downgrade_notches': 2,   # >= 2 notches downgrade
            'reducao_renda_pct': 0.30,  # >= 30% income reduction
            'aumento_dti_pp': 0.20,     # >= 20 percentage points DTI increase
            'queda_score_externo': 100  # >= 100 points drop in external score
        }
    },
    'STAGE_3': {
        'descricao': 'Default/Impairment',
        'ecl_horizonte': 'lifetime_max_lgd',
        'gatilhos': {
            'dias_atraso_min': 91,
            'evento_judicial': True,
            'insolvencia': True,
            'falha_renegociacao': True
        },
        'arrasto': True  # All client products migrate to Stage 3
    }
}

# =============================================================================
# IFRS 9 / BACEN 4966: CURE CRITERIA (STAGE REVERSAL)
# =============================================================================
# Conditions to reverse from higher stage to lower

CRITERIOS_CURA = {
    'STAGE_2_para_1': {
        'periodo_observacao_meses': 6,
        'condicoes': {
            'adimplente_meses_consecutivos': 6,
            'rating_estabilizado': True,
            'sem_novos_atrasos': True,
            'sem_eventos_negativos_internos': True,
            'sem_eventos_negativos_scr': True
        }
    },
    'STAGE_3_para_2': {
        'periodo_observacao_meses': 12,
        'condicoes': {
            'debito_quitado': True,
            'adimplente_meses_consecutivos': 12,
            'rating_minimo': 'C2'
        }
    }
}

# =============================================================================
# PROPENSITY MODEL: CONFIGURATION
# =============================================================================
# Ensemble configuration for propensity model

PROPENSITY_ENSEMBLE_CONFIG = {
    'primario': {
        'modelo': 'LightGBM',
        'peso': 0.70
    },
    'secundario': {
        'modelo': 'XGBoost',
        'peso': 0.20
    },
    'validacao': {
        'modelo': 'RandomForest',
        'peso': 0.10
    },
    'balanceamento': 'SMOTEENN',
    'auc_minimo_esperado': 0.85
}

# Top 15 features for propensity model (cross-product)
FEATURES_PROPENSAO_TOP15 = [
    'credit_score_internal',           # PRINAD score
    'credit_utilization_ratio',        # % limit used
    'annual_income',                   # Annual income
    'transaction_frequency_12m',       # Transactions/year
    'revolving_utilization_ratio',     # % card used
    'payment_history_score',           # % on-time payments
    'months_customer_tenure',          # Customer tenure
    'delinquency_rate_12m',            # 12m delinquency rate
    'discretionary_spending_ratio',    # Non-essential spending
    'debt_to_income_ratio',            # DTI
    'employment_stability_proxy',      # Employment stability
    'product_holding_diversity',       # Number of products
    'months_since_last_transaction',   # Inactivity
    'historical_product_usage_count',  # Historical usage
    'app_engagement_score',            # Digital engagement
]

# Product-specific features for propensity
FEATURES_PROPENSAO_POR_PRODUTO = {
    'pessoal': ['transaction_frequency', 'discretionary_ratio', 'months_since_txn'],
    'consignado': ['margem_remaining', 'is_inss_eligible', 'refinance_history'],
    'imobiliario': ['has_property', 'website_visits', 'income_stability'],
    'cartao_credito': ['txn_frequency_30d', 'online_shopping_ratio', 'utilization_ratio'],
    'credito_sazonal': ['is_clt', 'current_month', 'advance_history'],
    'energia_solar': ['property_owner', 'electricity_bill', 'environmental_spend'],
}

# Propensity classification thresholds
PROPENSAO_CLASSIFICACAO = {
    'ALTA': {'min': 60, 'max': 100},
    'MEDIA': {'min': 40, 'max': 59},
    'BAIXA': {'min': 0, 'max': 39}
}

# Minimum propensity for limit increase
PROPENSAO_MINIMA_PARA_AUMENTO = 55

# Maximum propensity for limit reduction
PROPENSAO_MAXIMA_PARA_REDUCAO = 45


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


# =============================================================================
# NEW HELPER FUNCTIONS FOR BACEN 4966 COMPLIANCE
# =============================================================================

def get_rating_from_prinad(prinad: float) -> str:
    """
    Convert PRINAD score (0-100) to Rating (A1 to DEFAULT).
    
    Args:
        prinad: PRINAD score (0-100)
        
    Returns:
        Rating string (A1, A2, ..., D, DEFAULT)
    """
    prinad = max(0.0, min(100.0, prinad))
    for threshold, rating in PRINAD_TO_RATING:
        if prinad < threshold:
            return rating
    return 'DEFAULT'


def calcular_pd_por_rating(prinad: float, rating: str = None) -> Dict[str, float]:
    """
    Calculate calibrated PD values (12m and lifetime) based on PRINAD and Rating.
    
    Uses interpolation within rating band:
    PD_12m = PD_min + (prinad_position_in_band) × (PD_max - PD_min)
    PD_lifetime = PD_12m × lifetime_multiplier
    
    Args:
        prinad: PRINAD score (0-100)
        rating: Optional rating override. If None, derived from prinad.
        
    Returns:
        Dict with pd_12m, pd_lifetime, rating
    """
    if rating is None:
        rating = get_rating_from_prinad(prinad)
    
    if rating not in PD_POR_RATING:
        rating = 'DEFAULT'
    
    pd_min, pd_max, lifetime_mult = PD_POR_RATING[rating]
    
    # Get rating band bounds from PRINAD_TO_RATING
    rating_bounds = {r: (i, t) for i, (t, r) in enumerate(PRINAD_TO_RATING)}
    
    # Find position within rating band (0 to 1)
    prinad_bands = [0] + [t for t, _ in PRINAD_TO_RATING[:-1]]
    idx = rating_bounds.get(rating, (0, 100))[0]
    band_min = prinad_bands[idx] if idx < len(prinad_bands) else 0
    band_max = prinad_bands[idx + 1] if idx + 1 < len(prinad_bands) else 100
    
    # Interpolate within band
    if band_max > band_min:
        position = (prinad - band_min) / (band_max - band_min)
    else:
        position = 0.5
    
    position = max(0.0, min(1.0, position))
    
    # Calculate PD 12m
    pd_12m = pd_min + position * (pd_max - pd_min)
    
    # Apply BACEN floor
    pd_12m = max(0.0003, pd_12m)  # 0.03% floor
    pd_12m = min(1.0, pd_12m)     # Cap at 100%
    
    # Calculate PD Lifetime using survival probability formula
    # PD_Lifetime = 1 - (1 - PD_12m)^n where n = maturity years
    maturity_years = lifetime_mult  # This is now maturity_years in the config
    pd_lifetime = 1 - ((1 - pd_12m) ** maturity_years)
    pd_lifetime = min(1.0, pd_lifetime)  # Cap at 100%
    pd_lifetime = max(pd_12m, pd_lifetime)  # Lifetime >= 12m
    
    return {
        'rating': rating,
        'pd_12m': round(pd_12m, 6),
        'pd_lifetime': round(pd_lifetime, 6),
        'maturity_years': maturity_years
    }


def calcular_ead(
    produto: str,
    limite_total: float,
    saldo_utilizado: float,
    ccf: float = None
) -> Dict[str, float]:
    """
    Calculate Exposure at Default (EAD) for a product.
    
    Formula: EAD = saldo_utilizado + (limite_disponivel × CCF)
    
    Args:
        produto: Product name
        limite_total: Total credit limit
        saldo_utilizado: Current balance used
        ccf: Optional CCF override. If None, uses product default.
        
    Returns:
        Dict with ead, limite_disponivel, ccf used
    """
    limite_disponivel = max(0, limite_total - saldo_utilizado)
    
    if ccf is None:
        ccf = CCF_POR_PRODUTO.get(produto, 0.75)
    
    ead = saldo_utilizado + (limite_disponivel * ccf)
    
    return {
        'ead': round(ead, 2),
        'saldo_utilizado': saldo_utilizado,
        'limite_disponivel': limite_disponivel,
        'ccf': ccf,
        'produto': produto
    }


def calcular_limite_global_fixo(renda_bruta: float) -> Dict[str, Any]:
    """
    Calculate the FIXED global limit based on maximum theoretical capacity.
    
    This limit ONLY changes when income changes (not affected by propensity).
    
    Uses Price formula: PV = PMT × [(1 - (1 + i)^-n) / i]
    
    Args:
        renda_bruta: Gross monthly income
        
    Returns:
        Dict with limite_global, detalhes per group, and renda_bruta
    """
    limite_global = 0.0
    detalhes = {}
    
    for grupo, params in PARAMS_LIMITE_GLOBAL.items():
        parcela = renda_bruta * params['pct']
        taxa = params['taxa']
        prazo = params['prazo']
        
        # Price formula: PV = PMT × [(1 - (1 + i)^-n) / i]
        if taxa > 0:
            fator = (1 - (1 + taxa) ** -prazo) / taxa
        else:
            fator = prazo
        
        limite = parcela * fator
        
        detalhes[grupo] = {
            'parcela': round(parcela, 2),
            'prazo': prazo,
            'taxa': taxa,
            'fator': round(fator, 2),
            'limite': round(limite, 2),
            'produtos': params['produtos'],
            'descricao': params['descricao']
        }
        limite_global += limite
    
    return {
        'limite_global': round(limite_global, 2),
        'detalhes': detalhes,
        'renda_bruta': renda_bruta,
        'comprometimento_max': COMPROMETIMENTO_MAXIMO_RENDA,
        'so_muda_com_renda': True
    }


def get_stage_from_criteria(
    dias_atraso: int = 0,
    rating_atual: str = 'A1',
    rating_anterior: str = None,
    evento_judicial: bool = False,
    insolvencia: bool = False,
    falha_renegociacao: bool = False
) -> Dict[str, Any]:
    """
    Determine IFRS 9 Stage based on criteria.
    
    Args:
        dias_atraso: Days in arrears
        rating_atual: Current rating
        rating_anterior: Previous rating (for downgrade calculation)
        evento_judicial: Has judicial event
        insolvencia: Is insolvent
        falha_renegociacao: Failed renegotiation
        
    Returns:
        Dict with stage, descricao, ecl_horizonte, arrasto
    """
    # Rating order for downgrade calculation
    RATING_ORDER = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D', 'DEFAULT']
    
    # Check Stage 3 triggers first (most severe)
    stage3_triggers = CRITERIOS_STAGE['STAGE_3']['gatilhos']
    if (dias_atraso >= stage3_triggers['dias_atraso_min'] or
        evento_judicial or insolvencia or falha_renegociacao):
        return {
            'stage': 3,
            'descricao': CRITERIOS_STAGE['STAGE_3']['descricao'],
            'ecl_horizonte': 'lifetime_max_lgd',
            'arrasto': True,
            'gatilho': 'dias_atraso' if dias_atraso >= 91 else 
                       'evento_judicial' if evento_judicial else
                       'insolvencia' if insolvencia else 'falha_renegociacao'
        }
    
    # Check Stage 2 triggers
    stage2_triggers = CRITERIOS_STAGE['STAGE_2']['gatilhos']
    
    # Calculate downgrade if rating_anterior provided
    downgrade_notches = 0
    if rating_anterior and rating_anterior in RATING_ORDER and rating_atual in RATING_ORDER:
        idx_anterior = RATING_ORDER.index(rating_anterior)
        idx_atual = RATING_ORDER.index(rating_atual)
        downgrade_notches = idx_atual - idx_anterior
    
    if (dias_atraso >= stage2_triggers['dias_atraso_min'] or
        downgrade_notches >= stage2_triggers['downgrade_notches']):
        return {
            'stage': 2,
            'descricao': CRITERIOS_STAGE['STAGE_2']['descricao'],
            'ecl_horizonte': 'lifetime',
            'arrasto': False,
            'gatilho': 'dias_atraso' if dias_atraso >= 31 else 'downgrade',
            'downgrade_notches': downgrade_notches
        }
    
    # Default to Stage 1
    return {
        'stage': 1,
        'descricao': CRITERIOS_STAGE['STAGE_1']['descricao'],
        'ecl_horizonte': '12_meses',
        'arrasto': False,
        'gatilho': None
    }


def calcular_ecl_por_stage(
    pd_result: Dict[str, float],
    lgd: float,
    ead: float,
    stage: int
) -> Dict[str, float]:
    """
    Calculate ECL based on Stage.
    
    Stage 1: ECL = PD_12m × LGD × EAD
    Stage 2: ECL = PD_lifetime × LGD × EAD
    Stage 3: ECL = PD_lifetime × LGD_max × EAD (LGD_max = min(1.0, LGD × 1.5))
    
    Args:
        pd_result: Result from calcular_pd_por_rating()
        lgd: Loss Given Default (0-1)
        ead: Exposure at Default
        stage: IFRS 9 stage (1, 2, or 3)
        
    Returns:
        Dict with ecl, pd_used, lgd_used, ead, stage
    """
    if stage == 1:
        pd_used = pd_result['pd_12m']
        lgd_used = lgd
    elif stage == 2:
        pd_used = pd_result['pd_lifetime']
        lgd_used = lgd
    else:  # Stage 3
        pd_used = pd_result['pd_lifetime']
        lgd_used = min(1.0, lgd * 1.5)  # Max LGD for impaired
    
    ecl = pd_used * lgd_used * ead
    
    return {
        'ecl': round(ecl, 2),
        'pd_used': pd_used,
        'lgd_used': lgd_used,
        'ead': ead,
        'stage': stage,
        'horizonte': '12_meses' if stage == 1 else 'lifetime'
    }
