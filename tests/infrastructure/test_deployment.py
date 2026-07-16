from __future__ import annotations

import json
import subprocess
import sys
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
    with pytest.raises(ValueError, match="non-empty"):
        local.validate_image_tag(" ")
    demo.validate_image_tag("v1.2.3")


def test_environment_profile_loader_rejects_name_secret_identity_and_demo_mode(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="local, test or demo"):
        load_environment_profile("production")

    root = tmp_path / "profiles"
    root.mkdir()
    base = {
        "schema_version": 1,
        "name": "test",
        "database_backend": "sqlite",
        "migration_mode": "apply",
        "release_tag_policy": "any",
        "compose_profile": "test",
    }
    (root / "test.json").write_text(json.dumps(base | {"db_password": "secret"}), encoding="utf-8")
    with pytest.raises(ValueError, match="must not contain secrets"):
        load_environment_profile("test", root)

    (root / "test.json").write_text(json.dumps(base | {"schema_version": 2}), encoding="utf-8")
    with pytest.raises(ValueError, match="identity or schema"):
        load_environment_profile("test", root)

    demo = base | {
        "name": "demo",
        "database_backend": "postgresql",
        "migration_mode": "apply",
        "release_tag_policy": "semver",
        "compose_profile": "demo",
    }
    (root / "demo.json").write_text(json.dumps(demo), encoding="utf-8")
    with pytest.raises(ValueError, match="validate migrations"):
        load_environment_profile("demo", root)


def test_delivery_plan_runs_without_runtime_database_dependencies(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-m",
            "scripts.deploy",
            "plan",
            "--environment",
            "demo",
            "--image-tag",
            "v2.0.2",
            "--commit",
            "a" * 40,
            "--output",
            str(tmp_path / "plan.json"),
        ],
        cwd=Path(__file__).parents[2],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    assert plan["image_tag"] == "v2.0.2"


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


def test_deployment_state_rejects_unknown_schema(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text('{"schema_version": 2, "environments": {}}', encoding="utf-8")
    store = DeploymentStateStore(state_path)

    with pytest.raises(DeploymentStateError, match="unsupported"):
        store.plan(load_environment_profile("test"), "candidate-1", "a" * 40)
