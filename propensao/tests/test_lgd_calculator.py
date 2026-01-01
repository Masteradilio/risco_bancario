"""
Unit tests for LGD Calculator (Dynamic).
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from propensao.src.lgd_calculator import (
    LGDCalculator,
    ResultadoLGD,
    ParametrosGarantia,
    get_lgd_calculator,
    get_lgd,
    calcular_lgd_operacao
)
from shared.utils import PRODUTOS_CREDITO, GARANTIA_POR_PRODUTO, IMPACTO_GARANTIA


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
    
    def test_parametros_carregados(self, calculator):
        """Parameters should be loaded for all guarantee types."""
        assert len(calculator.parametros_garantia) == len(IMPACTO_GARANTIA)
    
    def test_lgd_consignado_baixo(self, calculator_no_downturn):
        """Consignado should have low LGD (same impact as real estate)."""
        lgd = calculator_no_downturn.get_lgd_produto_default('consignado')
        assert lgd < 0.25  # Low due to payroll guarantee
    
    def test_lgd_imobiliario_baixo(self, calculator_no_downturn):
        """Imobiliario should have low LGD (real estate collateral)."""
        lgd = calculator_no_downturn.get_lgd_produto_default('imobiliario')
        assert lgd < 0.30
    
    def test_lgd_cartao_alto(self, calculator_no_downturn):
        """Credit card should have high LGD (unsecured)."""
        lgd = calculator_no_downturn.get_lgd_produto_default('cartao_credito_rotativo')
        assert lgd > 0.70
    
    def test_lgd_veiculo_medio(self, calculator_no_downturn):
        """Vehicle should have medium LGD."""
        lgd = calculator_no_downturn.get_lgd_produto_default('cred_veiculo')
        assert 0.30 <= lgd <= 0.50
    
    def test_lgd_energia_solar_igual_veiculo(self, calculator_no_downturn):
        """Energia solar should have same impact as vehicles."""
        lgd_solar = calculator_no_downturn.get_lgd_produto_default('energia_solar')
        lgd_veiculo = calculator_no_downturn.get_lgd_produto_default('cred_veiculo')
        # Should be similar (within 15%)
        assert abs(lgd_solar - lgd_veiculo) < 0.15
    
    def test_calcular_lgd_operacao(self, calculator):
        """Should calculate LGD for operation."""
        resultado = calculator.calcular_lgd_operacao(
            produto='cred_veiculo',
            valor_operacao=50000,
            valor_garantia=62500,  # 80% LTV
            prazo_total_meses=48
        )
        
        assert isinstance(resultado, ResultadoLGD)
        assert resultado.produto == 'cred_veiculo'
        assert resultado.tipo_garantia == 'veiculo'
        assert resultado.lgd_final > 0
    
    def test_lgd_aumenta_com_ltv(self, calculator_no_downturn):
        """Higher LTV should result in higher LGD."""
        # Low LTV (well covered)
        resultado_baixo = calculator_no_downturn.calcular_lgd_operacao(
            produto='cred_veiculo',
            valor_operacao=40000,
            valor_garantia=80000,  # 50% LTV
            prazo_total_meses=48
        )
        
        # High LTV (poorly covered)
        resultado_alto = calculator_no_downturn.calcular_lgd_operacao(
            produto='cred_veiculo',
            valor_operacao=72000,
            valor_garantia=80000,  # 90% LTV
            prazo_total_meses=48
        )
        
        assert resultado_alto.lgd_ajustado_ltv > resultado_baixo.lgd_ajustado_ltv
    
    def test_lgd_aumenta_com_prazo_depreciavel(self, calculator_no_downturn):
        """Longer term should increase LGD for depreciable assets."""
        # Short term
        resultado_curto = calculator_no_downturn.calcular_lgd_operacao(
            produto='cred_veiculo',
            valor_operacao=50000,
            valor_garantia=62500,
            prazo_total_meses=48,
            prazo_restante_meses=12
        )
        
        # Long term
        resultado_longo = calculator_no_downturn.calcular_lgd_operacao(
            produto='cred_veiculo',
            valor_operacao=50000,
            valor_garantia=62500,
            prazo_total_meses=48,
            prazo_restante_meses=48
        )
        
        assert resultado_longo.lgd_ajustado_prazo >= resultado_curto.lgd_ajustado_prazo
    
    def test_downturn_aumenta_lgd(self, calculator, calculator_no_downturn):
        """Downturn should increase LGD."""
        lgd_normal = calculator_no_downturn.get_lgd('cred_veiculo')
        lgd_downturn = calculator.get_lgd('cred_veiculo')
        
        assert lgd_downturn > lgd_normal
    
    def test_lgd_capped_at_100(self, calculator):
        """LGD should never exceed 100%."""
        resultado = calculator.calcular_lgd_operacao(
            produto='cheque_especial',  # High risk unsecured
            valor_operacao=100000,
            valor_garantia=0,
            prazo_total_meses=1
        )
        
        assert resultado.lgd_final <= 1.0
        assert resultado.lgd_downturn <= 1.0
    
    def test_get_parametros(self, calculator):
        """Should return parameters for product."""
        params = calculator.get_parametros('consignado')
        assert params is not None
        assert isinstance(params, ParametrosGarantia)
        assert params.tipo == 'consignacao'
    
    def test_get_all_lgd(self, calculator):
        """Should return LGD for all products."""
        all_lgd = calculator.get_all_lgd()
        assert len(all_lgd) == len(PRODUTOS_CREDITO)
    
    def test_calcular_perda_esperada(self, calculator):
        """Should calculate expected loss amount."""
        perda = calculator.calcular_perda_esperada_default(
            produto='consignado',
            ead=100000,
            valor_garantia=120000,
            prazo_meses=60
        )
        
        assert perda > 0
        assert perda < 100000  # Less than full exposure


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
    
    def test_calcular_lgd_operacao_function(self):
        """Convenience function for operation LGD."""
        resultado = calcular_lgd_operacao(
            produto='imobiliario',
            valor_operacao=300000,
            valor_garantia=400000,
            prazo_meses=360
        )
        
        assert isinstance(resultado, ResultadoLGD)
        assert resultado.lgd_final > 0
