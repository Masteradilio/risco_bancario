"""
Tests for the Historical Penalty Calculator module.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from historical_penalty import (
    HistoricalPenaltyCalculator,
    DelinquencyLevel,
    calculate_historical_penalty
)


class TestHistoricalPenaltyCalculator:
    """Test suite for HistoricalPenaltyCalculator."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = HistoricalPenaltyCalculator(
            forgiveness_months=12,
            max_penalty=1.5
        )
    
    def test_clean_client_no_penalty(self, sample_behavioral_data_clean):
        """Test that a clean client has no penalty."""
        analysis = self.calculator.calculate(sample_behavioral_data_clean)
        
        assert analysis.penalidade == 0.0
        assert analysis.nivel_delinquencia == DelinquencyLevel.NONE
        assert analysis.elegivel_perdao == True
    
    def test_delinquent_client_has_penalty(self, sample_behavioral_data_delinquent):
        """Test that a delinquent client has penalty."""
        analysis = self.calculator.calculate(sample_behavioral_data_delinquent)
        
        assert analysis.penalidade > 0.0
        assert analysis.penalidade <= 1.5
        assert analysis.nivel_delinquencia in [
            DelinquencyLevel.SHORT_TERM,
            DelinquencyLevel.LONG_TERM,
            DelinquencyLevel.SEVERE
        ]
    
    def test_penalty_capped_at_max(self):
        """Test that penalty is capped at max_penalty."""
        # Create extreme delinquent data
        extreme_data = {
            'v205': 100000.0, 'v210': 100000.0, 'v220': 100000.0, 'v230': 100000.0,
            'v240': 100000.0, 'v245': 100000.0, 'v250': 100000.0, 'v255': 100000.0,
            'v260': 100000.0, 'v270': 100000.0, 'v280': 100000.0, 'v290': 100000.0
        }
        
        analysis = self.calculator.calculate(extreme_data)
        
        assert analysis.penalidade <= 1.5
    
    def test_apply_penalty_multiplies_pd(self, sample_behavioral_data_delinquent):
        """Test that apply_penalty correctly multiplies PD."""
        pd_base = 20.0
        
        prinad, analysis = self.calculator.apply_penalty(pd_base, sample_behavioral_data_delinquent)
        
        expected = pd_base * (1 + analysis.penalidade)
        assert prinad == min(100.0, expected)
    
    def test_apply_penalty_capped_at_100(self, sample_behavioral_data_delinquent):
        """Test that final PRINAD is capped at 100%."""
        pd_base = 80.0
        
        prinad, _ = self.calculator.apply_penalty(pd_base, sample_behavioral_data_delinquent)
        
        assert prinad <= 100.0
    
    def test_short_term_delinquency_detection(self):
        """Test detection of short-term delinquency."""
        data = {
            'v205': 1000.0, 'v210': 500.0, 'v220': 0.0, 'v230': 0.0,
            'v240': 0.0, 'v245': 0.0, 'v250': 0.0, 'v255': 0.0,
            'v260': 0.0, 'v270': 0.0, 'v280': 0.0, 'v290': 0.0
        }
        
        analysis = self.calculator.calculate(data)
        
        assert analysis.nivel_delinquencia == DelinquencyLevel.SHORT_TERM
    
    def test_severe_delinquency_detection(self):
        """Test detection of severe delinquency."""
        data = {
            'v205': 0.0, 'v210': 0.0, 'v220': 0.0, 'v230': 0.0,
            'v240': 0.0, 'v245': 5000.0, 'v250': 5000.0, 'v255': 5000.0,
            'v260': 5000.0, 'v270': 5000.0, 'v280': 5000.0, 'v290': 10000.0
        }
        
        analysis = self.calculator.calculate(data)
        
        assert analysis.nivel_delinquencia == DelinquencyLevel.SEVERE
    
    def test_convenience_function(self, sample_behavioral_data_clean):
        """Test the convenience function."""
        penalty, details = calculate_historical_penalty(sample_behavioral_data_clean)
        
        assert isinstance(penalty, float)
        assert isinstance(details, dict)
        assert 'nivel' in details


class TestDelinquencyLevels:
    """Test suite for DelinquencyLevel enum."""
    
    def test_enum_values(self):
        """Test that all expected enum values exist."""
        assert DelinquencyLevel.NONE.value == "sem_atraso"
        assert DelinquencyLevel.SHORT_TERM.value == "curto_prazo"
        assert DelinquencyLevel.LONG_TERM.value == "longo_prazo"
        assert DelinquencyLevel.SEVERE.value == "severo"
        assert DelinquencyLevel.DEFAULT.value == "inadimplente"
