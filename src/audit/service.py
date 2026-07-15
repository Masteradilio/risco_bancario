"""Append-only, hash-chained audit events with payload minimization."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ..infrastructure.database import DatabaseManager
from ..infrastructure.database.repository import canonical_json, payload_hash


class AuditChainError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    action: str
    resource_type: str
    resource_id: str
    status: str
    input_hash: str
    result_hash: str
    previous_event_hash: str | None
    event_hash: str
    occurred_at: str


class AuditService:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def record(
        self,
        *,
        actor_id: str,
        actor_role: str | None,
        action: str,
        resource_type: str,
        resource_id: str,
        input_payload: dict[str, Any],
        result_payload: dict[str, Any],
        versions: dict[str, Any],
        status: str,
        client_ip: str | None = None,
        execution_id: str | None = None,
        reason: str | None = None,
    ) -> AuditEvent:
        occurred_at = datetime.now(UTC).isoformat()
        event_id = str(uuid4())
        input_digest = payload_hash(canonical_json(input_payload))
        result_digest = payload_hash(canonical_json(result_payload))
        versions_json = canonical_json(versions)
        previous = self.database.fetch_one(
            "SELECT event_hash FROM audit_events ORDER BY audit_sequence DESC LIMIT 1"
        )
        previous_hash = previous["event_hash"] if previous else None
        event_document = {
            "event_id": event_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "execution_id": execution_id,
            "status": status,
            "input_hash": input_digest,
            "result_hash": result_digest,
            "versions": versions,
            "client_ip": client_ip,
            "reason": reason,
            "occurred_at": occurred_at,
        }
        event_json = canonical_json(event_document)
        event_hash = hashlib.sha256(f"{previous_hash or ''}:{event_json}".encode()).hexdigest()
        self.database.execute(
            "INSERT INTO audit_events "
            "(event_id, actor_id, actor_role, action, resource_type, resource_id, "
            "execution_id, status, input_hash, result_hash, versions_json, event_json, "
            "previous_event_hash, event_hash, occurred_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event_id,
                actor_id,
                actor_role,
                action,
                resource_type,
                resource_id,
                execution_id,
                status,
                input_digest,
                result_digest,
                versions_json,
                event_json,
                previous_hash,
                event_hash,
                occurred_at,
            ),
        )
        return AuditEvent(
            event_id,
            action,
            resource_type,
            resource_id,
            status,
            input_digest,
            result_digest,
            previous_hash,
            event_hash,
            occurred_at,
        )

    def record_override(
        self,
        *,
        actor_id: str,
        actor_role: str,
        execution_id: str,
        override_type: str,
        before: dict[str, Any],
        after: dict[str, Any],
        reason: str,
    ) -> AuditEvent:
        if not reason.strip():
            raise ValueError("override reason is required")
        action = "MANAGEMENT_OVERLAY" if override_type == "management_overlay" else "ECL_OVERRIDE"
        return self.record(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            resource_type=override_type,
            resource_id=execution_id,
            execution_id=execution_id,
            input_payload=before,
            result_payload=after,
            versions={},
            status="SUCCEEDED",
            reason=reason,
        )

    def record_export_or_validation(
        self,
        *,
        actor_id: str,
        actor_role: str,
        action: str,
        artifact_id: str,
        input_payload: dict[str, Any],
        result_payload: dict[str, Any],
        versions: dict[str, Any],
        status: str,
    ) -> AuditEvent:
        if action not in {"REGULATORY_EXPORT", "REGULATORY_VALIDATION"}:
            raise ValueError("unsupported audit action")
        return self.record(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            resource_type="regulatory_artifact",
            resource_id=artifact_id,
            input_payload=input_payload,
            result_payload=result_payload,
            versions=versions,
            status=status,
        )

    def verify_chain(self) -> int:
        rows = self.database.fetch_all(
            "SELECT event_json, previous_event_hash, event_hash "
            "FROM audit_events ORDER BY audit_sequence"
        )
        previous: str | None = None
        for row in rows:
            expected = hashlib.sha256(f"{previous or ''}:{row['event_json']}".encode()).hexdigest()
            if row["previous_event_hash"] != previous or row["event_hash"] != expected:
                raise AuditChainError("audit hash chain is invalid")
            previous = row["event_hash"]
        return len(rows)

    def list_events(self, *, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 1000:
            raise ValueError("audit limit must be between 1 and 1000")
        return self.database.fetch_all(
            "SELECT audit_sequence, event_id, actor_id, actor_role, action, "
            "resource_type, resource_id, execution_id, status, input_hash, result_hash, "
            "versions_json, previous_event_hash, event_hash, occurred_at "
            "FROM audit_events ORDER BY audit_sequence DESC LIMIT ?",
            (limit,),
        )
