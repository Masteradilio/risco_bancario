"""
Unit tests for Limit Optimizer.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from propensao.src.limit_optimizer import (
    LimitOptimizer,
    AcaoLimite,
    RecomendacaoLimite,
    ClienteLimites,
    get_limit_optimizer
)
from shared.utils import PRODUTOS_CREDITO


class TestLimitOptimizer:
    """Test Limit Optimizer."""
    
    @pytest.fixture
    def optimizer(self):
        """Create optimizer fixture."""
        return LimitOptimizer()
    
    def test_initialization(self, optimizer):
        """Optimizer should initialize correctly."""
        assert optimizer is not None
    
    def test_avaliar_maxdebt_not_triggered(self, optimizer):
        """Max-debt rule should not trigger below 65%."""
        acoes = optimizer.avaliar_cliente_maxdebt(
            comprometimento=0.50,
            limites={'consignado': 100000},
            utilizacao={'consignado': 0}
        )
        
        assert len(acoes) == 0  # Rule not triggered
    
    def test_avaliar_maxdebt_triggered(self, optimizer):
        """Max-debt rule should trigger at 65%+."""
        acoes = optimizer.avaliar_cliente_maxdebt(
            comprometimento=0.68,
            limites={'consignado': 100000, 'cred_veiculo': 50000},
            utilizacao={'consignado': 0, 'cred_veiculo': 0}
        )
        
        assert 'consignado' in acoes
        assert acoes['consignado'][0] == AcaoLimite.REDUZIR
    
    def test_avaliar_maxdebt_cartao_exception(self, optimizer):
        """Credit card should be exception to max-debt rule."""
        acoes = optimizer.avaliar_cliente_maxdebt(
            comprometimento=0.70,
            limites={'cartao_credito': 15000, 'consignado': 100000},
            utilizacao={'cartao_credito': 0, 'consignado': 0}
        )
        
        assert acoes['cartao_credito'][0] == AcaoLimite.MANTER
        assert acoes['consignado'][0] == AcaoLimite.REDUZIR
    
    def test_avaliar_propensao_prinad_d(self, optimizer):
        """PRINAD D should zero limit."""
        acao, novo_limite, _ = optimizer.avaliar_propensao(
            produto='consignado',
            propensao=50,
            prinad=95,  # PRINAD D
            trimestres_sem_uso=0,
            limite_atual=100000
        )
        
        assert acao == AcaoLimite.ZERAR
        assert novo_limite == 0
    
    def test_avaliar_propensao_baixa_sem_uso(self, optimizer):
        """Low propensity + no use should reduce."""
        acao, novo_limite, _ = optimizer.avaliar_propensao(
            produto='consignado',
            propensao=20,  # Low
            prinad=15,
            trimestres_sem_uso=2,
            limite_atual=100000
        )
        
        assert acao == AcaoLimite.REDUZIR
        assert novo_limite == 30000  # 30% of original
    
    def test_avaliar_propensao_alta_bom_risco(self, optimizer):
        """High propensity + low risk should increase."""
        acao, novo_limite, _ = optimizer.avaliar_propensao(
            produto='consignado',
            propensao=80,  # High
            prinad=10,  # Low risk
            trimestres_sem_uso=0,
            limite_atual=100000
        )
        
        assert acao == AcaoLimite.AUMENTAR
        assert novo_limite == 120000  # 20% increase
    
    def test_avaliar_propensao_manter(self, optimizer):
        """Normal profile should maintain."""
        acao, novo_limite, _ = optimizer.avaliar_propensao(
            produto='consignado',
            propensao=50,  # Medium
            prinad=25,
            trimestres_sem_uso=0,
            limite_atual=100000
        )
        
        assert acao == AcaoLimite.MANTER
        assert novo_limite == 100000
    
    def test_otimizar_cliente(self, optimizer):
        """Optimize limits for client."""
        resultado = optimizer.otimizar_cliente(
            cliente_id='12345678901',
            renda_bruta=10000,
            parcelas_mensais=5000,
            limites={
                'consignado': 100000,
                'banparacard': 30000,
                'cartao_credito': 15000
            },
            propensoes={
                'consignado': 80,
                'banparacard': 20,
                'cartao_credito': 60
            },
            prinad=15.0,
            utilizacao_trimestral={
                'consignado': 0,
                'banparacard': 2,
                'cartao_credito': 0
            }
        )
        
        assert isinstance(resultado, ClienteLimites)
        assert resultado.cliente_id == '12345678901'
        assert resultado.comprometimento_atual == 0.5
        assert len(resultado.recomendacoes) > 0
    
    def test_aplicar_constraints(self, optimizer):
        """Income constraints should be applied."""
        rec = RecomendacaoLimite(
            cliente_id='123',
            produto='consignado',
            limite_atual=100000,
            limite_recomendado=200000,  # Very high
            acao=AcaoLimite.AUMENTAR,
            motivo='test',
            propensao=80,
            prinad=10,
            trimestres_sem_uso=0
        )
        
        resultado = optimizer.aplicar_constraints(
            recomendacoes=[rec],
            renda_bruta=10000,
            parcelas_atuais=5000
        )
        
        # Should be capped at max for product
        assert resultado[0].limite_recomendado <= 150000  # 15x salary
    
    def test_gerar_lista_notificacao(self, optimizer):
        """Generate notification list."""
        cliente = optimizer.otimizar_cliente(
            cliente_id='123',
            renda_bruta=10000,
            parcelas_mensais=3000,
            limites={'banparacard': 50000},
            propensoes={'banparacard': 10},
            prinad=15,
            utilizacao_trimestral={'banparacard': 3}
        )
        
        df_notif = optimizer.gerar_lista_notificacao([cliente])
        
        # If there are reductions, should have notifications
        assert df_notif.empty or 'cliente_id' in df_notif.columns


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_get_limit_optimizer(self):
        """Should return optimizer instance."""
        opt = get_limit_optimizer()
        assert isinstance(opt, LimitOptimizer)
