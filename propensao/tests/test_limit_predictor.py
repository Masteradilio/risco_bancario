"""
Unit tests for Limit Predictor.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from propensao.src.limit_predictor import (
    LimitPredictor,
    PrevisaoLimite,
    ListaNotificacao,
    get_limit_predictor
)


class TestLimitPredictor:
    """Test Limit Predictor."""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor fixture."""
        return LimitPredictor()
    
    def test_initialization(self, predictor):
        """Predictor should initialize correctly."""
        assert predictor is not None
        assert predictor.modelo_dir.exists()
    
    def test_calcular_tendencia_crescente(self, predictor):
        """Should detect increasing trend."""
        valores = [0.1, 0.2, 0.3, 0.4, 0.5]
        slope, r_sq = predictor._calcular_tendencia(valores)
        
        assert slope > 0  # Positive slope
        assert r_sq > 0.9  # High R²
    
    def test_calcular_tendencia_decrescente(self, predictor):
        """Should detect decreasing trend."""
        valores = [0.5, 0.4, 0.3, 0.2, 0.1]
        slope, r_sq = predictor._calcular_tendencia(valores)
        
        assert slope < 0  # Negative slope
    
    def test_calcular_tendencia_estavel(self, predictor):
        """Should detect stable trend."""
        valores = [0.3, 0.3, 0.3, 0.3, 0.3]
        slope, r_sq = predictor._calcular_tendencia(valores)
        
        assert abs(slope) < 0.01  # Near zero slope
    
    def test_calcular_tendencia_pouco_historico(self, predictor):
        """Should handle limited history."""
        valores = [0.5]
        slope, r_sq = predictor._calcular_tendencia(valores)
        
        assert slope == 0
        assert r_sq == 0
    
    def test_prever_utilizacao_sem_historico(self, predictor):
        """Should predict with no history."""
        util = predictor.prever_utilizacao(
            cliente_id='123',
            produto='consignado',
            historico_utilizacao=[],
            propensao=70
        )
        
        assert 0 <= util <= 1
    
    def test_prever_utilizacao_com_historico(self, predictor):
        """Should predict based on history."""
        util = predictor.prever_utilizacao(
            cliente_id='123',
            produto='consignado',
            historico_utilizacao=[0.8, 0.85, 0.9, 0.85, 0.9],
            propensao=70
        )
        
        assert util > 0.5  # High historical use should predict high future use
    
    def test_prever_utilizacao_baixo_uso(self, predictor):
        """Low history should predict low future."""
        util = predictor.prever_utilizacao(
            cliente_id='123',
            produto='consignado',
            historico_utilizacao=[0.0, 0.0, 0.05, 0.0, 0.0],
            propensao=20
        )
        
        assert util < 0.3  # Low use + low propensity
    
    def test_prever_utilizacao_alto_risco(self, predictor):
        """High risk should reduce prediction."""
        util_baixo_risco = predictor.prever_utilizacao(
            cliente_id='123',
            produto='consignado',
            historico_utilizacao=[0.5, 0.5, 0.5],
            propensao=70,
            prinad=15
        )
        
        util_alto_risco = predictor.prever_utilizacao(
            cliente_id='123',
            produto='consignado',
            historico_utilizacao=[0.5, 0.5, 0.5],
            propensao=70,
            prinad=85
        )
        
        assert util_alto_risco < util_baixo_risco
    
    def test_prever_acao_limite_zerar(self, predictor):
        """PRINAD D should predict zero."""
        previsao = predictor.prever_acao_limite(
            cliente_id='123',
            produto='consignado',
            limite_atual=100000,
            historico_utilizacao=[0.5, 0.5],
            propensao=70,
            prinad=95,  # PRINAD D
            trimestres_sem_uso=0
        )
        
        assert previsao.acao_prevista == 'zerar'
        assert previsao.limite_previsto == 0
        assert previsao.confianca > 0.9
    
    def test_prever_acao_limite_reduzir(self, predictor):
        """Low use should predict reduction."""
        previsao = predictor.prever_acao_limite(
            cliente_id='123',
            produto='consignado',
            limite_atual=100000,
            historico_utilizacao=[0.0, 0.0, 0.0, 0.0],
            propensao=15,  # Low propensity
            prinad=20,
            trimestres_sem_uso=2
        )
        
        assert previsao.acao_prevista == 'reduzir'
        assert previsao.limite_previsto == 30000  # 30%
    
    def test_prever_acao_limite_aumentar(self, predictor):
        """High use + low risk should predict increase."""
        previsao = predictor.prever_acao_limite(
            cliente_id='123',
            produto='consignado',
            limite_atual=100000,
            historico_utilizacao=[0.9, 0.95, 0.85, 0.9],
            propensao=85,
            prinad=10,
            trimestres_sem_uso=0
        )
        
        assert previsao.acao_prevista == 'aumentar'
        assert previsao.limite_previsto == 120000
    
    def test_prever_acao_limite_manter(self, predictor):
        """Normal profile should maintain."""
        previsao = predictor.prever_acao_limite(
            cliente_id='123',
            produto='consignado',
            limite_atual=100000,
            historico_utilizacao=[0.5, 0.5, 0.5],
            propensao=50,
            prinad=30,
            trimestres_sem_uso=0
        )
        
        assert previsao.acao_prevista == 'manter'
    
    def test_gerar_lista_notificacao(self, predictor):
        """Generate notification list."""
        previsao1 = predictor.prever_acao_limite(
            cliente_id='1', produto='consignado', limite_atual=100000,
            historico_utilizacao=[0, 0, 0], propensao=10, prinad=20,
            trimestres_sem_uso=3
        )
        previsao2 = predictor.prever_acao_limite(
            cliente_id='2', produto='consignado', limite_atual=50000,
            historico_utilizacao=[0.8, 0.9], propensao=80, prinad=15,
            trimestres_sem_uso=0
        )
        
        lista = predictor.gerar_lista_notificacao(
            previsoes=[previsao1, previsao2],
            horizonte_dias=60
        )
        
        assert isinstance(lista, ListaNotificacao)
        assert lista.horizonte_dias == 60
        assert lista.total_reducoes >= 0
    
    def test_verificar_cancelamento_com_uso(self, predictor):
        """Usage should cancel reduction."""
        should_cancel = predictor.verificar_cancelamento_reducao(
            cliente_id='123',
            produto='consignado',
            utilizacao_atual=0.30
        )
        
        assert should_cancel is True
    
    def test_verificar_cancelamento_sem_uso(self, predictor):
        """No usage should not cancel."""
        should_cancel = predictor.verificar_cancelamento_reducao(
            cliente_id='123',
            produto='consignado',
            utilizacao_atual=0.0
        )
        
        assert should_cancel is False


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_get_limit_predictor(self):
        """Should return predictor instance."""
        pred = get_limit_predictor()
        assert isinstance(pred, LimitPredictor)
