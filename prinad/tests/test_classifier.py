"""
Tests for the Classifier module.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from classifier import RatingMapper, ClassificationResult


class TestRatingMapper:
    """Test suite for RatingMapper class."""
    
    def test_rating_a1_minimum(self):
        """Test A1 rating for minimum risk."""
        result = RatingMapper.get_rating(0.0)
        assert result['rating'] == 'A1'
        assert result['cor'] == 'verde'
    
    def test_rating_a1_boundary(self):
        """Test A1 rating at upper boundary."""
        result = RatingMapper.get_rating(1.99)
        assert result['rating'] == 'A1'
    
    def test_rating_a2(self):
        """Test A2 rating."""
        result = RatingMapper.get_rating(3.0)
        assert result['rating'] == 'A2'
        assert result['cor'] == 'verde'
    
    def test_rating_a3(self):
        """Test A3 rating."""
        result = RatingMapper.get_rating(7.0)
        assert result['rating'] == 'A3'
        assert result['cor'] == 'verde'
    
    def test_rating_b1(self):
        """Test B1 rating."""
        result = RatingMapper.get_rating(15.0)
        assert result['rating'] == 'B1'
        assert result['cor'] == 'amarelo'
    
    def test_rating_b2(self):
        """Test B2 rating."""
        result = RatingMapper.get_rating(25.0)
        assert result['rating'] == 'B2'
        assert result['cor'] == 'amarelo'
    
    def test_rating_b3(self):
        """Test B3 rating."""
        result = RatingMapper.get_rating(40.0)
        assert result['rating'] == 'B3'
        assert result['cor'] == 'laranja'
    
    def test_rating_c1(self):
        """Test C1 rating."""
        result = RatingMapper.get_rating(60.0)
        assert result['rating'] == 'C1'
        assert result['cor'] == 'vermelho'
    
    def test_rating_c2(self):
        """Test C2 rating."""
        result = RatingMapper.get_rating(80.0)
        assert result['rating'] == 'C2'
        assert result['cor'] == 'vermelho'
    
    def test_rating_d(self):
        """Test D rating for maximum risk."""
        result = RatingMapper.get_rating(95.0)
        assert result['rating'] == 'D'
        assert result['cor'] == 'preto'
    
    def test_rating_d_at_100(self):
        """Test D rating at 100%."""
        result = RatingMapper.get_rating(100.0)
        assert result['rating'] == 'D'
    
    def test_rating_clamps_negative(self):
        """Test that negative values are handled."""
        result = RatingMapper.get_rating(-5.0)
        assert result['rating'] == 'A1'
    
    def test_rating_clamps_above_100(self):
        """Test that values above 100 are handled."""
        result = RatingMapper.get_rating(150.0)
        assert result['rating'] == 'D'
    
    def test_rating_has_action(self):
        """Test that rating includes action suggestion."""
        result = RatingMapper.get_rating(50.0)
        assert 'acao_sugerida' in result
        assert len(result['acao_sugerida']) > 0


class TestClassificationResult:
    """Test suite for ClassificationResult dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ClassificationResult(
            cpf="12345678901",
            prinad=25.5,
            rating="B2",
            rating_descricao="Risco Moderado",
            cor="amarelo",
            pd_base=20.0,
            penalidade_historica=0.275,
            peso_atual=0.5,
            peso_historico=0.5,
            acao_sugerida="Análise detalhada",
            explicacao_shap=[],
            timestamp="2024-12-23T22:00:00",
            model_version="1.0.0"
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['cpf'] == "12345678901"
        assert result_dict['prinad'] == 25.5
        assert result_dict['rating'] == "B2"


class TestRatingBoundaries:
    """Test suite for rating boundary conditions."""
    
    @pytest.mark.parametrize("prinad,expected_rating", [
        (0.0, 'A1'),
        (2.0, 'A2'),
        (5.0, 'A3'),
        (10.0, 'B1'),
        (20.0, 'B2'),
        (35.0, 'B3'),
        (50.0, 'C1'),
        (70.0, 'C2'),
        (90.0, 'D'),
    ])
    def test_rating_boundaries(self, prinad, expected_rating):
        """Test exact rating boundaries."""
        result = RatingMapper.get_rating(prinad)
        assert result['rating'] == expected_rating, f"Expected {expected_rating} for PRINAD={prinad}"
    
    @pytest.mark.parametrize("prinad,expected_color", [
        (5.0, 'verde'),
        (25.0, 'amarelo'),
        (40.0, 'laranja'),
        (60.0, 'vermelho'),
        (95.0, 'preto'),
    ])
    def test_rating_colors(self, prinad, expected_color):
        """Test rating colors."""
        result = RatingMapper.get_rating(prinad)
        assert result['cor'] == expected_color
