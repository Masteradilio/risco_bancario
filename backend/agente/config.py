# -*- coding: utf-8 -*-
"""
Configuração do Agente de IA
Sistema de Gestão de Risco Bancário
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Configuração do PostgreSQL."""
    host: str = field(default_factory=lambda: os.getenv("DATABASE_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DATABASE_PORT", "5432")))
    user: str = field(default_factory=lambda: os.getenv("DATABASE_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("DATABASE_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("DATABASE_NAME", "dbrisco"))
    
    @property
    def url(self) -> str:
        """URL de conexão PostgreSQL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """URL de conexão assíncrona."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class LLMConfig:
    """Configuração do LLM (OpenRouter)."""
    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENROUTER_MODEL", "moonshotai/kimi-k2:free"))
    base_url: str = field(default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
    temperature: float = 0.3
    max_tokens: int = 4096


@dataclass
class EmbeddingConfig:
    """Configuração de embeddings."""
    model: str = field(default_factory=lambda: os.getenv("FILE_SEARCH_EMBEDDING_MODEL", "intfloat/multilingual-e5-large-instruct"))
    dimension: int = field(default_factory=lambda: int(os.getenv("FILE_SEARCH_EMBEDDING_DIMENSION", "1024")))
    huggingface_token: Optional[str] = field(default_factory=lambda: os.getenv("HUGGINGFACE_TOKEN"))


@dataclass
class AgentConfig:
    """Configuração principal do Agente."""
    enabled: bool = field(default_factory=lambda: os.getenv("AGENT_ENABLED", "true").lower() == "true")
    docs_path: str = field(default_factory=lambda: os.getenv("AGENT_DOCS_PATH", "backend/perda_esperada/docs"))
    artifacts_path: str = field(default_factory=lambda: os.getenv("AGENT_ARTIFACTS_PATH", "backend/agente/artifacts"))
    max_history: int = field(default_factory=lambda: int(os.getenv("AGENT_MAX_HISTORY", "50")))
    
    # Sub-configurações
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # RAG Settings
    chunk_size: int = field(default_factory=lambda: int(os.getenv("FILE_SEARCH_CHUNK_SIZE", "1500")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("FILE_SEARCH_CHUNK_OVERLAP", "200")))
    use_rerank: bool = field(default_factory=lambda: os.getenv("FILE_SEARCH_USE_RERANK", "true").lower() == "true")


# Instância global
_config: Optional[AgentConfig] = None


def get_config() -> AgentConfig:
    """Obtém ou cria configuração."""
    global _config
    if _config is None:
        _config = AgentConfig()
    return _config


__all__ = [
    "DatabaseConfig",
    "LLMConfig",
    "EmbeddingConfig",
    "AgentConfig",
    "get_config"
]
