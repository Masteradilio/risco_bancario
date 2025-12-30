"""
Unit tests for ECL Engine.
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
from shared.utils import PRODUTOS_CREDITO


class TestECLEngine:
    """Test ECL Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create ECL engine fixture."""
        return ECLEngine()
    
    def test_initialization(self, engine):
        """Engine should initialize correctly."""
        assert engine is not None
        assert engine.lgd_calculator is not None
    
    def test_determinar_stage_1(self, engine):
        """Low risk should be Stage 1."""
        stage = engine.determinar_stage(prinad=10, dias_atraso=0)
        assert stage == IFRS9Stage.STAGE_1
    
    def test_determinar_stage_2_by_prinad(self, engine):
        """Medium PRINAD should be Stage 2."""
        stage = engine.determinar_stage(prinad=30, dias_atraso=0)
        assert stage == IFRS9Stage.STAGE_2
    
    def test_determinar_stage_2_by_atraso(self, engine):
        """30+ days overdue should be Stage 2."""
        stage = engine.determinar_stage(prinad=10, dias_atraso=45)
        assert stage == IFRS9Stage.STAGE_2
    
    def test_determinar_stage_3_by_prinad(self, engine):
        """High PRINAD should be Stage 3."""
        stage = engine.determinar_stage(prinad=80, dias_atraso=0)
        assert stage == IFRS9Stage.STAGE_3
    
    def test_determinar_stage_3_by_atraso(self, engine):
        """90+ days overdue should be Stage 3."""
        stage = engine.determinar_stage(prinad=10, dias_atraso=95)
        assert stage == IFRS9Stage.STAGE_3
    
    def test_calcular_ecl_individual_basic(self, engine):
        """Calculate ECL for single exposure."""
        result = engine.calcular_ecl_individual(
            cliente_id='123',
            produto='consignado',
            prinad=15.0,
            ead=50000
        )
        
        assert isinstance(result, ECLResult)
        assert result.cliente_id == '123'
        assert result.produto == 'consignado'
        assert result.ead == 50000
        assert result.ecl > 0
        assert result.stage == IFRS9Stage.STAGE_1
    
    def test_calcular_ecl_individual_stage2(self, engine):
        """ECL should be higher for Stage 2."""
        result_s1 = engine.calcular_ecl_individual(
            cliente_id='123',
            produto='consignado',
            prinad=10.0,
            ead=50000
        )
        result_s2 = engine.calcular_ecl_individual(
            cliente_id='123',
            produto='consignado',
            prinad=40.0,
            ead=50000
        )
        
        assert result_s2.stage == IFRS9Stage.STAGE_2
        assert result_s2.ecl > result_s1.ecl
    
    def test_calcular_ecl_pd_floor(self, engine):
        """PD should have minimum floor of 0.5%."""
        result = engine.calcular_ecl_individual(
            cliente_id='123',
            produto='consignado',
            prinad=0.0,  # Zero PRINAD
            ead=50000
        )
        
        assert result.pd >= 0.005  # Floor
        assert result.ecl > 0  # Should still have some ECL
    
    def test_calcular_ecl_cliente(self, engine):
        """Calculate ECL for multiple exposures."""
        exposicoes = [
            {'produto': 'consignado', 'ead': 50000, 'dias_atraso': 0},
            {'produto': 'cartao_credito', 'ead': 15000, 'dias_atraso': 0}
        ]
        
        results = engine.calcular_ecl_cliente(
            cliente_id='123',
            exposicoes=exposicoes,
            prinad=15.0
        )
        
        assert len(results) == 2
        assert all(isinstance(r, ECLResult) for r in results)
    
    def test_calcular_ecl_portfolio(self, engine):
        """Calculate ECL for portfolio."""
        df = pd.DataFrame([
            {'cliente_id': '1', 'produto': 'consignado', 'prinad': 10, 'ead': 50000, 'dias_atraso': 0},
            {'cliente_id': '2', 'produto': 'cartao_credito', 'prinad': 30, 'ead': 15000, 'dias_atraso': 0},
            {'cliente_id': '3', 'produto': 'imobiliario', 'prinad': 80, 'ead': 200000, 'dias_atraso': 100}
        ])
        
        portfolio, df_results = engine.calcular_ecl_portfolio(df)
        
        assert isinstance(portfolio, PortfolioECL)
        assert portfolio.total_ead == 265000
        assert portfolio.total_ecl > 0
        assert portfolio.count_exposures == 3
        assert len(df_results) == 3
    
    def test_simular_otimizacao(self, engine):
        """Simulate ECL savings from optimization."""
        df_atual = pd.DataFrame([
            {'cliente_id': '1', 'produto': 'consignado', 'prinad': 10, 'ead': 100000, 'dias_atraso': 0}
        ])
        df_otimizado = pd.DataFrame([
            {'cliente_id': '1', 'produto': 'consignado', 'prinad': 10, 'ead': 50000, 'dias_atraso': 0}
        ])
        
        resultado = engine.simular_otimizacao(df_atual, df_otimizado)
        
        assert resultado['economia_absoluta'] > 0
        assert resultado['economia_percentual'] > 0
        assert resultado['reducao_ead'] == 50000


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
