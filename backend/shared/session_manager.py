# -*- coding: utf-8 -*-
"""
Módulo de Gerenciamento de Sessões
==================================

Controle de sessões com timeout, logout por inatividade e revogação de tokens.

Autor: Sistema ECL
Data: Janeiro 2026
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import hashlib
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class Sessao:
    """Representa uma sessão de usuário ativa."""
    session_id: str
    usuario_id: str
    usuario_nome: str
    token_hash: str
    ip_address: str
    user_agent: str
    criado_em: datetime
    ultimo_acesso: datetime
    expira_em: datetime
    ativa: bool = True
    
    def esta_expirada(self) -> bool:
        """Verifica se a sessão expirou."""
        return datetime.now() > self.expira_em
    
    def esta_inativa(self, timeout_minutos: int) -> bool:
        """Verifica se a sessão está inativa pelo tempo especificado."""
        limite = datetime.now() - timedelta(minutes=timeout_minutos)
        return self.ultimo_acesso < limite


class SessionManager:
    """
    Gerenciador de sessões com controles de segurança.
    
    Features:
    - Timeout de sessão configurável
    - Logout automático por inatividade
    - Revogação de token em troca de senha
    - Limpeza automática de sessões expiradas
    """
    
    # Configurações padrão
    DEFAULT_TIMEOUT_MINUTES = 30  # Timeout padrão para ambiente bancário
    MAX_SESSIONS_PER_USER = 3     # Máximo de sessões simultâneas por usuário
    CLEANUP_INTERVAL_MINUTES = 5  # Intervalo de limpeza automática
    
    def __init__(self, timeout_minutos: int = None):
        """
        Inicializa o gerenciador de sessões.
        
        Args:
            timeout_minutos: Timeout de sessão em minutos (padrão: 30)
        """
        self._sessoes: Dict[str, Sessao] = {}
        self._timeout = timeout_minutos or self.DEFAULT_TIMEOUT_MINUTES
        self._lock = threading.Lock()
        self._tokens_revogados: set = set()
        
        logger.info(f"SessionManager inicializado com timeout de {self._timeout} minutos")
    
    def criar_sessao(
        self,
        usuario_id: str,
        usuario_nome: str,
        token: str,
        ip_address: str,
        user_agent: str = ""
    ) -> Sessao:
        """
        Cria nova sessão para o usuário.
        
        Args:
            usuario_id: ID do usuário
            usuario_nome: Nome do usuário
            token: Token JWT
            ip_address: Endereço IP
            user_agent: User agent do navegador
            
        Returns:
            Sessao criada
        """
        with self._lock:
            # Verificar limite de sessões
            sessoes_usuario = [
                s for s in self._sessoes.values()
                if s.usuario_id == usuario_id and s.ativa
            ]
            
            if len(sessoes_usuario) >= self.MAX_SESSIONS_PER_USER:
                # Encerrar sessão mais antiga
                sessao_antiga = min(sessoes_usuario, key=lambda s: s.criado_em)
                self.encerrar_sessao(sessao_antiga.session_id)
                logger.warning(
                    f"Limite de sessões atingido para {usuario_nome}. "
                    f"Sessão antiga encerrada."
                )
            
            # Criar nova sessão
            session_id = hashlib.sha256(
                f"{usuario_id}{datetime.now().isoformat()}{token[:20]}".encode()
            ).hexdigest()[:32]
            
            sessao = Sessao(
                session_id=session_id,
                usuario_id=usuario_id,
                usuario_nome=usuario_nome,
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                ip_address=ip_address,
                user_agent=user_agent,
                criado_em=datetime.now(),
                ultimo_acesso=datetime.now(),
                expira_em=datetime.now() + timedelta(minutes=self._timeout)
            )
            
            self._sessoes[session_id] = sessao
            
            logger.info(f"Sessão criada para {usuario_nome} (IP: {ip_address})")
            return sessao
    
    def atualizar_atividade(self, session_id: str) -> bool:
        """
        Atualiza o timestamp de última atividade da sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se atualizado com sucesso
        """
        with self._lock:
            sessao = self._sessoes.get(session_id)
            if not sessao:
                return False
            
            if not sessao.ativa or sessao.esta_expirada():
                return False
            
            sessao.ultimo_acesso = datetime.now()
            sessao.expira_em = datetime.now() + timedelta(minutes=self._timeout)
            return True
    
    def validar_sessao(self, session_id: str = None, token: str = None) -> Optional[Sessao]:
        """
        Valida se a sessão está ativa e não expirada.
        
        Args:
            session_id: ID da sessão (opcional)
            token: Token JWT para busca (opcional)
            
        Returns:
            Sessao se válida, None caso contrário
        """
        with self._lock:
            # Verificar se token foi revogado
            if token:
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                if token_hash in self._tokens_revogados:
                    return None
                
                # Buscar por token
                for sessao in self._sessoes.values():
                    if sessao.token_hash == token_hash:
                        if sessao.ativa and not sessao.esta_expirada():
                            return sessao
                        return None
            
            # Buscar por session_id
            if session_id:
                sessao = self._sessoes.get(session_id)
                if sessao and sessao.ativa and not sessao.esta_expirada():
                    return sessao
            
            return None
    
    def encerrar_sessao(self, session_id: str) -> bool:
        """
        Encerra uma sessão específica.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se encerrada com sucesso
        """
        with self._lock:
            sessao = self._sessoes.get(session_id)
            if not sessao:
                return False
            
            sessao.ativa = False
            self._tokens_revogados.add(sessao.token_hash)
            
            logger.info(f"Sessão {session_id[:8]}... encerrada para {sessao.usuario_nome}")
            return True
    
    def encerrar_todas_sessoes_usuario(self, usuario_id: str) -> int:
        """
        Encerra todas as sessões de um usuário.
        
        Útil para logout de todos os dispositivos ou troca de senha.
        
        Args:
            usuario_id: ID do usuário
            
        Returns:
            Quantidade de sessões encerradas
        """
        with self._lock:
            count = 0
            for sessao in self._sessoes.values():
                if sessao.usuario_id == usuario_id and sessao.ativa:
                    sessao.ativa = False
                    self._tokens_revogados.add(sessao.token_hash)
                    count += 1
            
            logger.info(f"{count} sessões encerradas para usuário {usuario_id}")
            return count
    
    def revogar_token(self, token: str) -> bool:
        """
        Revoga um token específico.
        
        Usado em troca de senha para invalidar tokens antigos.
        
        Args:
            token: Token JWT a ser revogado
            
        Returns:
            True se revogado com sucesso
        """
        with self._lock:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            self._tokens_revogados.add(token_hash)
            
            # Encerrar sessão associada
            for sessao in self._sessoes.values():
                if sessao.token_hash == token_hash:
                    sessao.ativa = False
                    logger.info(f"Token revogado para {sessao.usuario_nome}")
                    return True
            
            logger.info("Token revogado (sessão não encontrada)")
            return True
    
    def limpar_sessoes_expiradas(self) -> int:
        """
        Remove sessões expiradas e inativas.
        
        Returns:
            Quantidade de sessões removidas
        """
        with self._lock:
            sessoes_para_remover = []
            
            for session_id, sessao in self._sessoes.items():
                if not sessao.ativa or sessao.esta_expirada():
                    sessoes_para_remover.append(session_id)
                elif sessao.esta_inativa(self._timeout):
                    sessao.ativa = False
                    sessoes_para_remover.append(session_id)
            
            for session_id in sessoes_para_remover:
                del self._sessoes[session_id]
            
            if sessoes_para_remover:
                logger.info(f"{len(sessoes_para_remover)} sessões expiradas removidas")
            
            return len(sessoes_para_remover)
    
    def obter_sessoes_ativas(self, usuario_id: str = None) -> List[Dict]:
        """
        Lista sessões ativas, opcionalmente filtradas por usuário.
        
        Args:
            usuario_id: Filtrar por usuário (opcional)
            
        Returns:
            Lista de sessões ativas
        """
        with self._lock:
            sessoes = [
                {
                    "session_id": s.session_id,
                    "usuario_id": s.usuario_id,
                    "usuario_nome": s.usuario_nome,
                    "ip_address": s.ip_address,
                    "criado_em": s.criado_em.isoformat(),
                    "ultimo_acesso": s.ultimo_acesso.isoformat(),
                    "expira_em": s.expira_em.isoformat()
                }
                for s in self._sessoes.values()
                if s.ativa and not s.esta_expirada()
                and (usuario_id is None or s.usuario_id == usuario_id)
            ]
            return sessoes
    
    def verificar_inatividade(self, session_id: str) -> Dict:
        """
        Verifica status de inatividade de uma sessão.
        
        Returns:
            Dict com informações de inatividade
        """
        with self._lock:
            sessao = self._sessoes.get(session_id)
            if not sessao:
                return {"valida": False, "motivo": "Sessão não encontrada"}
            
            if not sessao.ativa:
                return {"valida": False, "motivo": "Sessão encerrada"}
            
            if sessao.esta_expirada():
                return {"valida": False, "motivo": "Sessão expirada"}
            
            tempo_inativo = (datetime.now() - sessao.ultimo_acesso).total_seconds() / 60
            tempo_restante = (sessao.expira_em - datetime.now()).total_seconds() / 60
            
            return {
                "valida": True,
                "tempo_inativo_minutos": round(tempo_inativo, 1),
                "tempo_restante_minutos": round(tempo_restante, 1),
                "aviso_inatividade": tempo_restante < 5  # Aviso quando restar menos de 5 min
            }
    
    def set_timeout(self, minutos: int) -> None:
        """
        Atualiza o timeout de sessão.
        
        Args:
            minutos: Novo timeout em minutos
        """
        self._timeout = minutos
        logger.info(f"Timeout de sessão atualizado para {minutos} minutos")


# Instância global
_session_manager: Optional[SessionManager] = None


def get_session_manager(timeout: int = None) -> SessionManager:
    """Obtém ou cria instância do gerenciador de sessões."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(timeout)
    return _session_manager


__all__ = [
    "Sessao",
    "SessionManager",
    "get_session_manager"
]
