"""Versioned database connection and migration management."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import psycopg2  # type: ignore[import-untyped]
from psycopg2.extras import RealDictCursor  # type: ignore[import-untyped]

DatabaseBackend = Literal["sqlite", "postgresql"]


class DatabaseConfigurationError(ValueError):
    """Raised when the selected database has incomplete configuration."""


class MigrationIntegrityError(RuntimeError):
    """Raised when an applied migration no longer matches its checksum."""


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    """Explicit database settings; the selected backend is never substituted."""

    backend: DatabaseBackend = "sqlite"
    sqlite_path: Path = Path("var/dbrisco.sqlite3")
    postgresql_dsn: str | None = None

    @classmethod
    def from_env(cls) -> DatabaseSettings:
        """Load settings without guessing credentials or silently falling back."""
        backend = os.getenv("DATABASE_BACKEND", "sqlite").lower()
        if backend not in {"sqlite", "postgresql"}:
            raise DatabaseConfigurationError("DATABASE_BACKEND must be 'sqlite' or 'postgresql'")
        if backend == "postgresql":
            dsn = os.getenv("DATABASE_URL")
            if not dsn:
                raise DatabaseConfigurationError(
                    "DATABASE_URL is required when DATABASE_BACKEND=postgresql"
                )
            return cls(backend="postgresql", postgresql_dsn=dsn)
        return cls(
            backend="sqlite",
            sqlite_path=Path(os.getenv("DATABASE_SQLITE_PATH", "var/dbrisco.sqlite3")),
        )


class DatabaseManager:
    """Open transactions and apply immutable, checksummed SQL migrations."""

    def __init__(
        self,
        settings: DatabaseSettings | None = None,
        *,
        migrations_root: Path | None = None,
    ) -> None:
        self.settings = settings or DatabaseSettings.from_env()
        self.migrations_root = migrations_root or Path(__file__).parent / "migrations"

    def _connect(self) -> Any:
        if self.settings.backend == "sqlite":
            path = self.settings.sqlite_path
            if str(path) != ":memory:":
                path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection
        if not self.settings.postgresql_dsn:
            raise DatabaseConfigurationError("PostgreSQL DSN is missing")
        return psycopg2.connect(self.settings.postgresql_dsn, connect_timeout=5)

    @contextmanager
    def transaction(self) -> Generator[Any]:
        """Commit a successful unit of work and roll back every exception."""
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _sql(self, statement: str) -> str:
        if self.settings.backend == "postgresql":
            return statement.replace("?", "%s")
        return statement

    def execute(self, statement: str, parameters: Sequence[Any] = ()) -> int:
        with self.transaction() as connection:
            cursor = connection.cursor()
            cursor.execute(self._sql(statement), tuple(parameters))
            return int(cursor.rowcount)

    def fetch_one(self, statement: str, parameters: Sequence[Any] = ()) -> dict[str, Any] | None:
        with self.transaction() as connection:
            cursor = (
                connection.cursor(cursor_factory=RealDictCursor)
                if self.settings.backend == "postgresql"
                else connection.cursor()
            )
            cursor.execute(self._sql(statement), tuple(parameters))
            row = cursor.fetchone()
            return dict(row) if row is not None else None

    def fetch_all(self, statement: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        with self.transaction() as connection:
            cursor = (
                connection.cursor(cursor_factory=RealDictCursor)
                if self.settings.backend == "postgresql"
                else connection.cursor()
            )
            cursor.execute(self._sql(statement), tuple(parameters))
            return [dict(row) for row in cursor.fetchall()]

    def apply_migrations(self) -> tuple[str, ...]:
        """Apply pending migrations and verify checksums of prior migrations."""
        migration_dir = self.migrations_root / self.settings.backend
        migration_files = sorted(migration_dir.glob("[0-9][0-9][0-9][0-9]_*.sql"))
        if not migration_files:
            raise FileNotFoundError(f"No migrations found in {migration_dir}")

        applied_now: list[str] = []
        with self.transaction() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "version TEXT PRIMARY KEY, checksum TEXT NOT NULL, "
                "applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )
            cursor.execute("SELECT version, checksum FROM schema_migrations")
            applied: Mapping[str, str] = dict(cursor.fetchall())
            for migration_file in migration_files:
                version = migration_file.name.split("_", 1)[0]
                sql = migration_file.read_text(encoding="utf-8")
                checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
                if version in applied:
                    if applied[version] != checksum:
                        raise MigrationIntegrityError(
                            f"Migration {version} checksum does not match"
                        )
                    continue
                if self.settings.backend == "sqlite":
                    cursor.executescript(
                        "BEGIN IMMEDIATE;\n"
                        f"{sql}\n"
                        "INSERT INTO schema_migrations (version, checksum) "
                        f"VALUES ('{version}', '{checksum}');\n"
                        "COMMIT;"
                    )
                else:
                    cursor.execute(sql)
                    cursor.execute(
                        "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                        (version, checksum),
                    )
                applied_now.append(version)
        return tuple(applied_now)
