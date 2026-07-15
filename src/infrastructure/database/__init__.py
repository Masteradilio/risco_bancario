"""Persistence adapters for versioned platform data."""

from .manager import DatabaseManager, DatabaseSettings
from .repository import PersistenceConflictError, VersionedRepository

__all__ = [
    "DatabaseManager",
    "DatabaseSettings",
    "PersistenceConflictError",
    "VersionedRepository",
]
