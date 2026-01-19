# -*- coding: utf-8 -*-
"""
Módulo de Conexão com PostgreSQL
Sistema de Gestão de Risco Bancário
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool

from .config import get_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador de conexões PostgreSQL com pool."""
    
    _instance: Optional['DatabaseManager'] = None
    _pool: Optional[pool.ThreadedConnectionPool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            self._initialize_pool()
    
    def _initialize_pool(self):
        """Inicializa o pool de conexões."""
        config = get_config()
        try:
            self._pool = pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                host=config.database.host,
                port=config.database.port,
                user=config.database.user,
                password=config.database.password,
                database=config.database.database
            )
            logger.info(f"✅ Pool de conexões PostgreSQL inicializado: {config.database.host}:{config.database.port}/{config.database.database}")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager para obter conexão do pool."""
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
    
    def execute(self, query: str, params: tuple = None) -> int:
        """Executa query e retorna número de linhas afetadas."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Busca uma linha."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return dict(row) if row else None
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Busca todas as linhas."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    
    def close(self):
        """Fecha o pool de conexões."""
        if self._pool:
            self._pool.closeall()
            logger.info("Pool de conexões fechado")


# Instância global
_db: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Obtém instância do gerenciador de banco."""
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db


# ============================================================================
# CRUD Sessões
# ============================================================================

def criar_sessao(usuario_id: str, usuario_role: str, titulo: str = "Nova Conversa") -> Dict[str, Any]:
    """Cria uma nova sessão de chat."""
    db = get_db()
    query = """
        INSERT INTO agente.sessoes (usuario_id, usuario_role, titulo)
        VALUES (%s, %s, %s)
        RETURNING id, usuario_id, usuario_role, titulo, created_at
    """
    return db.fetch_one(query, (usuario_id, usuario_role, titulo))


def listar_sessoes(usuario_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Lista sessões do usuário."""
    db = get_db()
    query = """
        SELECT id, titulo, resumo, created_at, updated_at
        FROM agente.sessoes
        WHERE usuario_id = %s
        ORDER BY updated_at DESC
        LIMIT %s
    """
    return db.fetch_all(query, (usuario_id, limit))


def obter_sessao(sessao_id: str) -> Optional[Dict[str, Any]]:
    """Obtém uma sessão específica."""
    db = get_db()
    query = """
        SELECT id, usuario_id, usuario_role, titulo, resumo, metadata, created_at, updated_at
        FROM agente.sessoes
        WHERE id = %s
    """
    return db.fetch_one(query, (sessao_id,))


def atualizar_sessao(sessao_id: str, titulo: str = None, resumo: str = None) -> bool:
    """Atualiza uma sessão."""
    db = get_db()
    updates = []
    params = []
    
    if titulo:
        updates.append("titulo = %s")
        params.append(titulo)
    if resumo:
        updates.append("resumo = %s")
        params.append(resumo)
    
    if not updates:
        return False
    
    updates.append("updated_at = NOW()")
    params.append(sessao_id)
    
    query = f"""
        UPDATE agente.sessoes
        SET {', '.join(updates)}
        WHERE id = %s
    """
    return db.execute(query, tuple(params)) > 0


def excluir_sessao(sessao_id: str) -> bool:
    """Exclui uma sessão e suas mensagens."""
    db = get_db()
    query = "DELETE FROM agente.sessoes WHERE id = %s"
    return db.execute(query, (sessao_id,)) > 0


# ============================================================================
# CRUD Mensagens
# ============================================================================

def adicionar_mensagem(
    sessao_id: str,
    role: str,
    content: str,
    tool_name: str = None,
    tool_calls: dict = None,
    tool_result: dict = None,
    metadata: dict = None
) -> Dict[str, Any]:
    """Adiciona uma mensagem à sessão."""
    db = get_db()
    query = """
        INSERT INTO agente.mensagens 
        (sessao_id, role, content, tool_name, tool_calls, tool_result, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, role, content, created_at
    """
    import json
    return db.fetch_one(query, (
        sessao_id,
        role,
        content,
        tool_name,
        json.dumps(tool_calls) if tool_calls else None,
        json.dumps(tool_result) if tool_result else None,
        json.dumps(metadata or {})
    ))


def listar_mensagens(sessao_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Lista mensagens de uma sessão."""
    db = get_db()
    query = """
        SELECT id, role, content, tool_name, tool_calls, tool_result, metadata, created_at
        FROM agente.mensagens
        WHERE sessao_id = %s
        ORDER BY created_at ASC
        LIMIT %s
    """
    return db.fetch_all(query, (sessao_id, limit))


# ============================================================================
# CRUD Artefatos
# ============================================================================

def criar_artefato(
    usuario_id: str,
    tipo: str,
    nome: str,
    sessao_id: str = None,
    mensagem_id: str = None,
    descricao: str = None,
    mime_type: str = None,
    conteudo_path: str = None,
    conteudo_base64: str = None,
    metadata: dict = None
) -> Dict[str, Any]:
    """Cria um novo artefato."""
    db = get_db()
    query = """
        INSERT INTO agente.artefatos 
        (usuario_id, sessao_id, mensagem_id, tipo, nome, descricao, mime_type, 
         conteudo_path, conteudo_base64, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, tipo, nome, created_at
    """
    import json
    return db.fetch_one(query, (
        usuario_id, sessao_id, mensagem_id, tipo, nome, descricao, mime_type,
        conteudo_path, conteudo_base64, json.dumps(metadata or {})
    ))


def listar_artefatos(usuario_id: str = None, sessao_id: str = None) -> List[Dict[str, Any]]:
    """Lista artefatos por usuário ou sessão."""
    db = get_db()
    
    if sessao_id:
        query = """
            SELECT id, tipo, nome, descricao, mime_type, created_at
            FROM agente.artefatos
            WHERE sessao_id = %s
            ORDER BY created_at DESC
        """
        return db.fetch_all(query, (sessao_id,))
    elif usuario_id:
        query = """
            SELECT id, tipo, nome, descricao, mime_type, sessao_id, created_at
            FROM agente.artefatos
            WHERE usuario_id = %s
            ORDER BY created_at DESC
            LIMIT 100
        """
        return db.fetch_all(query, (usuario_id,))
    
    return []


def obter_artefato(artefato_id: str) -> Optional[Dict[str, Any]]:
    """Obtém um artefato específico."""
    db = get_db()
    query = """
        SELECT id, usuario_id, sessao_id, tipo, nome, descricao, mime_type,
               conteudo_path, conteudo_base64, metadata, created_at
        FROM agente.artefatos
        WHERE id = %s
    """
    return db.fetch_one(query, (artefato_id,))


# ============================================================================
# Log de Ferramentas
# ============================================================================

def registrar_uso_ferramenta(
    usuario_id: str,
    usuario_role: str,
    tool_name: str,
    tool_input: dict = None,
    tool_output: dict = None,
    success: bool = True,
    error_message: str = None,
    execution_ms: int = None,
    sessao_id: str = None
) -> None:
    """Registra uso de ferramenta para auditoria."""
    db = get_db()
    query = """
        INSERT INTO agente.tool_usage_log 
        (usuario_id, usuario_role, tool_name, tool_input, tool_output, 
         success, error_message, execution_ms, sessao_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    import json
    db.execute(query, (
        usuario_id, usuario_role, tool_name,
        json.dumps(tool_input) if tool_input else None,
        json.dumps(tool_output) if tool_output else None,
        success, error_message, execution_ms, sessao_id
    ))


__all__ = [
    "DatabaseManager",
    "get_db",
    "criar_sessao",
    "listar_sessoes",
    "obter_sessao",
    "atualizar_sessao",
    "excluir_sessao",
    "adicionar_mensagem",
    "listar_mensagens",
    "criar_artefato",
    "listar_artefatos",
    "obter_artefato",
    "registrar_uso_ferramenta"
]
