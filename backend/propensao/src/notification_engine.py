"""
Notification Engine - Handles client notifications for limit changes.

Supports multiple channels:
- Push notifications
- SMS
- In-app banners

Manages the 60/30/0 day notification cycle.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import PROPENSAO_DIR, setup_logging
from propensao.src.limit_predictor import PrevisaoLimite, ListaNotificacao

logger = setup_logging(__name__)


class CanalNotificacao(Enum):
    """Notification channels."""
    PUSH = "push"
    SMS = "sms"
    BANNER = "banner"
    EMAIL = "email"


class TipoNotificacao(Enum):
    """Types of notifications."""
    AVISO_60_DIAS = "aviso_60_dias"
    AVISO_30_DIAS = "aviso_30_dias"
    CONFIRMACAO_REDUCAO = "confirmacao_reducao"
    REDUCAO_CANCELADA = "reducao_cancelada"
    LIMITE_ALTERADO = "limite_alterado"
    AUMENTO_DISPONIVEL = "aumento_disponivel"


@dataclass
class Notificacao:
    """A single notification."""
    id: str
    cliente_id: str
    tipo: TipoNotificacao
    canais: List[CanalNotificacao]
    titulo: str
    mensagem: str
    data_envio: Optional[datetime] = None
    data_agendada: Optional[datetime] = None
    enviada: bool = False
    dados_adicionais: Dict = field(default_factory=dict)


@dataclass
class HistoricoNotificacao:
    """History of notifications for a client."""
    cliente_id: str
    notificacoes: List[Notificacao]
    ultima_notificacao: Optional[datetime] = None


class NotificationEngine:
    """
    Manages notifications for credit limit changes.
    
    Notification cycle:
    - 60 days: First warning (Push + SMS + Banner)
    - 30 days: Confirmation (Push + Banner)
    - 0 days: Limit changed (Push + SMS)
    
    If client uses limit during cycle, cancellation is notified.
    """
    
    # Message templates
    TEMPLATES = {
        TipoNotificacao.AVISO_60_DIAS: {
            'titulo': '⚠️ Aviso sobre seu limite de crédito',
            'mensagem': (
                'Olá! Identificamos que seu limite de {produto} de R$ {limite_atual:,.2f} '
                'não está sendo utilizado. Se continuar sem uso nos próximos 60 dias, '
                'poderá ser reduzido para R$ {limite_futuro:,.2f}. '
                'Aproveite seu crédito disponível!'
            )
        },
        TipoNotificacao.AVISO_30_DIAS: {
            'titulo': '⏰ Último aviso: Limite de crédito será reduzido',
            'mensagem': (
                'Seu limite de {produto} será reduzido em 30 dias. '
                'Limite atual: R$ {limite_atual:,.2f} → '
                'Novo limite: R$ {limite_futuro:,.2f}. '
                'Utilize seu crédito para manter o limite atual.'
            )
        },
        TipoNotificacao.CONFIRMACAO_REDUCAO: {
            'titulo': '📉 Limite de crédito reduzido',
            'mensagem': (
                'Seu limite de {produto} foi ajustado. '
                'Novo limite: R$ {limite_futuro:,.2f}. '
                'Isso foi necessário para otimizar nossos recursos. '
                'Entre em contato para mais informações.'
            )
        },
        TipoNotificacao.REDUCAO_CANCELADA: {
            'titulo': '✅ Redução de limite cancelada',
            'mensagem': (
                'Boa notícia! Identificamos movimentação no seu {produto}. '
                'A redução do limite prevista foi cancelada. '
                'Seu limite permanece em R$ {limite_atual:,.2f}.'
            )
        },
        TipoNotificacao.AUMENTO_DISPONIVEL: {
            'titulo': '🎉 Aumento de limite disponível!',
            'mensagem': (
                'Você pode aumentar seu limite de {produto}! '
                'Limite atual: R$ {limite_atual:,.2f} → '
                'Novo limite disponível: R$ {limite_futuro:,.2f}. '
                'Acesse o app para ativar.'
            )
        }
    }
    
    # Channel configuration per notification type
    CANAIS_POR_TIPO = {
        TipoNotificacao.AVISO_60_DIAS: [CanalNotificacao.PUSH, CanalNotificacao.SMS, CanalNotificacao.BANNER],
        TipoNotificacao.AVISO_30_DIAS: [CanalNotificacao.PUSH, CanalNotificacao.BANNER],
        TipoNotificacao.CONFIRMACAO_REDUCAO: [CanalNotificacao.PUSH, CanalNotificacao.SMS],
        TipoNotificacao.REDUCAO_CANCELADA: [CanalNotificacao.PUSH],
        TipoNotificacao.AUMENTO_DISPONIVEL: [CanalNotificacao.PUSH, CanalNotificacao.BANNER]
    }
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize notification engine.
        
        Args:
            output_dir: Directory for notification logs
        """
        self.output_dir = output_dir or (PROPENSAO_DIR / "notificacoes")
        self.output_dir.mkdir(exist_ok=True)
        
        self.historico: Dict[str, HistoricoNotificacao] = {}
        self._notification_counter = 0
        
        logger.info(f"NotificationEngine initialized (output: {self.output_dir})")
    
    def _gerar_id(self) -> str:
        """Generate unique notification ID."""
        self._notification_counter += 1
        return f"NOT{datetime.now().strftime('%Y%m%d%H%M%S')}{self._notification_counter:04d}"
    
    def _formatar_mensagem(
        self,
        template: Dict[str, str],
        dados: Dict
    ) -> tuple:
        """Format title and message with data."""
        titulo = template['titulo']
        mensagem = template['mensagem'].format(**dados)
        return titulo, mensagem
    
    def criar_notificacao(
        self,
        cliente_id: str,
        tipo: TipoNotificacao,
        produto: str,
        limite_atual: float,
        limite_futuro: float,
        agendar_para: Optional[datetime] = None
    ) -> Notificacao:
        """
        Create a notification.
        
        Args:
            cliente_id: Client identifier
            tipo: Notification type
            produto: Credit product
            limite_atual: Current limit
            limite_futuro: Future limit
            agendar_para: Optional scheduled date
            
        Returns:
            Notificacao object
        """
        template = self.TEMPLATES.get(tipo, {
            'titulo': 'Notificação',
            'mensagem': 'Você tem uma nova notificação.'
        })
        
        dados = {
            'produto': produto,
            'limite_atual': limite_atual,
            'limite_futuro': limite_futuro
        }
        
        titulo, mensagem = self._formatar_mensagem(template, dados)
        canais = self.CANAIS_POR_TIPO.get(tipo, [CanalNotificacao.PUSH])
        
        notificacao = Notificacao(
            id=self._gerar_id(),
            cliente_id=cliente_id,
            tipo=tipo,
            canais=canais,
            titulo=titulo,
            mensagem=mensagem,
            data_agendada=agendar_para,
            dados_adicionais={
                'produto': produto,
                'limite_atual': limite_atual,
                'limite_futuro': limite_futuro
            }
        )
        
        # Add to history
        if cliente_id not in self.historico:
            self.historico[cliente_id] = HistoricoNotificacao(
                cliente_id=cliente_id,
                notificacoes=[]
            )
        
        self.historico[cliente_id].notificacoes.append(notificacao)
        
        logger.info(f"Notification created: {notificacao.id} for {cliente_id}")
        
        return notificacao
    
    def processar_lista_notificacao(
        self,
        lista: ListaNotificacao
    ) -> List[Notificacao]:
        """
        Process a notification list and create notifications.
        
        Args:
            lista: ListaNotificacao from LimitPredictor
            
        Returns:
            List of created notifications
        """
        notificacoes = []
        
        # Determine notification type based on horizon
        if lista.horizonte_dias >= 60:
            tipo = TipoNotificacao.AVISO_60_DIAS
        elif lista.horizonte_dias >= 30:
            tipo = TipoNotificacao.AVISO_30_DIAS
        else:
            tipo = TipoNotificacao.CONFIRMACAO_REDUCAO
        
        for previsao in lista.clientes:
            if previsao.acao_prevista == 'reduzir':
                notif = self.criar_notificacao(
                    cliente_id=previsao.cliente_id,
                    tipo=tipo,
                    produto=previsao.produto,
                    limite_atual=previsao.limite_atual,
                    limite_futuro=previsao.limite_previsto
                )
                notificacoes.append(notif)
        
        logger.info(f"Processed {len(notificacoes)} notifications from list")
        
        return notificacoes
    
    def notificar_cancelamento(
        self,
        cliente_id: str,
        produto: str,
        limite_atual: float
    ) -> Notificacao:
        """
        Notify client that reduction was cancelled due to usage.
        
        Args:
            cliente_id: Client identifier
            produto: Product name
            limite_atual: Current limit
            
        Returns:
            Created notification
        """
        return self.criar_notificacao(
            cliente_id=cliente_id,
            tipo=TipoNotificacao.REDUCAO_CANCELADA,
            produto=produto,
            limite_atual=limite_atual,
            limite_futuro=limite_atual
        )
    
    def enviar_notificacao(
        self,
        notificacao: Notificacao
    ) -> bool:
        """
        Send a notification through configured channels.
        
        In production, this would integrate with:
        - Firebase/OneSignal for Push
        - Twilio/AWS SNS for SMS
        - In-app API for Banners
        
        Args:
            notificacao: Notification to send
            
        Returns:
            True if sent successfully
        """
        # Log the send (mock implementation)
        logger.info(f"Sending notification {notificacao.id} via {notificacao.canais}")
        
        for canal in notificacao.canais:
            if canal == CanalNotificacao.PUSH:
                self._enviar_push(notificacao)
            elif canal == CanalNotificacao.SMS:
                self._enviar_sms(notificacao)
            elif canal == CanalNotificacao.BANNER:
                self._configurar_banner(notificacao)
        
        notificacao.enviada = True
        notificacao.data_envio = datetime.now()
        
        return True
    
    def _enviar_push(self, notificacao: Notificacao):
        """Send push notification (mock)."""
        logger.info(f"[PUSH] {notificacao.cliente_id}: {notificacao.titulo}")
    
    def _enviar_sms(self, notificacao: Notificacao):
        """Send SMS notification (mock)."""
        logger.info(f"[SMS] {notificacao.cliente_id}: {notificacao.mensagem[:50]}...")
    
    def _configurar_banner(self, notificacao: Notificacao):
        """Configure in-app banner (mock)."""
        logger.info(f"[BANNER] {notificacao.cliente_id}: Banner configurado")
    
    def exportar_historico(self, formato: str = 'csv') -> Path:
        """
        Export notification history.
        
        Args:
            formato: 'csv' or 'json'
            
        Returns:
            Path to exported file
        """
        registros = []
        
        for cliente_id, hist in self.historico.items():
            for notif in hist.notificacoes:
                registros.append({
                    'id': notif.id,
                    'cliente_id': notif.cliente_id,
                    'tipo': notif.tipo.value,
                    'canais': ','.join([c.value for c in notif.canais]),
                    'titulo': notif.titulo,
                    'mensagem': notif.mensagem,
                    'data_envio': notif.data_envio.isoformat() if notif.data_envio else None,
                    'enviada': notif.enviada
                })
        
        df = pd.DataFrame(registros)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == 'json':
            output_file = self.output_dir / f"notificacoes_{timestamp}.json"
            df.to_json(output_file, orient='records', indent=2)
        else:
            output_file = self.output_dir / f"notificacoes_{timestamp}.csv"
            df.to_csv(output_file, index=False, sep=';')
        
        logger.info(f"Exported {len(registros)} notifications to {output_file}")
        
        return output_file


# Module-level instance
_notification_engine: Optional[NotificationEngine] = None


def get_notification_engine() -> NotificationEngine:
    """Get or create notification engine instance."""
    global _notification_engine
    if _notification_engine is None:
        _notification_engine = NotificationEngine()
    return _notification_engine


if __name__ == "__main__":
    engine = NotificationEngine()
    
    # Example notification
    notif = engine.criar_notificacao(
        cliente_id="12345678901",
        tipo=TipoNotificacao.AVISO_60_DIAS,
        produto="consignado",
        limite_atual=50000,
        limite_futuro=15000
    )
    
    print("=" * 60)
    print("Notification Example")
    print("=" * 60)
    print(f"ID: {notif.id}")
    print(f"Cliente: {notif.cliente_id}")
    print(f"Tipo: {notif.tipo.value}")
    print(f"Canais: {[c.value for c in notif.canais]}")
    print(f"Título: {notif.titulo}")
    print(f"Mensagem: {notif.mensagem}")
    print("=" * 60)
    
    # Send it
    engine.enviar_notificacao(notif)
