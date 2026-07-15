"""Controlled database migration policy for application startup."""

from __future__ import annotations

import os
from typing import Literal, cast

from .manager import DatabaseConfigurationError, DatabaseManager

MigrationMode = Literal["apply", "validate", "disabled"]


def migration_mode_from_env() -> MigrationMode:
    raw = os.getenv("DATABASE_MIGRATION_MODE", "apply").lower()
    if raw not in {"apply", "validate", "disabled"}:
        raise DatabaseConfigurationError(
            "DATABASE_MIGRATION_MODE must be 'apply', 'validate' or 'disabled'"
        )
    environment = os.getenv("APP_ENV", "local").lower()
    if environment == "demo" and raw != "validate":
        raise DatabaseConfigurationError(
            "APP_ENV=demo requires DATABASE_MIGRATION_MODE=validate; "
            "apply migrations in the controlled pre-deployment step"
        )
    return cast(MigrationMode, raw)


def prepare_database(
    manager: DatabaseManager, mode: MigrationMode | None = None
) -> tuple[str, ...]:
    """Apply, validate, or explicitly skip migrations according to policy."""
    selected = mode or migration_mode_from_env()
    if selected == "apply":
        return manager.apply_migrations()
    if selected == "validate":
        return manager.validate_migrations()
    return ()
