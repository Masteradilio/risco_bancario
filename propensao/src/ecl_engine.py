"""
ECL Engine - Expected Credit Loss calculation following IFRS 9 / BACEN 4966.

Calculates ECL using the formula: ECL = PD × LGD × EAD
Implements the three-stage model for impairment recognition.

REVAMP v2.0:
- Uses calibrated PD from shared/utils.py (pd_12m and pd_lifetime)
- Integrates with StageClassifier for stage determination
- Calculates EAD with CCF (Credit Conversion Factor)
- Applies stage-appropriate ECL horizon
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    LGD_POR_PRODUTO,
    CCF_POR_PRODUTO,
    PD_POR_RATING,
    CRITERIOS_STAGE,
    get_rating_from_prinad,
    calcular_pd_por_rating,
    calcular_ead,
    get_stage_from_criteria,
    calcular_ecl_por_stage,
    get_lgd,
    setup_logging
)
from propensao.src.lgd_calculator import get_lgd_calculator, LGDCalculator
from propensao.src.stage_classifier import (
    StageClassifier, 
    StageClassification,
    Stage,
    classificar_stage_simples
)

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
    prinad: float
    rating: str
    pd_12m: float
    pd_lifetime: float
    lgd: float
    ead: float
    ecl: float
    stage: int
    ecl_12m: float
    ecl_lifetime: float
    ecl_horizonte: str  # '12_meses' or 'lifetime'
    arrasto: bool = False
    data_calculo: datetime = field(default_factory=datetime.now)
    detalhes: Dict = field(default_factory=dict)


@dataclass
class PortfolioECL:
    """Aggregated ECL for a portfolio."""
    total_ead: float
    total_ecl: float
    total_ecl_stage1: float
    total_ecl_stage2: float
    total_ecl_stage3: float
    ecl_por_produto: Dict[str, float]
    ecl_por_rating: Dict[str, float]
    count_exposures: int
    count_stage1: int
    count_stage2: int
    count_stage3: int
    average_pd_12m: float
    average_pd_lifetime: float
    average_lgd: float
    cobertura_ecl_pct: float  # ECL / EAD
    data_calculo: datetime = field(default_factory=datetime.now)


class ECLEngine:
    """
    Engine for calculating Expected Credit Loss (ECL) under IFRS 9 / BACEN 4966.
    
    ECL = PD × LGD × EAD
    
    Where:
        PD = Probability of Default:
             - Stage 1: PD_12m (calibrated)
             - Stage 2/3: PD_lifetime (calibrated)
        LGD = Loss Given Default (from LGDCalculator or product config)
             - Stage 3: LGD × 1.5 (max 100%)
        EAD = Exposure at Default:
             - saldo_utilizado + (limite_disponivel × CCF)
    
    REVAMP v2.0 Features:
    - Calibrated PD values per rating band
    - Stage classification via StageClassifier
    - EAD calculation with CCF
    - Drag effect support (arrasto)
    """
    
    def __init__(
        self, 
        lgd_calculator: Optional[LGDCalculator] = None,
        stage_classifier: Optional[StageClassifier] = None
    ):
        """
        Initialize ECL Engine.
        
        Args:
            lgd_calculator: LGD calculator instance
            stage_classifier: Stage classifier instance
        """
        self.lgd_calculator = lgd_calculator or get_lgd_calculator()
        self.stage_classifier = stage_classifier or StageClassifier()
        logger.info("ECLEngine v2.0 initialized (BACEN 4966 compliant)")
    
    def calcular_ecl_individual(
        self,
        cliente_id: str,
        produto: str,
        prinad: float,
        limite_total: float,
        saldo_utilizado: float = 0,
        dias_atraso: int = 0,
        rating_anterior: str = None,
        evento_judicial: bool = False,
        insolvencia: bool = False,
        falha_renegociacao: bool = False,
        arrasto: bool = False,
        lgd_override: float = None,
        ccf_override: float = None
    ) -> ECLResult:
        """
        Calculate ECL for a single exposure using BACEN 4966 methodology.
        
        Args:
            cliente_id: Client identifier
            produto: Credit product
            prinad: PRINAD score (0-100)
            limite_total: Total credit limit
            saldo_utilizado: Current balance used
            dias_atraso: Days past due
            rating_anterior: Previous rating (for downgrade trigger)
            evento_judicial: Has judicial event
            insolvencia: Is insolvent
            falha_renegociacao: Failed renegotiation
            arrasto: Drag effect active (from other product in Stage 3)
            lgd_override: Override LGD value
            ccf_override: Override CCF value
            
        Returns:
            ECLResult with all components
        """
        # Get rating from PRINAD
        rating = get_rating_from_prinad(prinad)
        
        # Calculate calibrated PD (12m and lifetime)
        pd_result = calcular_pd_por_rating(prinad, rating)
        
        # Calculate EAD with CCF
        ead_result = calcular_ead(
            produto=produto,
            limite_total=limite_total,
            saldo_utilizado=saldo_utilizado,
            ccf=ccf_override
        )
        ead = ead_result['ead']
        
        # Get LGD
        if lgd_override is not None:
            lgd = lgd_override
        else:
            lgd = self.lgd_calculator.get_lgd(produto)
        
        # Determine stage (use simple version or full classifier)
        if arrasto:
            # Drag effect forces Stage 3
            stage = 3
            ecl_horizonte = 'lifetime_max_lgd'
            gatilho = 'arrasto'
        else:
            # Use StageClassifier for full analysis
            stage_result = get_stage_from_criteria(
                dias_atraso=dias_atraso,
                rating_atual=rating,
                rating_anterior=rating_anterior,
                evento_judicial=evento_judicial,
                insolvencia=insolvencia,
                falha_renegociacao=falha_renegociacao
            )
            stage = stage_result['stage']
            ecl_horizonte = stage_result['ecl_horizonte']
            gatilho = stage_result.get('gatilho')
        
        # Calculate ECL based on stage
        ecl_result = calcular_ecl_por_stage(
            pd_result=pd_result,
            lgd=lgd,
            ead=ead,
            stage=stage
        )
        
        # Also calculate both horizons for reference
        ecl_12m = pd_result['pd_12m'] * lgd * ead
        ecl_lifetime = pd_result['pd_lifetime'] * lgd * ead
        
        return ECLResult(
            cliente_id=cliente_id,
            produto=produto,
            prinad=prinad,
            rating=rating,
            pd_12m=pd_result['pd_12m'],
            pd_lifetime=pd_result['pd_lifetime'],
            lgd=ecl_result['lgd_used'],
            ead=ead,
            ecl=ecl_result['ecl'],
            stage=stage,
            ecl_12m=round(ecl_12m, 2),
            ecl_lifetime=round(ecl_lifetime, 2),
            ecl_horizonte=ecl_horizonte,
            arrasto=arrasto,
            detalhes={
                'ccf': ead_result['ccf'],
                'limite_total': limite_total,
                'saldo_utilizado': saldo_utilizado,
                'limite_disponivel': ead_result['limite_disponivel'],
                'lgd_original': lgd,
                'pd_lifetime_mult': pd_result['lifetime_multiplier'],
                'gatilho': gatilho
            }
        )
    
    def calcular_ecl_individual_simples(
        self,
        cliente_id: str,
        produto: str,
        prinad: float,
        ead: float,
        dias_atraso: int = 0
    ) -> ECLResult:
        """
        Simplified ECL calculation (backward compatible).
        
        Uses EAD directly (assumes saldo_utilizado = limite_total for CCF = 1.0 products).
        
        Args:
            cliente_id: Client identifier
            produto: Credit product
            prinad: PRINAD score (0-100)
            ead: Exposure at Default
            dias_atraso: Days past due
            
        Returns:
            ECLResult with all components
        """
        return self.calcular_ecl_individual(
            cliente_id=cliente_id,
            produto=produto,
            prinad=prinad,
            limite_total=ead,  # Assume full utilization
            saldo_utilizado=ead,
            dias_atraso=dias_atraso
        )
    
    def calcular_ecl_cliente(
        self,
        cliente_id: str,
        exposicoes: List[Dict],
        prinad: float,
        aplicar_arrasto: bool = True
    ) -> List[ECLResult]:
        """
        Calculate ECL for all exposures of a client.
        
        Implements drag effect: if any product is in Stage 3,
        all products are calculated with Stage 3.
        
        Args:
            cliente_id: Client identifier
            exposicoes: List of dicts with 'produto', 'limite_total', 'saldo_utilizado', 'dias_atraso'
            prinad: Client's PRINAD score
            aplicar_arrasto: Whether to apply drag effect
            
        Returns:
            List of ECLResults
        """
        # First pass: determine if any product triggers Stage 3
        arrasto_ativo = False
        arrasto_origem = None
        
        if aplicar_arrasto:
            for exp in exposicoes:
                stage = classificar_stage_simples(
                    dias_atraso=exp.get('dias_atraso', 0),
                    prinad=prinad,
                    evento_judicial=exp.get('evento_judicial', False)
                )
                if stage == 3:
                    arrasto_ativo = True
                    arrasto_origem = exp.get('produto')
                    break
        
        # Second pass: calculate ECL for all products
        results = []
        for exp in exposicoes:
            is_arrasto = arrasto_ativo and exp.get('produto') != arrasto_origem
            
            result = self.calcular_ecl_individual(
                cliente_id=cliente_id,
                produto=exp.get('produto', 'outros'),
                prinad=prinad,
                limite_total=exp.get('limite_total', exp.get('ead', 0)),
                saldo_utilizado=exp.get('saldo_utilizado', exp.get('ead', 0)),
                dias_atraso=exp.get('dias_atraso', 0),
                evento_judicial=exp.get('evento_judicial', False),
                insolvencia=exp.get('insolvencia', False),
                falha_renegociacao=exp.get('falha_renegociacao', False),
                arrasto=is_arrasto
            )
            
            if is_arrasto:
                result.detalhes['arrasto_origem'] = arrasto_origem
            
            results.append(result)
        
        return results
    
    def calcular_ecl_portfolio(
        self,
        df: pd.DataFrame,
        col_cliente: str = 'cliente_id',
        col_produto: str = 'produto',
        col_prinad: str = 'prinad',
        col_limite_total: str = 'limite_total',
        col_saldo_utilizado: str = 'saldo_utilizado',
        col_dias_atraso: str = 'dias_atraso',
        aplicar_arrasto: bool = True
    ) -> Tuple[PortfolioECL, pd.DataFrame]:
        """
        Calculate ECL for an entire portfolio.
        
        Args:
            df: DataFrame with portfolio data
            col_*: Column name mappings
            aplicar_arrasto: Whether to apply drag effect
            
        Returns:
            Tuple of (PortfolioECL summary, DataFrame with ECL details)
        """
        logger.info(f"Calculating ECL for portfolio with {len(df)} exposures")
        
        # Handle missing columns
        if col_saldo_utilizado not in df.columns:
            if 'ead' in df.columns:
                df[col_saldo_utilizado] = df['ead']
            elif col_limite_total in df.columns:
                df[col_saldo_utilizado] = df[col_limite_total]
            else:
                df[col_saldo_utilizado] = 0
        
        if col_limite_total not in df.columns:
            if 'ead' in df.columns:
                df[col_limite_total] = df['ead']
            else:
                df[col_limite_total] = df[col_saldo_utilizado]
        
        if col_dias_atraso not in df.columns:
            df[col_dias_atraso] = 0
        
        # Group by client for drag effect
        if aplicar_arrasto:
            clientes = df[col_cliente].unique()
            all_results = []
            
            for cliente_id in clientes:
                df_cliente = df[df[col_cliente] == cliente_id]
                exposicoes = df_cliente.to_dict('records')
                
                # Get PRINAD (use first row or mean)
                prinad = df_cliente[col_prinad].iloc[0] if len(df_cliente) > 0 else 50
                
                # Format exposicoes for calcular_ecl_cliente
                exposicoes_fmt = [
                    {
                        'produto': row.get(col_produto, 'outros'),
                        'limite_total': row.get(col_limite_total, 0),
                        'saldo_utilizado': row.get(col_saldo_utilizado, 0),
                        'dias_atraso': row.get(col_dias_atraso, 0)
                    }
                    for row in exposicoes
                ]
                
                results = self.calcular_ecl_cliente(
                    cliente_id=cliente_id,
                    exposicoes=exposicoes_fmt,
                    prinad=prinad,
                    aplicar_arrasto=True
                )
                all_results.extend(results)
        else:
            # Simple row-by-row calculation
            all_results = []
            for _, row in df.iterrows():
                result = self.calcular_ecl_individual_simples(
                    cliente_id=str(row.get(col_cliente, '')),
                    produto=row.get(col_produto, 'outros'),
                    prinad=row.get(col_prinad, 50),
                    ead=row.get(col_limite_total, row.get('ead', 0)),
                    dias_atraso=row.get(col_dias_atraso, 0)
                )
                all_results.append(result)
        
        # Convert to DataFrame
        df_results = pd.DataFrame([
            {
                'cliente_id': r.cliente_id,
                'produto': r.produto,
                'prinad': r.prinad,
                'rating': r.rating,
                'pd_12m': r.pd_12m,
                'pd_lifetime': r.pd_lifetime,
                'lgd': r.lgd,
                'ead': r.ead,
                'ecl': r.ecl,
                'stage': r.stage,
                'ecl_12m': r.ecl_12m,
                'ecl_lifetime': r.ecl_lifetime,
                'ecl_horizonte': r.ecl_horizonte,
                'arrasto': r.arrasto
            }
            for r in all_results
        ])
        
        # Aggregate by stage
        stage_counts = df_results['stage'].value_counts().to_dict()
        ecl_por_stage = df_results.groupby('stage')['ecl'].sum().to_dict()
        
        # Aggregate by product
        ecl_por_produto = df_results.groupby('produto')['ecl'].sum().to_dict()
        
        # Aggregate by rating
        ecl_por_rating = df_results.groupby('rating')['ecl'].sum().to_dict()
        
        # Calculate coverage
        total_ead = df_results['ead'].sum()
        total_ecl = df_results['ecl'].sum()
        cobertura = (total_ecl / total_ead * 100) if total_ead > 0 else 0
        
        portfolio_ecl = PortfolioECL(
            total_ead=round(total_ead, 2),
            total_ecl=round(total_ecl, 2),
            total_ecl_stage1=round(ecl_por_stage.get(1, 0), 2),
            total_ecl_stage2=round(ecl_por_stage.get(2, 0), 2),
            total_ecl_stage3=round(ecl_por_stage.get(3, 0), 2),
            ecl_por_produto=ecl_por_produto,
            ecl_por_rating=ecl_por_rating,
            count_exposures=len(df_results),
            count_stage1=stage_counts.get(1, 0),
            count_stage2=stage_counts.get(2, 0),
            count_stage3=stage_counts.get(3, 0),
            average_pd_12m=round(df_results['pd_12m'].mean(), 6),
            average_pd_lifetime=round(df_results['pd_lifetime'].mean(), 6),
            average_lgd=round(df_results['lgd'].mean(), 4),
            cobertura_ecl_pct=round(cobertura, 4)
        )
        
        logger.info(f"Portfolio ECL: R$ {portfolio_ecl.total_ecl:,.2f} ({portfolio_ecl.cobertura_ecl_pct:.2f}% coverage)")
        
        return portfolio_ecl, df_results
    
    def simular_otimizacao(
        self,
        df_atual: pd.DataFrame,
        df_otimizado: pd.DataFrame,
        col_ead: str = 'ead'
    ) -> Dict[str, Any]:
        """
        Simulate ECL savings from limit optimization.
        
        Args:
            df_atual: Current portfolio
            df_otimizado: Optimized portfolio (with reduced limits)
            
        Returns:
            Dict with ECL comparison metrics
        """
        ecl_atual, df_ecl_atual = self.calcular_ecl_portfolio(df_atual, aplicar_arrasto=True)
        ecl_otimizado, df_ecl_otimizado = self.calcular_ecl_portfolio(df_otimizado, aplicar_arrasto=True)
        
        economia = ecl_atual.total_ecl - ecl_otimizado.total_ecl
        economia_pct = (economia / ecl_atual.total_ecl * 100) if ecl_atual.total_ecl > 0 else 0
        
        return {
            'ecl_atual': ecl_atual.total_ecl,
            'ecl_otimizado': ecl_otimizado.total_ecl,
            'economia_absoluta': round(economia, 2),
            'economia_percentual': round(economia_pct, 2),
            'ead_atual': ecl_atual.total_ead,
            'ead_otimizado': ecl_otimizado.total_ead,
            'reducao_ead': round(ecl_atual.total_ead - ecl_otimizado.total_ead, 2),
            'cobertura_atual_pct': ecl_atual.cobertura_ecl_pct,
            'cobertura_otimizado_pct': ecl_otimizado.cobertura_ecl_pct,
            'stage_migration': {
                'stage1_diff': ecl_otimizado.count_stage1 - ecl_atual.count_stage1,
                'stage2_diff': ecl_otimizado.count_stage2 - ecl_atual.count_stage2,
                'stage3_diff': ecl_otimizado.count_stage3 - ecl_atual.count_stage3
            }
        }
    
    def gerar_relatorio_ecl(
        self,
        portfolio_ecl: PortfolioECL,
        df_results: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generate comprehensive ECL report.
        
        Args:
            portfolio_ecl: Portfolio ECL summary
            df_results: Detailed results DataFrame
            
        Returns:
            Report dict with all metrics
        """
        return {
            'resumo': {
                'total_ead': portfolio_ecl.total_ead,
                'total_ecl': portfolio_ecl.total_ecl,
                'cobertura_pct': portfolio_ecl.cobertura_ecl_pct,
                'total_exposicoes': portfolio_ecl.count_exposures
            },
            'por_stage': {
                'stage_1': {
                    'count': portfolio_ecl.count_stage1,
                    'ecl': portfolio_ecl.total_ecl_stage1,
                    'pct_total': round(portfolio_ecl.total_ecl_stage1 / portfolio_ecl.total_ecl * 100, 2) if portfolio_ecl.total_ecl > 0 else 0
                },
                'stage_2': {
                    'count': portfolio_ecl.count_stage2,
                    'ecl': portfolio_ecl.total_ecl_stage2,
                    'pct_total': round(portfolio_ecl.total_ecl_stage2 / portfolio_ecl.total_ecl * 100, 2) if portfolio_ecl.total_ecl > 0 else 0
                },
                'stage_3': {
                    'count': portfolio_ecl.count_stage3,
                    'ecl': portfolio_ecl.total_ecl_stage3,
                    'pct_total': round(portfolio_ecl.total_ecl_stage3 / portfolio_ecl.total_ecl * 100, 2) if portfolio_ecl.total_ecl > 0 else 0
                }
            },
            'por_produto': portfolio_ecl.ecl_por_produto,
            'por_rating': portfolio_ecl.ecl_por_rating,
            'metricas': {
                'pd_12m_medio': portfolio_ecl.average_pd_12m,
                'pd_lifetime_medio': portfolio_ecl.average_pd_lifetime,
                'lgd_medio': portfolio_ecl.average_lgd
            },
            'data_geracao': portfolio_ecl.data_calculo.isoformat()
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
    ead: float,
    dias_atraso: int = 0
) -> float:
    """
    Convenience function to calculate ECL.
    
    Args:
        cliente_id: Client ID
        produto: Product name
        prinad: PRINAD score (0-100)
        ead: Exposure at Default
        dias_atraso: Days past due
        
    Returns:
        ECL value
    """
    result = get_ecl_engine().calcular_ecl_individual_simples(
        cliente_id=cliente_id,
        produto=produto,
        prinad=prinad,
        ead=ead,
        dias_atraso=dias_atraso
    )
    return result.ecl


if __name__ == "__main__":
    # Example calculation with new methodology
    print("=" * 70)
    print("ECL Engine v2.0 - BACEN 4966 Compliant")
    print("=" * 70)
    
    engine = ECLEngine()
    
    # Test 1: Simple calculation
    result = engine.calcular_ecl_individual_simples(
        cliente_id="12345678901",
        produto="consignado",
        prinad=15.0,
        ead=50000,
        dias_atraso=0
    )
    
    print("\nTest 1: Single Exposure (Stage 1)")
    print(f"  Cliente: {result.cliente_id}")
    print(f"  Produto: {result.produto}")
    print(f"  PRINAD: {result.prinad}% → Rating: {result.rating}")
    print(f"  PD 12m: {result.pd_12m:.4%}")
    print(f"  PD Lifetime: {result.pd_lifetime:.4%}")
    print(f"  LGD: {result.lgd:.2%}")
    print(f"  EAD: R$ {result.ead:,.2f}")
    print(f"  Stage: {result.stage}")
    print(f"  ECL 12m: R$ {result.ecl_12m:,.2f}")
    print(f"  ECL Lifetime: R$ {result.ecl_lifetime:,.2f}")
    print(f"  ECL Final: R$ {result.ecl:,.2f}")
    
    # Test 2: Stage 2 (delayed)
    result2 = engine.calcular_ecl_individual_simples(
        cliente_id="12345678902",
        produto="cartao_credito_rotativo",
        prinad=50.0,
        ead=10000,
        dias_atraso=45
    )
    
    print("\nTest 2: Delayed Payment (Stage 2)")
    print(f"  Rating: {result2.rating}, Stage: {result2.stage}")
    print(f"  PD used: {result2.pd_lifetime:.4%}")
    print(f"  ECL: R$ {result2.ecl:,.2f}")
    
    # Test 3: Client with drag effect
    exposicoes = [
        {'produto': 'consignado', 'limite_total': 100000, 'saldo_utilizado': 80000, 'dias_atraso': 95},
        {'produto': 'cartao_credito_rotativo', 'limite_total': 5000, 'saldo_utilizado': 3000, 'dias_atraso': 0},
        {'produto': 'imobiliario', 'limite_total': 200000, 'saldo_utilizado': 150000, 'dias_atraso': 0}
    ]
    
    results = engine.calcular_ecl_cliente(
        cliente_id="12345678903",
        exposicoes=exposicoes,
        prinad=85.0,
        aplicar_arrasto=True
    )
    
    print("\nTest 3: Client with Drag Effect")
    for r in results:
        print(f"  {r.produto}: Stage {r.stage} (arrasto: {r.arrasto}), ECL: R$ {r.ecl:,.2f}")
    
    total_ecl = sum(r.ecl for r in results)
    print(f"  Total ECL: R$ {total_ecl:,.2f}")
    
    print("\n" + "=" * 70)
    print("✓ All tests completed!")
    print("=" * 70)
