"""
ECL Engine - Expected Credit Loss calculation following IFRS 9.

Calculates ECL using the formula: ECL = PD × LGD × EAD
Implements the three-stage model for impairment recognition.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    get_ifrs9_stage,
    setup_logging
)
from propensao.src.lgd_calculator import get_lgd_calculator, LGDCalculator

logger = setup_logging(__name__)


class IFRS9Stage(Enum):
    """IFRS 9 impairment stages."""
    STAGE_1 = 1  # 12-month ECL
    STAGE_2 = 2  # Lifetime ECL (significant increase in credit risk)
    STAGE_3 = 3  # Lifetime ECL (credit-impaired)


@dataclass
class ECLResult:
    """Result of ECL calculation for a single exposure."""
    cliente_id: str
    produto: str
    pd: float
    lgd: float
    ead: float
    ecl: float
    stage: IFRS9Stage
    ecl_12m: float
    ecl_lifetime: float


@dataclass
class PortfolioECL:
    """Aggregated ECL for a portfolio."""
    total_ead: float
    total_ecl: float
    total_ecl_stage1: float
    total_ecl_stage2: float
    total_ecl_stage3: float
    ecl_por_produto: Dict[str, float]
    count_exposures: int
    average_pd: float
    average_lgd: float


class ECLEngine:
    """
    Engine for calculating Expected Credit Loss (ECL) under IFRS 9.
    
    ECL = PD × LGD × EAD
    
    Where:
        PD = Probability of Default (from PRINAD model, 0-1)
        LGD = Loss Given Default (from LGDCalculator, 0-1)
        EAD = Exposure at Default (credit limit or outstanding balance)
    """
    
    # Lifetime multipliers by stage (approximation for term structure)
    LIFETIME_MULTIPLIERS = {
        IFRS9Stage.STAGE_1: 1.0,   # 12-month ECL only
        IFRS9Stage.STAGE_2: 2.5,  # ~2.5 years average lifetime
        IFRS9Stage.STAGE_3: 3.0,  # Higher for impaired
    }
    
    # PRINAD thresholds for stage classification
    PD_THRESHOLD_STAGE2 = 0.20  # 20% PD → Stage 2
    PD_THRESHOLD_STAGE3 = 0.70  # 70% PD → Stage 3
    
    def __init__(self, lgd_calculator: Optional[LGDCalculator] = None):
        """
        Initialize ECL Engine.
        
        Args:
            lgd_calculator: LGD calculator instance
        """
        self.lgd_calculator = lgd_calculator or get_lgd_calculator()
        logger.info("ECLEngine initialized")
    
    def determinar_stage(self, prinad: float, dias_atraso: int = 0) -> IFRS9Stage:
        """
        Determine IFRS 9 stage based on PRINAD and days past due.
        
        Args:
            prinad: PRINAD score (0-100)
            dias_atraso: Days past due
            
        Returns:
            IFRS 9 stage
        """
        # Convert PRINAD to PD (0-1 scale)
        pd = prinad / 100.0
        
        # Stage 3: Credit-impaired (90+ days or PD >= 70%)
        if dias_atraso >= 90 or pd >= self.PD_THRESHOLD_STAGE3:
            return IFRS9Stage.STAGE_3
        
        # Stage 2: Significant increase in credit risk (30+ days or PD >= 20%)
        if dias_atraso >= 30 or pd >= self.PD_THRESHOLD_STAGE2:
            return IFRS9Stage.STAGE_2
        
        # Stage 1: No significant increase
        return IFRS9Stage.STAGE_1
    
    def calcular_ecl_individual(
        self,
        cliente_id: str,
        produto: str,
        prinad: float,
        ead: float,
        dias_atraso: int = 0
    ) -> ECLResult:
        """
        Calculate ECL for a single exposure.
        
        Args:
            cliente_id: Client identifier
            produto: Credit product
            prinad: PRINAD score (0-100)
            ead: Exposure at Default
            dias_atraso: Days past due
            
        Returns:
            ECLResult with all components
        """
        # Convert PRINAD to PD
        pd = min(1.0, max(0.005, prinad / 100.0))  # Floor of 0.5% per Basel III
        
        # Get LGD for product
        lgd = self.lgd_calculator.get_lgd(produto)
        
        # Determine stage
        stage = self.determinar_stage(prinad, dias_atraso)
        
        # Calculate 12-month ECL
        ecl_12m = pd * lgd * ead
        
        # Calculate lifetime ECL
        lifetime_mult = self.LIFETIME_MULTIPLIERS[stage]
        ecl_lifetime = ecl_12m * lifetime_mult
        
        # ECL to report depends on stage
        if stage == IFRS9Stage.STAGE_1:
            ecl_final = ecl_12m
        else:
            ecl_final = ecl_lifetime
        
        return ECLResult(
            cliente_id=cliente_id,
            produto=produto,
            pd=pd,
            lgd=lgd,
            ead=ead,
            ecl=ecl_final,
            stage=stage,
            ecl_12m=ecl_12m,
            ecl_lifetime=ecl_lifetime
        )
    
    def calcular_ecl_cliente(
        self,
        cliente_id: str,
        exposicoes: List[Dict],
        prinad: float
    ) -> List[ECLResult]:
        """
        Calculate ECL for all exposures of a client.
        
        Args:
            cliente_id: Client identifier
            exposicoes: List of dicts with 'produto', 'ead', 'dias_atraso'
            prinad: Client's PRINAD score
            
        Returns:
            List of ECLResults
        """
        results = []
        for exp in exposicoes:
            result = self.calcular_ecl_individual(
                cliente_id=cliente_id,
                produto=exp['produto'],
                prinad=prinad,
                ead=exp.get('ead', 0),
                dias_atraso=exp.get('dias_atraso', 0)
            )
            results.append(result)
        
        return results
    
    def calcular_ecl_portfolio(
        self,
        df: pd.DataFrame,
        col_cliente: str = 'cliente_id',
        col_produto: str = 'produto',
        col_prinad: str = 'prinad',
        col_ead: str = 'ead',
        col_dias_atraso: str = 'dias_atraso'
    ) -> Tuple[PortfolioECL, pd.DataFrame]:
        """
        Calculate ECL for an entire portfolio.
        
        Args:
            df: DataFrame with portfolio data
            col_*: Column name mappings
            
        Returns:
            Tuple of (PortfolioECL summary, DataFrame with ECL details)
        """
        logger.info(f"Calculating ECL for portfolio with {len(df)} exposures")
        
        results = []
        for _, row in df.iterrows():
            result = self.calcular_ecl_individual(
                cliente_id=row.get(col_cliente, ''),
                produto=row.get(col_produto, 'outros'),
                prinad=row.get(col_prinad, 50),  # Default to 50% if missing
                ead=row.get(col_ead, 0),
                dias_atraso=row.get(col_dias_atraso, 0)
            )
            results.append(result)
        
        # Convert to DataFrame
        df_results = pd.DataFrame([
            {
                'cliente_id': r.cliente_id,
                'produto': r.produto,
                'pd': r.pd,
                'lgd': r.lgd,
                'ead': r.ead,
                'ecl': r.ecl,
                'stage': r.stage.value,
                'ecl_12m': r.ecl_12m,
                'ecl_lifetime': r.ecl_lifetime
            }
            for r in results
        ])
        
        # Aggregate by stage
        ecl_por_stage = df_results.groupby('stage')['ecl'].sum().to_dict()
        
        # Aggregate by product
        ecl_por_produto = df_results.groupby('produto')['ecl'].sum().to_dict()
        
        portfolio_ecl = PortfolioECL(
            total_ead=df_results['ead'].sum(),
            total_ecl=df_results['ecl'].sum(),
            total_ecl_stage1=ecl_por_stage.get(1, 0),
            total_ecl_stage2=ecl_por_stage.get(2, 0),
            total_ecl_stage3=ecl_por_stage.get(3, 0),
            ecl_por_produto=ecl_por_produto,
            count_exposures=len(df_results),
            average_pd=df_results['pd'].mean(),
            average_lgd=df_results['lgd'].mean()
        )
        
        logger.info(f"Portfolio ECL: {portfolio_ecl.total_ecl:,.2f}")
        
        return portfolio_ecl, df_results
    
    def simular_otimizacao(
        self,
        df_atual: pd.DataFrame,
        df_otimizado: pd.DataFrame,
        col_ead: str = 'ead'
    ) -> Dict[str, float]:
        """
        Simulate ECL savings from limit optimization.
        
        Args:
            df_atual: Current portfolio
            df_otimizado: Optimized portfolio (with reduced limits)
            
        Returns:
            Dict with ECL comparison metrics
        """
        ecl_atual, _ = self.calcular_ecl_portfolio(df_atual)
        ecl_otimizado, _ = self.calcular_ecl_portfolio(df_otimizado)
        
        economia = ecl_atual.total_ecl - ecl_otimizado.total_ecl
        economia_pct = economia / ecl_atual.total_ecl if ecl_atual.total_ecl > 0 else 0
        
        return {
            'ecl_atual': ecl_atual.total_ecl,
            'ecl_otimizado': ecl_otimizado.total_ecl,
            'economia_absoluta': economia,
            'economia_percentual': economia_pct,
            'ead_atual': ecl_atual.total_ead,
            'ead_otimizado': ecl_otimizado.total_ead,
            'reducao_ead': ecl_atual.total_ead - ecl_otimizado.total_ead
        }


# Module-level instance
_ecl_engine: Optional[ECLEngine] = None


def get_ecl_engine() -> ECLEngine:
    """Get or create ECL engine instance."""
    global _ecl_engine
    if _ecl_engine is None:
        _ecl_engine = ECLEngine()
    return _ecl_engine


def calcular_ecl(
    cliente_id: str,
    produto: str,
    prinad: float,
    ead: float
) -> float:
    """
    Convenience function to calculate ECL.
    
    Args:
        cliente_id: Client ID
        produto: Product name
        prinad: PRINAD score (0-100)
        ead: Exposure at Default
        
    Returns:
        ECL value
    """
    result = get_ecl_engine().calcular_ecl_individual(
        cliente_id=cliente_id,
        produto=produto,
        prinad=prinad,
        ead=ead
    )
    return result.ecl


if __name__ == "__main__":
    # Example calculation
    engine = ECLEngine()
    
    # Single exposure
    result = engine.calcular_ecl_individual(
        cliente_id="12345678901",
        produto="consignado",
        prinad=15.0,  # 15% PD
        ead=50000,    # R$ 50,000 limit
        dias_atraso=0
    )
    
    print("=" * 60)
    print("ECL Calculation Example")
    print("=" * 60)
    print(f"Cliente: {result.cliente_id}")
    print(f"Produto: {result.produto}")
    print(f"PD: {result.pd:.2%}")
    print(f"LGD: {result.lgd:.2%}")
    print(f"EAD: R$ {result.ead:,.2f}")
    print(f"Stage: {result.stage.name}")
    print(f"ECL 12m: R$ {result.ecl_12m:,.2f}")
    print(f"ECL Lifetime: R$ {result.ecl_lifetime:,.2f}")
    print(f"ECL Final: R$ {result.ecl:,.2f}")
    print("=" * 60)
