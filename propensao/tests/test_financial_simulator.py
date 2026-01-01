"""
Unit tests for Financial Simulator.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from propensao.src.financial_simulator import (
    FinancialSimulator,
    CenarioTipo,
    ParametrosCenario,
    ResultadoSimulacao,
    RelatorioImpacto,
    get_financial_simulator
)


class TestFinancialSimulator:
    """Test Financial Simulator."""
    
    @pytest.fixture
    def simulator(self):
        """Create simulator fixture."""
        return FinancialSimulator('3T2025')
    
    def test_initialization(self, simulator):
        """Simulator should initialize correctly."""
        assert simulator is not None
        assert simulator.trimestre_base == '3T2025'
    
    def test_baseline_data(self, simulator):
        """Should have baseline data."""
        assert simulator.baseline['carteira_credito'] > 10_000_000_000  # > R$ 10 bi
        assert simulator.baseline['inadimplencia'] < 0.10  # < 10%
    
    def test_cenarios_definidos(self, simulator):
        """All scenarios should be defined."""
        assert len(simulator.CENARIOS) == 3
        assert CenarioTipo.CONSERVADOR in simulator.CENARIOS
        assert CenarioTipo.MODERADO in simulator.CENARIOS
        assert CenarioTipo.OTIMISTA in simulator.CENARIOS
    
    def test_simular_cenario_conservador(self, simulator):
        """Conservative scenario should work."""
        resultado = simulator.simular_cenario(CenarioTipo.CONSERVADOR)
        
        assert isinstance(resultado, ResultadoSimulacao)
        assert resultado.cenario == "Conservador"
        assert resultado.economia_ecl >= 0
        assert resultado.impacto_roe_pp >= 0
    
    def test_simular_cenario_moderado(self, simulator):
        """Moderate scenario should work."""
        resultado = simulator.simular_cenario(CenarioTipo.MODERADO)
        
        assert resultado.cenario == "Moderado"
        assert resultado.ecl_projetado < resultado.ecl_atual
    
    def test_simular_cenario_otimista(self, simulator):
        """Optimistic scenario should work."""
        resultado = simulator.simular_cenario(CenarioTipo.OTIMISTA)
        
        assert resultado.cenario == "Otimista"
        assert resultado.impacto_roe_pp > 0  # Should improve ROE
    
    def test_economia_ecl_positiva(self, simulator):
        """ECL savings should be positive."""
        resultado = simulator.simular_cenario(CenarioTipo.CONSERVADOR)
        
        assert resultado.economia_ecl > 0
        assert resultado.economia_ecl_percentual > 0
    
    def test_capital_liberado(self, simulator):
        """Should liberate capital."""
        resultado = simulator.simular_cenario(CenarioTipo.CONSERVADOR)
        
        assert resultado.capital_liberado > 0
        assert resultado.capital_liberado_percentual > 0
    
    def test_inadimplencia_nao_piora(self, simulator):
        """Default rate should not increase."""
        resultado = simulator.simular_cenario(CenarioTipo.MODERADO)
        
        assert resultado.inadimplencia_projetada <= resultado.inadimplencia_atual
    
    def test_simular_todos_cenarios(self, simulator):
        """Should simulate all scenarios."""
        relatorio = simulator.simular_todos_cenarios()
        
        assert isinstance(relatorio, RelatorioImpacto)
        assert len(relatorio.resultados) == 3
        assert relatorio.recomendacao is not None
    
    def test_calcular_ecl_portfolio(self, simulator):
        """Should calculate portfolio ECL."""
        ecl = simulator.calcular_ecl_portfolio(
            limite_total=1_000_000_000,  # R$ 1 bi
            pd_medio=0.03,  # 3% default
            lgd_medio=0.40  # 40% LGD
        )
        
        assert ecl == 1_000_000_000 * 0.03 * 0.40


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_get_financial_simulator(self):
        """Should return simulator instance."""
        sim = get_financial_simulator()
        assert isinstance(sim, FinancialSimulator)
