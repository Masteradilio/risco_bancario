from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from src.audit import AuditChainError, AuditService
from src.infrastructure.database import DatabaseManager, DatabaseSettings, VersionedRepository


@pytest.fixture
def database(tmp_path: Path) -> DatabaseManager:
    manager = DatabaseManager(
        DatabaseSettings(backend="sqlite", sqlite_path=tmp_path / "audit.sqlite3")
    )
    manager.apply_migrations()
    return manager


def test_event_hashes_inputs_results_versions_and_actor(database: DatabaseManager) -> None:
    service = AuditService(database)
    event = service.record(
        actor_id="user-1",
        actor_role="ANALYST",
        action="ECL_CALCULATE_INDIVIDUAL",
        resource_type="contract",
        resource_id="C-1",
        input_payload={"tax_id": "sensitive-value", "balance": "100.00"},
        result_payload={"ecl": "4.00"},
        versions={"policy": "2026.07.1", "code": "abcdef1"},
        status="SUCCEEDED",
        client_ip="127.0.0.1",
    )

    row = database.fetch_one("SELECT * FROM audit_events WHERE event_id = ?", (event.event_id,))
    assert row is not None
    assert row["actor_id"] == "user-1"
    assert row["actor_role"] == "ANALYST"
    assert len(row["input_hash"]) == len(row["result_hash"]) == 64
    assert "sensitive-value" not in row["event_json"]
    assert "2026.07.1" in row["versions_json"]
    assert service.verify_chain() == 1


def test_chain_links_events_and_table_is_immutable(database: DatabaseManager) -> None:
    service = AuditService(database)
    first = service.record(
        actor_id="user-1",
        actor_role="MANAGER",
        action="FIRST",
        resource_type="job",
        resource_id="J-1",
        input_payload={},
        result_payload={},
        versions={},
        status="SUCCEEDED",
    )
    second = service.record(
        actor_id="user-1",
        actor_role="MANAGER",
        action="SECOND",
        resource_type="job",
        resource_id="J-2",
        input_payload={},
        result_payload={},
        versions={},
        status="SUCCEEDED",
    )

    assert second.previous_event_hash == first.event_hash
    assert service.verify_chain() == 2
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute("DELETE FROM audit_events WHERE event_id = ?", (first.event_id,))


def test_chain_verifier_detects_privileged_tampering(database: DatabaseManager) -> None:
    service = AuditService(database)
    event = service.record(
        actor_id="system",
        actor_role=None,
        action="TEST",
        resource_type="test",
        resource_id="1",
        input_payload={},
        result_payload={},
        versions={},
        status="SUCCEEDED",
    )
    database.execute("DROP TRIGGER audit_events_no_update")
    database.execute(
        "UPDATE audit_events SET event_json = ? WHERE event_id = ?", ("{}", event.event_id)
    )

    with pytest.raises(AuditChainError, match="invalid"):
        service.verify_chain()


def test_override_overlay_export_and_validation_contracts(database: DatabaseManager) -> None:
    repository = VersionedRepository(database)
    execution = repository.start_execution(
        execution_key="audit-run",
        reference_date=date(2026, 6, 30),
        lineage={"code": "abcdef1"},
    )
    service = AuditService(database)

    with pytest.raises(ValueError, match="reason"):
        service.record_override(
            actor_id="manager",
            actor_role="MANAGER",
            execution_id=execution["execution_id"],
            override_type="management_overlay",
            before={"overlay": "0.00"},
            after={"overlay": "10.00"},
            reason=" ",
        )
    override = service.record_override(
        actor_id="manager",
        actor_role="MANAGER",
        execution_id=execution["execution_id"],
        override_type="stage_override",
        before={"stage": 1},
        after={"stage": 2},
        reason="governed committee decision",
    )
    overlay = service.record_override(
        actor_id="manager",
        actor_role="MANAGER",
        execution_id=execution["execution_id"],
        override_type="management_overlay",
        before={"overlay": "0.00"},
        after={"overlay": "10.00"},
        reason="governed committee decision",
    )
    exported = service.record_export_or_validation(
        actor_id="manager",
        actor_role="MANAGER",
        action="REGULATORY_EXPORT",
        artifact_id="doc3040-1",
        input_payload={"execution_id": execution["execution_id"]},
        result_payload={"artifact_hash": "a" * 64},
        versions={"layout": "2026.1"},
        status="SUCCEEDED",
    )
    validated = service.record_export_or_validation(
        actor_id="manager",
        actor_role="MANAGER",
        action="REGULATORY_VALIDATION",
        artifact_id="doc3040-1",
        input_payload={"artifact_hash": "a" * 64},
        result_payload={"valid": True},
        versions={"validator": "2026.1"},
        status="SUCCEEDED",
    )

    assert override.action == "ECL_OVERRIDE"
    assert overlay.action == "MANAGEMENT_OVERLAY"
    assert exported.action == "REGULATORY_EXPORT"
    assert validated.action == "REGULATORY_VALIDATION"
    assert service.verify_chain() == 4
