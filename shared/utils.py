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

# Products configuration
PRODUTOS_CREDITO = [
    'consignado',
    'banparacard', 
    'cartao_credito',
    'imobiliario',
    'antecipacao_13_sal',
    'cred_veiculo'
]

# LGD by product (Basel III Foundation IRB)
LGD_POR_PRODUTO = {
    'consignado': 0.35,
    'banparacard': 0.45,
    'cartao_credito': 0.70,
    'imobiliario': 0.12,
    'antecipacao_13_sal': 0.18,
    'cred_veiculo': 0.30
}

# Maximum credit limit multipliers (vs. gross salary)
LIMITE_MAXIMO_MULTIPLO = {
    'consignado': 15,
    'banparacard': 5,
    'cartao_credito': 1.5,
    'imobiliario': 30,
    'antecipacao_13_sal': 1,
    'cred_veiculo': 10
}

# Maximum installment terms (months)
PRAZO_MAXIMO_MESES = {
    'consignado': 180,
    'banparacard': 80,
    'cartao_credito': 1,  # Revolving
    'imobiliario': 420,
    'antecipacao_13_sal': 1,
    'cred_veiculo': 60
}

# Constants
COMPROMETIMENTO_MAXIMO_RENDA = 0.70  # Max 70% of income
LIMITE_MINIMO_PERCENTUAL = 0.30  # Min 30% of original limit
COMPROMETIMENTO_GATILHO_MAXDEBT = 0.65  # Trigger for max-debt rule


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
