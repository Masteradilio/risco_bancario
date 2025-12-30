"""
Unit tests for LGD Calculator.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from propensao.src.lgd_calculator import (
    LGDCalculator,
    TipoGarantia,
    ParametrosLGD,
    get_lgd_calculator,
    get_lgd
)
from shared.utils import PRODUTOS_CREDITO


class TestLGDCalculator:
    """Test LGD Calculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create LGD calculator fixture."""
        return LGDCalculator(aplicar_downturn=True)
    
    @pytest.fixture
    def calculator_no_downturn(self):
        """Create LGD calculator without downturn."""
        return LGDCalculator(aplicar_downturn=False)
    
    def test_initialization(self, calculator):
        """Calculator should initialize correctly."""
        assert calculator is not None
        assert calculator.aplicar_downturn is True
    
    def test_lgd_all_products(self, calculator):
        """Should return LGD for all products."""
        for produto in PRODUTOS_CREDITO:
            lgd = calculator.get_lgd(produto)
            assert 0 < lgd <= 1, f"LGD for {produto} should be between 0 and 1"
    
    def test_lgd_consignado(self, calculator):
        """LGD for consignado should be around 40%."""
        lgd = calculator.get_lgd('consignado')
        assert 0.35 <= lgd <= 0.55  # Base + workout + downturn
    
    def test_lgd_imobiliario(self, calculator):
        """LGD for imobiliario should be lower (has collateral)."""
        lgd = calculator.get_lgd('imobiliario')
        assert lgd < 0.30  # Lower due to real estate collateral
    
    def test_lgd_cartao_credito(self, calculator):
        """LGD for credit card should be high (unsecured revolving)."""
        lgd = calculator.get_lgd('cartao_credito')
        assert lgd > 0.70  # High risk unsecured
    
    def test_downturn_increases_lgd(self, calculator, calculator_no_downturn):
        """Downturn should increase LGD."""
        for produto in PRODUTOS_CREDITO:
            lgd_dt = calculator.get_lgd(produto)
            lgd_no_dt = calculator_no_downturn.get_lgd(produto)
            assert lgd_dt >= lgd_no_dt, f"Downturn LGD should be >= base for {produto}"
    
    def test_lgd_capped_at_1(self, calculator):
        """LGD should never exceed 1."""
        for produto in PRODUTOS_CREDITO:
            lgd = calculator.get_lgd(produto)
            assert lgd <= 1.0, f"LGD for {produto} exceeds 1.0"
    
    def test_get_parametros(self, calculator):
        """Should return parameters for known products."""
        params = calculator.get_parametros('consignado')
        assert params is not None
        assert isinstance(params, ParametrosLGD)
        assert params.tipo_garantia == TipoGarantia.CONSIGNACAO
    
    def test_get_parametros_unknown(self, calculator):
        """Should return None for unknown products."""
        params = calculator.get_parametros('produto_inexistente')
        assert params is None
    
    def test_get_all_lgd(self, calculator):
        """Should return LGD dict for all products."""
        all_lgd = calculator.get_all_lgd()
        assert len(all_lgd) == len(PRODUTOS_CREDITO)
        for produto in PRODUTOS_CREDITO:
            assert produto in all_lgd
    
    def test_calcular_perda_esperada(self, calculator):
        """Should calculate expected loss amount."""
        perda = calculator.calcular_perda_esperada_default(
            produto='consignado',
            ead=100000
        )
        lgd = calculator.get_lgd('consignado')
        assert perda == 100000 * lgd
    
    def test_display_lgd_table(self, calculator):
        """Should generate displayable table."""
        table = calculator.display_lgd_table()
        assert isinstance(table, str)
        assert 'consignado' in table
        assert 'LGD' in table


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_get_lgd_calculator(self):
        """Should return calculator instance."""
        calc = get_lgd_calculator()
        assert isinstance(calc, LGDCalculator)
    
    def test_get_lgd_function(self):
        """Convenience function should work."""
        lgd = get_lgd('consignado')
        assert 0 < lgd <= 1
