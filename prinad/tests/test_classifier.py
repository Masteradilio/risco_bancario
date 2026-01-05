"""
Tests for the Classifier module (BACEN 4966 compliant).
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from classifier import RatingMapper, ClassificationResult


class TestRatingMapper:
    """Test suite for RatingMapper class (BACEN 4966 rating bands)."""
    
    def test_rating_a1_minimum(self):
        """Test A1 rating for minimum risk."""
        result = RatingMapper.get_rating(0.0)
        assert result['rating'] == 'A1'
        assert result['cor'] == 'verde'
    
    def test_rating_a1_boundary(self):
        """Test A1 rating at upper boundary."""
        result = RatingMapper.get_rating(4.99)
        assert result['rating'] == 'A1'
    
    def test_rating_a2(self):
        """Test A2 rating."""
        result = RatingMapper.get_rating(10.0)
        assert result['rating'] == 'A2'
        assert result['cor'] == 'verde'
    
    def test_rating_a3(self):
        """Test A3 rating."""
        result = RatingMapper.get_rating(20.0)
        assert result['rating'] == 'A3'
        assert result['cor'] == 'verde'
    
    def test_rating_b1(self):
        """Test B1 rating."""
        result = RatingMapper.get_rating(30.0)
        assert result['rating'] == 'B1'
        assert result['cor'] == 'amarelo'
    
    def test_rating_b2(self):
        """Test B2 rating."""
        result = RatingMapper.get_rating(40.0)
        assert result['rating'] == 'B2'
        assert result['cor'] == 'amarelo'
    
    def test_rating_b3(self):
        """Test B3 rating."""
        result = RatingMapper.get_rating(50.0)
        assert result['rating'] == 'B3'
        assert result['cor'] == 'laranja'
    
    def test_rating_c1(self):
        """Test C1 rating."""
        result = RatingMapper.get_rating(60.0)
        assert result['rating'] == 'C1'
        assert result['cor'] == 'vermelho'
    
    def test_rating_c2(self):
        """Test C2 rating."""
        result = RatingMapper.get_rating(70.0)
        assert result['rating'] == 'C2'
        assert result['cor'] == 'vermelho'
    
    def test_rating_c3(self):
        """Test C3 rating."""
        result = RatingMapper.get_rating(80.0)
        assert result['rating'] == 'C3'
        assert result['cor'] == 'vermelho'
    
    def test_rating_d_pre_default(self):
        """Test D rating for pre-default."""
        result = RatingMapper.get_rating(90.0)
        assert result['rating'] == 'D'
        assert result['cor'] == 'preto'
    
    def test_rating_default(self):
        """Test DEFAULT rating at 95+."""
        result = RatingMapper.get_rating(96.0)
        assert result['rating'] == 'DEFAULT'
        assert result['cor'] == 'preto'
    
    def test_rating_at_100(self):
        """Test DEFAULT rating at 100%."""
        result = RatingMapper.get_rating(100.0)
        assert result['rating'] == 'DEFAULT'
    
    def test_rating_clamps_negative(self):
        """Test that negative values are handled."""
        result = RatingMapper.get_rating(-5.0)
        assert result['rating'] == 'A1'
    
    def test_rating_clamps_above_100(self):
        """Test that values above 100 are handled."""
        result = RatingMapper.get_rating(150.0)
        # Clamped to 100, which is DEFAULT
        assert result['rating'] in ['D', 'DEFAULT']
    
    def test_rating_has_action(self):
        """Test that rating includes action suggestion."""
        result = RatingMapper.get_rating(50.0)
        assert 'acao_sugerida' in result
        assert len(result['acao_sugerida']) > 0


class TestClassificationResult:
    """Test suite for ClassificationResult dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary (BACEN 4966 compliant)."""
        result = ClassificationResult(
            cpf="12345678901",
            prinad=25.5,
            rating="B1",
            rating_descricao="Risco Baixo-Moderado",
            cor="amarelo",
            pd_base=20.0,
            pd_12m=0.025,        # BACEN 4966
            pd_lifetime=0.075,   # BACEN 4966
            penalidade_historica=0.275,
            peso_atual=0.5,
            peso_historico=0.5,
            acao_sugerida="Análise padrão",
            explicacao_shap=[],
            timestamp="2026-01-02T22:00:00",
            model_version="2.0.0",
            estagio_pe=1              # IFRS 9 / Estágio PE
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['cpf'] == "12345678901"
        assert result_dict['prinad'] == 25.5
        assert result_dict['rating'] == "B1"
        assert 'pd_12m' in result_dict
        assert 'pd_lifetime' in result_dict
        assert 'estagio_pe' in result_dict


class TestRatingBoundaries:
    """Test suite for rating boundary conditions (BACEN 4966)."""
    
    @pytest.mark.parametrize("prinad,expected_rating", [
        (0.0, 'A1'),
        (4.9, 'A1'),
        (5.0, 'A2'),
        (14.9, 'A2'),
        (15.0, 'A3'),
        (24.9, 'A3'),
        (25.0, 'B1'),
        (34.9, 'B1'),
        (35.0, 'B2'),
        (44.9, 'B2'),
        (45.0, 'B3'),
        (54.9, 'B3'),
        (55.0, 'C1'),
        (64.9, 'C1'),
        (65.0, 'C2'),
        (74.9, 'C2'),
        (75.0, 'C3'),
        (84.9, 'C3'),
        (85.0, 'D'),
        (94.9, 'D'),
        (95.0, 'DEFAULT'),
        (100.0, 'DEFAULT'),
    ])
    def test_rating_boundaries(self, prinad, expected_rating):
        """Test exact rating boundaries."""
        result = RatingMapper.get_rating(prinad)
        assert result['rating'] == expected_rating, f"Expected {expected_rating} for PRINAD={prinad}"
    
    @pytest.mark.parametrize("prinad,expected_color", [
        (2.5, 'verde'),      # A1
        (10.0, 'verde'),     # A2
        (20.0, 'verde'),     # A3
        (30.0, 'amarelo'),   # B1
        (40.0, 'amarelo'),   # B2
        (50.0, 'laranja'),   # B3
        (60.0, 'vermelho'),  # C1
        (70.0, 'vermelho'),  # C2
        (80.0, 'vermelho'),  # C3
        (90.0, 'preto'),     # D
        (97.0, 'preto'),     # DEFAULT
    ])
    def test_rating_colors(self, prinad, expected_color):
        """Test rating colors."""
        result = RatingMapper.get_rating(prinad)
        assert result['cor'] == expected_color
