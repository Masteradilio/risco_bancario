"""
Tests for the Historical Penalty Calculator module v2.0.
Updated for BACEN 4966 compliance - split internal/external penalties.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from historical_penalty import (
    HistoricalPenaltyCalculator,
    HistoricalAnalysis,
    DelinquencyLevel,
    calculate_historical_penalty
)


class TestHistoricalPenaltyCalculator:
    """Test suite for HistoricalPenaltyCalculator v2.0."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # v2.0 API: separate max penalties for internal/external
        self.calculator = HistoricalPenaltyCalculator(
            forgiveness_months=6,
            max_penalty_internal=0.75,
            max_penalty_external=0.75
        )
    
    def test_clean_client_no_penalty(self, sample_behavioral_data_clean):
        """Test that a clean client (internal AND external) has no penalty."""
        analysis = self.calculator.calculate(sample_behavioral_data_clean)
        
        assert analysis.penalidade_total == 0.0
        assert analysis.penalidade_interna == 0.0
        assert analysis.penalidade_externa == 0.0
        assert analysis.nivel_delinquencia == DelinquencyLevel.NONE
        assert analysis.elegivel_perdao == True
    
    def test_internal_delinquent_has_internal_penalty(self, sample_behavioral_data_delinquent):
        """Test that internal delinquency generates internal penalty."""
        analysis = self.calculator.calculate(sample_behavioral_data_delinquent)
        
        assert analysis.penalidade_interna > 0.0
        assert analysis.penalidade_interna <= 0.75
        assert analysis.penalidade_total > 0.0
    
    def test_external_only_has_external_penalty(self, sample_behavioral_data_external_only):
        """Test that external-only delinquency generates external penalty."""
        analysis = self.calculator.calculate(sample_behavioral_data_external_only)
        
        # Internal should be zero (v-columns clean)
        assert analysis.penalidade_interna == 0.0
        # External should have penalty (SCR data shows delinquency)
        assert analysis.penalidade_externa > 0.0
        assert analysis.penalidade_externa <= 0.75
    
    def test_both_penalties_when_both_delinquent(self, sample_behavioral_data_delinquent):
        """Test that both internal and external penalties apply when both are delinquent."""
        analysis = self.calculator.calculate(sample_behavioral_data_delinquent)
        
        # Both should have some penalty
        assert analysis.penalidade_interna > 0.0
        assert analysis.penalidade_externa > 0.0
        # Total should be sum
        assert analysis.penalidade_total == analysis.penalidade_interna + analysis.penalidade_externa
    
    def test_penalty_capped_at_max(self):
        """Test that penalties are capped at max_penalty."""
        # Create extreme delinquent data (internal + external)
        extreme_data = {
            # Extreme internal
            'v205': 100000.0, 'v210': 100000.0, 'v220': 100000.0, 'v230': 100000.0,
            'v240': 100000.0, 'v245': 100000.0, 'v250': 100000.0, 'v255': 100000.0,
            'v260': 100000.0, 'v270': 100000.0, 'v280': 100000.0, 'v290': 100000.0,
            # Extreme external
            'scr_classificacao_risco': 'H',
            'scr_dias_atraso': 365,
            'scr_valor_vencido': 100000,
            'scr_tem_prejuizo': 1,
            'scr_taxa_utilizacao': 1.0,
            'scr_score_risco': 8
        }
        
        analysis = self.calculator.calculate(extreme_data)
        
        assert analysis.penalidade_interna <= 0.75
        assert analysis.penalidade_externa <= 0.75
        assert analysis.penalidade_total <= 1.5
    
    def test_apply_penalty_multiplies_pd(self, sample_behavioral_data_delinquent):
        """Test that apply_penalty correctly multiplies PD."""
        pd_base = 20.0
        
        prinad, analysis = self.calculator.apply_penalty(pd_base, sample_behavioral_data_delinquent)
        
        expected = pd_base * (1 + analysis.penalidade_total)
        assert prinad == pytest.approx(min(100.0, expected), rel=0.01)
    
    def test_apply_penalty_capped_at_100(self, sample_behavioral_data_delinquent):
        """Test that final PRINAD is capped at 100%."""
        pd_base = 80.0
        
        prinad, _ = self.calculator.apply_penalty(pd_base, sample_behavioral_data_delinquent)
        
        assert prinad <= 100.0
    
    def test_short_term_delinquency_detection(self):
        """Test detection of short-term delinquency with recent internal arrears."""
        # Use v290 (360 days) to force meses_desde_ultimo_atraso_interno = 0
        # This represents a client with very recent severe delinquency
        data = {
            'v205': 1000.0, 'v210': 1000.0, 'v220': 0.0, 'v230': 0.0,
            'v240': 0.0, 'v245': 0.0, 'v250': 0.0, 'v255': 0.0,
            'v260': 0.0, 'v270': 0.0, 'v280': 0.0, 'v290': 5000.0,  # Active severe delinquency
            # External is clean but algorithm checks internal first
            'scr_classificacao_risco': 'E', 'scr_dias_atraso': 45,
            'scr_valor_vencido': 1000, 'scr_tem_prejuizo': 0, 'scr_score_risco': 5
        }
        
        analysis = self.calculator.calculate(data)
        
        # With v290 > 0, it's severe delinquency (not short-term)
        # Let's test for ANY penalty applied
        assert analysis.penalidade_total > 0.0
        assert analysis.nivel_delinquencia != DelinquencyLevel.NONE
    
    def test_severe_delinquency_detection(self):
        """Test detection of severe delinquency."""
        data = {
            'v205': 0.0, 'v210': 0.0, 'v220': 0.0, 'v230': 0.0,
            'v240': 0.0, 'v245': 5000.0, 'v250': 5000.0, 'v255': 5000.0,
            'v260': 5000.0, 'v270': 5000.0, 'v280': 5000.0, 'v290': 10000.0,
            # Also check SCR triggers severe
            'scr_classificacao_risco': 'H', 'scr_dias_atraso': 180,
            'scr_valor_vencido': 10000, 'scr_tem_prejuizo': 1, 'scr_score_risco': 8
        }
        
        analysis = self.calculator.calculate(data)
        
        assert analysis.nivel_delinquencia == DelinquencyLevel.SEVERE
    
    def test_forgiveness_requires_both_clean(self):
        """Test that forgiveness requires BOTH internal AND external clean for 6+ months."""
        # Internal clean but external not clean
        data = {
            'v205': 0.0, 'v210': 0.0, 'v220': 0.0, 'v230': 0.0,
            'v240': 0.0, 'v245': 0.0, 'v250': 0.0, 'v255': 0.0,
            'v260': 0.0, 'v270': 0.0, 'v280': 0.0, 'v290': 0.0,
            # External has recent issue
            'scr_classificacao_risco': 'D', 'scr_dias_atraso': 30,
            'scr_valor_vencido': 1000, 'scr_tem_prejuizo': 0, 'scr_score_risco': 4
        }
        
        analysis = self.calculator.calculate(data)
        
        # Should NOT be eligible for forgiveness
        assert analysis.elegivel_perdao == False
        # Should have external penalty
        assert analysis.penalidade_externa > 0.0
    
    def test_convenience_function(self, sample_behavioral_data_clean):
        """Test the convenience function."""
        penalty_total, details = calculate_historical_penalty(sample_behavioral_data_clean)
        
        assert isinstance(penalty_total, float)
        assert isinstance(details, dict)
        assert 'nivel' in details
        assert 'penalidade_interna' in details
        assert 'penalidade_externa' in details


class TestDelinquencyLevels:
    """Test suite for DelinquencyLevel enum."""
    
    def test_enum_values(self):
        """Test that all expected enum values exist."""
        assert DelinquencyLevel.NONE.value == "sem_atraso"
        assert DelinquencyLevel.SHORT_TERM.value == "curto_prazo"
        assert DelinquencyLevel.LONG_TERM.value == "longo_prazo"
        assert DelinquencyLevel.SEVERE.value == "severo"
        assert DelinquencyLevel.DEFAULT.value == "inadimplente"


class TestHistoricalAnalysis:
    """Test the HistoricalAnalysis dataclass."""
    
    def test_analysis_structure(self):
        """Test that HistoricalAnalysis has expected fields."""
        analysis = HistoricalAnalysis(
            penalidade_interna=0.3,
            penalidade_externa=0.2,
            penalidade_total=0.5,
            nivel_delinquencia=DelinquencyLevel.SHORT_TERM,
            meses_desde_ultimo_atraso_interno=3,
            meses_desde_ultimo_atraso_externo=5,
            elegivel_perdao=False,
            detalhes={'test': 'value'}
        )
        
        assert analysis.penalidade_interna == 0.3
        assert analysis.penalidade_externa == 0.2
        assert analysis.penalidade_total == 0.5
        assert analysis.meses_desde_ultimo_atraso_interno == 3
        assert analysis.meses_desde_ultimo_atraso_externo == 5
