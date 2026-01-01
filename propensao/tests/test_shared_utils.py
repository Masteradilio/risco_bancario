"""
Unit tests for shared utilities.
"""

import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    LGD_POR_PRODUTO,
    LIMITE_MAXIMO_MULTIPLO,
    COMPROMETIMENTO_MAXIMO_RENDA,
    LIMITE_MINIMO_PERCENTUAL,
    calcular_comprometimento_renda,
    calcular_limite_maximo_produto,
    get_lgd,
    calcular_ecl,
    get_ifrs9_stage,
    parse_month_from_filename
)


class TestConstants:
    """Test shared constants."""
    
    def test_produtos_credito_count(self):
        """Should have 9 products."""
        assert len(PRODUTOS_CREDITO) == 9
    
    def test_produtos_credito_content(self):
        """Should contain expected products."""
        expected = [
            'consignado', 'banparacard', 'cartao_credito_parcelado',
            'cartao_credito_rotativo', 'imobiliario', 'cred_veiculo',
            'energia_solar', 'cheque_especial', 'credito_sazonal'
        ]
        assert PRODUTOS_CREDITO == expected
    
    def test_lgd_values_range(self):
        """LGD values should be between 0 and 1."""
        for produto, lgd in LGD_POR_PRODUTO.items():
            assert 0 <= lgd <= 1, f"LGD for {produto} out of range"
    
    def test_limite_multiplos_positive(self):
        """Limit multipliers should be positive."""
        for produto, mult in LIMITE_MAXIMO_MULTIPLO.items():
            assert mult > 0, f"Multiplier for {produto} should be positive"
    
    def test_comprometimento_maximo(self):
        """Maximum commitment should be 70%."""
        assert COMPROMETIMENTO_MAXIMO_RENDA == 0.70
    
    def test_limite_minimo_percentual(self):
        """Minimum limit should be 30%."""
        assert LIMITE_MINIMO_PERCENTUAL == 0.30


class TestFunctions:
    """Test utility functions."""
    
    def test_calcular_comprometimento_normal(self):
        """Calculate commitment with normal values."""
        result = calcular_comprometimento_renda(5000, 10000)
        assert result == 0.5
    
    def test_calcular_comprometimento_zero_renda(self):
        """Should return 1.0 for zero income."""
        result = calcular_comprometimento_renda(5000, 0)
        assert result == 1.0
    
    def test_calcular_comprometimento_negative_renda(self):
        """Should return 1.0 for negative income."""
        result = calcular_comprometimento_renda(5000, -1000)
        assert result == 1.0
    
    def test_calcular_comprometimento_capped(self):
        """Should cap at 1.0 for values above 100%."""
        result = calcular_comprometimento_renda(15000, 10000)
        assert result == 1.0
    
    def test_calcular_limite_maximo_consignado(self):
        """Calculate max limit for consignado."""
        result = calcular_limite_maximo_produto('consignado', 10000)
        assert result == 150000  # 15x
    
    def test_calcular_limite_maximo_cartao(self):
        """Calculate max limit for credit card."""
        result = calcular_limite_maximo_produto('cartao_credito_rotativo', 10000)
        assert result == 15000  # 1.5x
    
    def test_get_lgd_valid_product(self):
        """Get LGD for valid product (consignado has low-medium LGD)."""
        result = get_lgd('consignado')
        assert result < 0.50  # Reasonable for secured product
    
    def test_get_lgd_invalid_product(self):
        """Get default LGD for invalid product."""
        result = get_lgd('produto_invalido')
        assert result >= 0.45  # Default unsecured or higher
    
    def test_calcular_ecl_basic(self):
        """Calculate basic ECL."""
        result = calcular_ecl(0.10, 0.40, 100000)
        assert result == pytest.approx(4000, rel=1e-6)  # 10% × 40% × 100k
    
    def test_calcular_ecl_zero_pd(self):
        """ECL should be zero if PD is zero."""
        result = calcular_ecl(0, 0.40, 100000)
        assert result == 0
    
    def test_get_ifrs9_stage_1(self):
        """Low risk should be Stage 1."""
        assert get_ifrs9_stage(10) == 1
        assert get_ifrs9_stage(19) == 1
    
    def test_get_ifrs9_stage_2(self):
        """Medium risk should be Stage 2."""
        assert get_ifrs9_stage(20) == 2
        assert get_ifrs9_stage(50) == 2
        assert get_ifrs9_stage(69) == 2
    
    def test_get_ifrs9_stage_3(self):
        """High risk should be Stage 3."""
        assert get_ifrs9_stage(70) == 3
        assert get_ifrs9_stage(100) == 3
    
    def test_parse_month_from_filename_valid(self):
        """Parse month from valid filename."""
        result = parse_month_from_filename('limites_012025.csv')
        assert result == '2025-01'
    
    def test_parse_month_from_filename_invalid(self):
        """Return None for invalid filename."""
        result = parse_month_from_filename('invalid_file.csv')
        assert result is None
