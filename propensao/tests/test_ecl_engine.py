"""
Unit tests for ECL Engine v2.0 (BACEN 4966 Compliant).
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from propensao.src.ecl_engine import (
    ECLEngine,
    ECLResult,
    PortfolioECL,
    IFRS9Stage,
    get_ecl_engine,
    calcular_ecl
)
from shared.utils import (
    PRODUTOS_CREDITO,
    get_rating_from_prinad,
    calcular_pd_por_rating
)


class TestECLEngineV2:
    """Test ECL Engine v2.0 (BACEN 4966)."""
    
    @pytest.fixture
    def engine(self):
        """Create ECL engine fixture."""
        return ECLEngine()
    
    def test_initialization(self, engine):
        """Engine should initialize correctly."""
        assert engine is not None
        assert engine.lgd_calculator is not None
        assert engine.stage_classifier is not None
    
    def test_calcular_ecl_individual_simples_stage1(self, engine):
        """Calculate ECL for Stage 1 exposure."""
        result = engine.calcular_ecl_individual_simples(
            cliente_id='123',
            produto='consignado',
            prinad=15.0,
            ead=50000,
            dias_atraso=0
        )
        
        assert isinstance(result, ECLResult)
        assert result.cliente_id == '123'
        assert result.produto == 'consignado'
        assert result.ead == 50000
        assert result.ecl > 0
        assert result.stage == 1
        assert result.rating == 'A3'
    
    def test_calcular_ecl_individual_simples_stage2(self, engine):
        """ECL should be higher for Stage 2 (delayed)."""
        result_s1 = engine.calcular_ecl_individual_simples(
            cliente_id='123',
            produto='consignado',
            prinad=15.0,
            ead=50000,
            dias_atraso=0
        )
        result_s2 = engine.calcular_ecl_individual_simples(
            cliente_id='123',
            produto='consignado',
            prinad=15.0,
            ead=50000,
            dias_atraso=45  # Triggers Stage 2
        )
        
        assert result_s1.stage == 1
        assert result_s2.stage == 2
        assert result_s2.ecl > result_s1.ecl
    
    def test_calcular_ecl_individual_simples_stage3(self, engine):
        """Stage 3 should have highest ECL."""
        result_s3 = engine.calcular_ecl_individual_simples(
            cliente_id='123',
            produto='consignado',
            prinad=90.0,
            ead=50000,
            dias_atraso=95  # Triggers Stage 3
        )
        
        assert result_s3.stage == 3
        assert result_s3.ecl > 0
        # Stage 3 uses max LGD (1.5x)
        assert result_s3.lgd > 0.25  # Normal consignado LGD
    
    def test_calcular_ecl_individual_full(self, engine):
        """Full ECL calculation with limite_total and saldo_utilizado."""
        result = engine.calcular_ecl_individual(
            cliente_id='123',
            produto='cartao_credito_rotativo',
            prinad=30.0,
            limite_total=10000,
            saldo_utilizado=5000,
            dias_atraso=0
        )
        
        assert result.ead > 5000  # EAD includes CCF on unused limit
        assert result.ead < 10000  # But not full limit
        assert result.ecl > 0
    
    def test_calcular_ecl_individual_with_arrasto(self, engine):
        """Drag effect should force Stage 3."""
        result = engine.calcular_ecl_individual(
            cliente_id='123',
            produto='consignado',
            prinad=10.0,  # Low risk
            limite_total=50000,
            saldo_utilizado=40000,
            dias_atraso=0,  # No delay
            arrasto=True  # Drag from another product
        )
        
        assert result.stage == 3
        assert result.arrasto == True
    
    def test_pd_calibration(self, engine):
        """PD should be properly calibrated per rating band."""
        # A1 rating (PRINAD 0-5)
        result_a1 = engine.calcular_ecl_individual_simples(
            cliente_id='1', produto='consignado', prinad=2.0, ead=50000
        )
        # D rating (PRINAD 85-95)
        result_d = engine.calcular_ecl_individual_simples(
            cliente_id='2', produto='consignado', prinad=90.0, ead=50000
        )
        
        assert result_a1.rating == 'A1'
        assert result_d.rating == 'D'
        assert result_a1.pd_12m < result_d.pd_12m
        assert result_a1.pd_lifetime < result_d.pd_lifetime
    
    def test_calcular_ecl_cliente_with_arrasto(self, engine):
        """Client ECL with drag effect."""
        exposicoes = [
            {'produto': 'consignado', 'limite_total': 100000, 'saldo_utilizado': 80000, 'dias_atraso': 95},
            {'produto': 'cartao_credito_rotativo', 'limite_total': 5000, 'saldo_utilizado': 3000, 'dias_atraso': 0},
            {'produto': 'imobiliario', 'limite_total': 200000, 'saldo_utilizado': 150000, 'dias_atraso': 0}
        ]
        
        results = engine.calcular_ecl_cliente(
            cliente_id='123',
            exposicoes=exposicoes,
            prinad=85.0,
            aplicar_arrasto=True
        )
        
        assert len(results) == 3
        # All should be Stage 3 due to drag
        assert all(r.stage == 3 for r in results)
        # First product is the trigger
        assert results[0].arrasto == False
        # Others are dragged
        assert results[1].arrasto == True
        assert results[2].arrasto == True
    
    def test_calcular_ecl_portfolio(self, engine):
        """Calculate ECL for portfolio with new columns."""
        df = pd.DataFrame([
            {'cliente_id': '1', 'produto': 'consignado', 'prinad': 10, 'limite_total': 50000, 'saldo_utilizado': 50000, 'dias_atraso': 0},
            {'cliente_id': '2', 'produto': 'cartao_credito_rotativo', 'prinad': 50, 'limite_total': 15000, 'saldo_utilizado': 10000, 'dias_atraso': 45},
            {'cliente_id': '3', 'produto': 'imobiliario', 'prinad': 80, 'limite_total': 200000, 'saldo_utilizado': 150000, 'dias_atraso': 100}
        ])
        
        portfolio, df_results = engine.calcular_ecl_portfolio(df, aplicar_arrasto=False)
        
        assert isinstance(portfolio, PortfolioECL)
        assert portfolio.total_ead > 0
        assert portfolio.total_ecl > 0
        assert portfolio.count_exposures == 3
        assert len(df_results) == 3
        
        # Check new columns exist
        assert 'pd_12m' in df_results.columns
        assert 'pd_lifetime' in df_results.columns
        assert 'stage' in df_results.columns
        assert 'rating' in df_results.columns
    
    def test_simular_otimizacao(self, engine):
        """Simulate ECL savings from optimization."""
        df_atual = pd.DataFrame([
            {'cliente_id': '1', 'produto': 'consignado', 'prinad': 10, 'limite_total': 100000, 'saldo_utilizado': 100000, 'dias_atraso': 0}
        ])
        df_otimizado = pd.DataFrame([
            {'cliente_id': '1', 'produto': 'consignado', 'prinad': 10, 'limite_total': 50000, 'saldo_utilizado': 50000, 'dias_atraso': 0}
        ])
        
        resultado = engine.simular_otimizacao(df_atual, df_otimizado)
        
        assert resultado['economia_absoluta'] > 0
        assert resultado['economia_percentual'] > 0


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_get_ecl_engine(self):
        """Should return engine instance."""
        engine = get_ecl_engine()
        assert isinstance(engine, ECLEngine)
    
    def test_calcular_ecl_function(self):
        """Convenience function should work."""
        ecl = calcular_ecl('123', 'consignado', 15.0, 50000)
        assert ecl > 0
    
    def test_calcular_ecl_function_with_dias_atraso(self):
        """Convenience function with dias_atraso."""
        ecl_normal = calcular_ecl('123', 'consignado', 15.0, 50000, dias_atraso=0)
        ecl_delayed = calcular_ecl('123', 'consignado', 15.0, 50000, dias_atraso=95)
        
        assert ecl_delayed > ecl_normal


class TestPDCalibration:
    """Test PD calibration per rating."""
    
    def test_pd_floor(self):
        """PD should have BACEN floor of 0.03%."""
        result = calcular_pd_por_rating(0.0)  # Lowest PRINAD
        assert result['pd_12m'] >= 0.0003
    
    def test_pd_increases_with_prinad(self):
        """Higher PRINAD should have higher PD."""
        pds = []
        for prinad in [5, 15, 35, 55, 75, 90]:
            result = calcular_pd_por_rating(prinad)
            pds.append(result['pd_12m'])
        
        # PD should be monotonically increasing
        for i in range(1, len(pds)):
            assert pds[i] >= pds[i-1]
    
    def test_pd_lifetime_higher_than_12m(self):
        """Lifetime PD should always be >= 12m PD."""
        for prinad in [5, 25, 50, 75, 95]:
            result = calcular_pd_por_rating(prinad)
            assert result['pd_lifetime'] >= result['pd_12m']


class TestRatingConversion:
    """Test PRINAD to Rating conversion."""
    
    @pytest.mark.parametrize("prinad,expected_rating", [
        (2.0, 'A1'),
        (10.0, 'A2'),
        (20.0, 'A3'),
        (30.0, 'B1'),
        (40.0, 'B2'),
        (50.0, 'B3'),
        (60.0, 'C1'),
        (70.0, 'C2'),
        (80.0, 'C3'),
        (90.0, 'D'),
        (98.0, 'DEFAULT')
    ])
    def test_rating_from_prinad(self, prinad, expected_rating):
        """Rating should match PRINAD bands."""
        rating = get_rating_from_prinad(prinad)
        assert rating == expected_rating
