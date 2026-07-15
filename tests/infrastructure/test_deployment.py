from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.infrastructure.database import (
    DatabaseManager,
    DatabaseSettings,
    PendingMigrationsError,
)
from src.infrastructure.database.startup import migration_mode_from_env, prepare_database
from src.infrastructure.deployment import (
    DeploymentStateError,
    DeploymentStateStore,
    load_environment_profile,
)


def test_environment_profiles_are_separate_secret_free_and_strict() -> None:
    local = load_environment_profile("local")
    test = load_environment_profile("test")
    demo = load_environment_profile("demo")

    assert (local.database_backend, test.database_backend) == ("sqlite", "sqlite")
    assert demo.database_backend == "postgresql"
    assert demo.migration_mode == "validate"
    with pytest.raises(ValueError, match="semantic version"):
        demo.validate_image_tag("latest")
    demo.validate_image_tag("v1.2.3")


def test_validate_mode_is_read_only_and_requires_current_schema(tmp_path: Path) -> None:
    database = DatabaseManager(DatabaseSettings(sqlite_path=tmp_path / "risk.sqlite3"))

    with pytest.raises(PendingMigrationsError, match="0001, 0002, 0003, 0004"):
        prepare_database(database, "validate")
    assert not (tmp_path / "risk.sqlite3").exists() or database.migration_status().applied == ()

    assert prepare_database(database, "apply") == ("0001", "0002", "0003", "0004")
    assert prepare_database(database, "validate") == ("0001", "0002", "0003", "0004")


def test_demo_rejects_automatic_or_disabled_migrations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "demo")
    for mode in ("apply", "disabled"):
        monkeypatch.setenv("DATABASE_MIGRATION_MODE", mode)
        with pytest.raises(ValueError, match="requires.*validate"):
            migration_mode_from_env()


def test_promotion_and_application_rollback_are_atomic(tmp_path: Path) -> None:
    profile = load_environment_profile("test")
    store = DeploymentStateStore(tmp_path / "state.json")

    with pytest.raises(DeploymentStateError, match="no previous"):
        store.rollback(profile)
    store.promote(profile, "candidate-1", "a" * 40)
    with pytest.raises(DeploymentStateError, match="immutable image tag"):
        store.promote(profile, "candidate-1", "c" * 40)
    store.promote(profile, "candidate-2", "b" * 40)
    rollback = store.rollback(profile)

    assert rollback["restored"]["image_tag"] == "candidate-1"
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["environments"]["test"]["current"]["commit"] == "a" * 40
    assert rollback["database_rollback"] == "not_performed_forward_only"
