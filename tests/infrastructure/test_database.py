from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.infrastructure.database.manager import (
    DatabaseConfigurationError,
    DatabaseManager,
    DatabaseSettings,
    MigrationIntegrityError,
)
from src.infrastructure.database.repository import (
    PersistenceConflictError,
    VersionedRepository,
)


@pytest.fixture
def database(tmp_path: Path) -> DatabaseManager:
    manager = DatabaseManager(
        DatabaseSettings(backend="sqlite", sqlite_path=tmp_path / "risk.sqlite3")
    )
    assert manager.apply_migrations() == ("0001", "0002", "0003", "0004")
    return manager


@pytest.fixture
def repository(database: DatabaseManager) -> VersionedRepository:
    return VersionedRepository(database)


def test_settings_require_explicit_postgresql_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_BACKEND", "postgresql")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(DatabaseConfigurationError, match="DATABASE_URL"):
        DatabaseSettings.from_env()


def test_migrations_are_versioned_idempotent_and_separated(
    database: DatabaseManager,
) -> None:
    assert database.apply_migrations() == ()
    tables = {
        row["name"]
        for row in database.fetch_all("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {
        "operational_contracts",
        "operational_snapshots",
        "operational_macro_observations",
        "model_registry_models",
        "model_registry_scenarios",
        "calculation_executions",
        "calculation_results",
        "audit_lineage_events",
    } <= tables
    assert "users" not in tables


def test_changed_applied_migration_is_rejected(tmp_path: Path) -> None:
    migration_dir = tmp_path / "migrations" / "sqlite"
    migration_dir.mkdir(parents=True)
    migration = migration_dir / "0001_test.sql"
    migration.write_text("CREATE TABLE example (id INTEGER);", encoding="utf-8")
    manager = DatabaseManager(
        DatabaseSettings(sqlite_path=tmp_path / "checksum.sqlite3"),
        migrations_root=tmp_path / "migrations",
    )
    manager.apply_migrations()
    migration.write_text("CREATE TABLE changed (id INTEGER);", encoding="utf-8")

    with pytest.raises(MigrationIntegrityError, match="checksum"):
        manager.apply_migrations()


def test_failed_migration_is_rolled_back(tmp_path: Path) -> None:
    migration_dir = tmp_path / "migrations" / "sqlite"
    migration_dir.mkdir(parents=True)
    (migration_dir / "0001_broken.sql").write_text(
        "CREATE TABLE should_rollback (id INTEGER); INVALID SQL;", encoding="utf-8"
    )
    manager = DatabaseManager(
        DatabaseSettings(sqlite_path=tmp_path / "rollback.sqlite3"),
        migrations_root=tmp_path / "migrations",
    )

    with pytest.raises(sqlite3.OperationalError):
        manager.apply_migrations()

    tables = {
        row["name"]
        for row in manager.fetch_all("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert "should_rollback" not in tables


def test_persists_versioned_operational_and_model_inputs(
    repository: VersionedRepository,
    database: DatabaseManager,
) -> None:
    contract_hash = repository.persist_contract(
        "C-1", "source-2026-07", {"balance": Decimal("100.10")}
    )
    snapshot_hash = repository.persist_snapshot("S-1", date(2026, 6, 30), {"contracts": ["C-1"]})
    model_hash = repository.persist_model("PD", "1.0.0", {"artifact": "sha256:x"})
    scenario_hash = repository.persist_scenario("baseline", "2026.1", {"weight": Decimal("0.6000")})

    assert all(
        len(value) == 64 for value in (contract_hash, snapshot_hash, model_hash, scenario_hash)
    )
    row = database.fetch_one(
        "SELECT payload_json FROM operational_contracts WHERE contract_id = ?", ("C-1",)
    )
    assert row is not None
    assert '"100.10"' in row["payload_json"]


def test_immutable_input_is_idempotent_and_conflict_is_rejected(
    repository: VersionedRepository,
) -> None:
    first = repository.persist_contract("C-1", "v1", {"balance": Decimal("10.00")})
    assert repository.persist_contract("C-1", "v1", {"balance": Decimal("10.00")}) == first

    with pytest.raises(PersistenceConflictError, match="different content"):
        repository.persist_contract("C-1", "v1", {"balance": Decimal("11.00")})


def test_execution_reuse_and_explicit_reprocessing(
    repository: VersionedRepository,
    database: DatabaseManager,
) -> None:
    lineage = {
        "snapshot_hash": "s" * 64,
        "model_versions": {"pd": "1.0"},
        "scenario_version": "2026.1",
        "policy_hash": "p" * 64,
        "code_commit": "abc123",
    }
    first = repository.start_execution(
        execution_key="portfolio:2026-06-30",
        reference_date=date(2026, 6, 30),
        lineage=lineage,
    )
    reused = repository.start_execution(
        execution_key="portfolio:2026-06-30",
        reference_date=date(2026, 6, 30),
        lineage=lineage,
    )
    revised = repository.start_execution(
        execution_key="portfolio:2026-06-30",
        reference_date=date(2026, 6, 30),
        lineage={**lineage, "code_commit": "def456"},
        reprocess=True,
    )

    assert first["revision"] == 1 and first["reused"] is False
    assert reused["execution_id"] == first["execution_id"] and reused["reused"] is True
    assert revised["revision"] == 2
    persisted = database.fetch_one(
        "SELECT previous_execution_id FROM calculation_executions WHERE execution_id = ?",
        (revised["execution_id"],),
    )
    assert persisted == {"previous_execution_id": first["execution_id"]}


def test_execution_lineage_collision_requires_reprocess(
    repository: VersionedRepository,
) -> None:
    repository.start_execution(
        execution_key="run", reference_date=date(2026, 6, 30), lineage={"hash": "a"}
    )
    with pytest.raises(PersistenceConflictError, match="reprocess=True"):
        repository.start_execution(
            execution_key="run", reference_date=date(2026, 6, 30), lineage={"hash": "b"}
        )


def test_ecl_result_preserves_decimal_and_is_idempotent(
    repository: VersionedRepository,
    database: DatabaseManager,
) -> None:
    execution = repository.start_execution(
        execution_key="run", reference_date=date(2026, 6, 30), lineage={"hash": "a"}
    )
    arguments = {
        "execution_id": execution["execution_id"],
        "contract_id": "C-1",
        "period": 12,
        "scenario_id": "baseline",
        "ecl_amount": Decimal("1234567890.123456789"),
        "payload": {"pd": "0.01", "lgd": "0.40", "ead": "100.00"},
    }
    first_hash = repository.persist_ecl_result(**arguments)
    assert repository.persist_ecl_result(**arguments) == first_hash
    row = database.fetch_one("SELECT ecl_amount FROM calculation_results")
    assert row == {"ecl_amount": "1234567890.123456789"}

    with pytest.raises(PersistenceConflictError, match="different content"):
        repository.persist_ecl_result(
            **{**arguments, "ecl_amount": Decimal("1234567890.123456788")}
        )


def test_audit_lineage_event_is_immutable(
    repository: VersionedRepository,
    database: DatabaseManager,
) -> None:
    execution = repository.start_execution(
        execution_key="run", reference_date=date(2026, 6, 30), lineage={"hash": "a"}
    )
    event_id = repository.record_lineage_event(
        execution_id=execution["execution_id"],
        event_type="EXECUTION_STARTED",
        payload={"actor": "system"},
    )

    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute(
            "UPDATE audit_lineage_events SET event_type = ? WHERE event_id = ?",
            ("CHANGED", event_id),
        )
