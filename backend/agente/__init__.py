# -*- coding: utf-8 -*-
"""
Agente de IA - Sistema de Gestão de Risco Bancário
"""

from .config import AgentConfig, get_config
from .database import get_db
from .permissions import check_tool_permission, get_allowed_tools, UserRole

__version__ = "1.0.0"

__all__ = [
    "AgentConfig",
    "get_config",
    "get_db",
    "check_tool_permission",
    "get_allowed_tools",
    "UserRole"
]
