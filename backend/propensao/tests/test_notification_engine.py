"""
Unit tests for Notification Engine.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from propensao.src.notification_engine import (
    NotificationEngine,
    CanalNotificacao,
    TipoNotificacao,
    Notificacao,
    HistoricoNotificacao,
    get_notification_engine
)
from propensao.src.limit_predictor import PrevisaoLimite, ListaNotificacao


class TestNotificationEngine:
    """Test Notification Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create engine fixture."""
        return NotificationEngine()
    
    def test_initialization(self, engine):
        """Engine should initialize correctly."""
        assert engine is not None
        assert engine.output_dir.exists()
    
    def test_gerar_id(self, engine):
        """Should generate unique IDs."""
        id1 = engine._gerar_id()
        id2 = engine._gerar_id()
        
        assert id1 != id2
        assert id1.startswith('NOT')
    
    def test_criar_notificacao_aviso_60(self, engine):
        """Create 60-day warning notification."""
        notif = engine.criar_notificacao(
            cliente_id='12345678901',
            tipo=TipoNotificacao.AVISO_60_DIAS,
            produto='consignado',
            limite_atual=100000,
            limite_futuro=30000
        )
        
        assert isinstance(notif, Notificacao)
        assert notif.cliente_id == '12345678901'
        assert notif.tipo == TipoNotificacao.AVISO_60_DIAS
        assert 'consignado' in notif.mensagem
        assert '100.000' in notif.mensagem or '100,000' in notif.mensagem
        assert CanalNotificacao.PUSH in notif.canais
        assert CanalNotificacao.SMS in notif.canais
        assert CanalNotificacao.BANNER in notif.canais
    
    def test_criar_notificacao_aviso_30(self, engine):
        """Create 30-day warning notification."""
        notif = engine.criar_notificacao(
            cliente_id='123',
            tipo=TipoNotificacao.AVISO_30_DIAS,
            produto='banparacard',
            limite_atual=50000,
            limite_futuro=15000
        )
        
        assert notif.tipo == TipoNotificacao.AVISO_30_DIAS
        assert CanalNotificacao.PUSH in notif.canais
        assert CanalNotificacao.BANNER in notif.canais
        # SMS not in 30-day warning
        assert CanalNotificacao.SMS not in notif.canais
    
    def test_criar_notificacao_reducao_cancelada(self, engine):
        """Create reduction cancelled notification."""
        notif = engine.criar_notificacao(
            cliente_id='123',
            tipo=TipoNotificacao.REDUCAO_CANCELADA,
            produto='consignado',
            limite_atual=100000,
            limite_futuro=100000
        )
        
        assert notif.tipo == TipoNotificacao.REDUCAO_CANCELADA
        assert 'cancelada' in notif.titulo.lower()
        assert CanalNotificacao.PUSH in notif.canais
    
    def test_criar_notificacao_aumento(self, engine):
        """Create limit increase notification."""
        notif = engine.criar_notificacao(
            cliente_id='123',
            tipo=TipoNotificacao.AUMENTO_DISPONIVEL,
            produto='consignado',
            limite_atual=100000,
            limite_futuro=150000
        )
        
        assert notif.tipo == TipoNotificacao.AUMENTO_DISPONIVEL
        assert 'aumento' in notif.titulo.lower()
    
    def test_historico_cliente(self, engine):
        """Notifications should be added to history."""
        engine.criar_notificacao(
            cliente_id='123',
            tipo=TipoNotificacao.AVISO_60_DIAS,
            produto='consignado',
            limite_atual=100000,
            limite_futuro=30000
        )
        engine.criar_notificacao(
            cliente_id='123',
            tipo=TipoNotificacao.AVISO_30_DIAS,
            produto='consignado',
            limite_atual=100000,
            limite_futuro=30000
        )
        
        assert '123' in engine.historico
        assert len(engine.historico['123'].notificacoes) == 2
    
    def test_processar_lista_notificacao(self, engine):
        """Process notification list."""
        lista = ListaNotificacao(
            data_geracao=datetime.now(),
            horizonte_dias=60,
            clientes=[
                PrevisaoLimite(
                    cliente_id='1', produto='consignado',
                    limite_atual=100000, utilizacao_prevista=0.1,
                    limite_previsto=30000, acao_prevista='reduzir',
                    confianca=0.8, dias_para_aplicacao=55
                ),
                PrevisaoLimite(
                    cliente_id='2', produto='banparacard',
                    limite_atual=50000, utilizacao_prevista=0.9,
                    limite_previsto=60000, acao_prevista='aumentar',
                    confianca=0.7, dias_para_aplicacao=55
                )
            ],
            total_reducoes=1,
            total_aumentos=1,
            economia_ecl_estimada=5000
        )
        
        notificacoes = engine.processar_lista_notificacao(lista)
        
        # Only reductions should generate notifications
        assert len(notificacoes) == 1
        assert notificacoes[0].cliente_id == '1'
    
    def test_notificar_cancelamento(self, engine):
        """Create cancellation notification."""
        notif = engine.notificar_cancelamento(
            cliente_id='123',
            produto='consignado',
            limite_atual=100000
        )
        
        assert notif.tipo == TipoNotificacao.REDUCAO_CANCELADA
        assert 'cancelada' in notif.mensagem.lower() or 'cancelada' in notif.titulo.lower()
    
    def test_enviar_notificacao(self, engine):
        """Send notification (mock)."""
        notif = engine.criar_notificacao(
            cliente_id='123',
            tipo=TipoNotificacao.AVISO_60_DIAS,
            produto='consignado',
            limite_atual=100000,
            limite_futuro=30000
        )
        
        assert notif.enviada is False
        
        result = engine.enviar_notificacao(notif)
        
        assert result is True
        assert notif.enviada is True
        assert notif.data_envio is not None
    
    def test_exportar_historico_csv(self, engine):
        """Export history to CSV."""
        engine.criar_notificacao(
            cliente_id='123',
            tipo=TipoNotificacao.AVISO_60_DIAS,
            produto='consignado',
            limite_atual=100000,
            limite_futuro=30000
        )
        
        output_file = engine.exportar_historico(formato='csv')
        
        assert output_file.exists()
        assert output_file.suffix == '.csv'
        
        # Cleanup
        output_file.unlink()
    
    def test_exportar_historico_json(self, engine):
        """Export history to JSON."""
        engine.criar_notificacao(
            cliente_id='123',
            tipo=TipoNotificacao.AVISO_60_DIAS,
            produto='consignado',
            limite_atual=100000,
            limite_futuro=30000
        )
        
        output_file = engine.exportar_historico(formato='json')
        
        assert output_file.exists()
        assert output_file.suffix == '.json'
        
        # Cleanup
        output_file.unlink()


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_get_notification_engine(self):
        """Should return engine instance."""
        eng = get_notification_engine()
        assert isinstance(eng, NotificationEngine)
