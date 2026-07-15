"""Versioned persistence repository with deterministic lineage hashes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from .manager import DatabaseManager


class PersistenceConflictError(RuntimeError):
    """Raised when an immutable identity is reused with different content."""


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Return stable JSON while preserving Decimal and temporal values exactly."""

    def encode(value: Any) -> str:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        raise TypeError(f"Unsupported persistence value: {type(value).__name__}")

    return json.dumps(
        payload,
        default=encode,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def payload_hash(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


class VersionedRepository:
    """Persist immutable inputs and revisioned ECL executions."""

    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def _persist_immutable(
        self,
        table: str,
        identity_columns: Mapping[str, str],
        payload: Mapping[str, Any],
    ) -> str:
        serialized = canonical_json(payload)
        digest = payload_hash(serialized)
        where = " AND ".join(f"{column} = ?" for column in identity_columns)
        existing = self.database.fetch_one(
            f"SELECT payload_hash FROM {table} WHERE {where}",
            tuple(identity_columns.values()),
        )
        if existing:
            if existing["payload_hash"] != digest:
                raise PersistenceConflictError(
                    f"Immutable identity already exists with different content in {table}"
                )
            return digest
        columns = [*identity_columns, "payload_json", "payload_hash"]
        placeholders = ", ".join("?" for _ in columns)
        self.database.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            (*identity_columns.values(), serialized, digest),
        )
        return digest

    def persist_contract(
        self, contract_id: str, source_version: str, payload: Mapping[str, Any]
    ) -> str:
        return self._persist_immutable(
            "operational_contracts",
            {"contract_id": contract_id, "source_version": source_version},
            payload,
        )

    def persist_snapshot(
        self, snapshot_id: str, reference_date: date, payload: Mapping[str, Any]
    ) -> str:
        return self._persist_immutable(
            "operational_snapshots",
            {"snapshot_id": snapshot_id, "reference_date": reference_date.isoformat()},
            payload,
        )

    def persist_model(self, model_id: str, version: str, payload: Mapping[str, Any]) -> str:
        return self._persist_immutable(
            "model_registry_models",
            {"model_id": model_id, "version": version},
            payload,
        )

    def persist_scenario(self, scenario_id: str, version: str, payload: Mapping[str, Any]) -> str:
        return self._persist_immutable(
            "model_registry_scenarios",
            {"scenario_id": scenario_id, "version": version},
            payload,
        )

    def start_execution(
        self,
        *,
        execution_key: str,
        reference_date: date,
        lineage: Mapping[str, Any],
        reprocess: bool = False,
    ) -> dict[str, Any]:
        """Create/reuse an execution, or create a linked revision on reprocessing."""
        lineage_json = canonical_json(lineage)
        lineage_digest = payload_hash(lineage_json)
        previous = self.database.fetch_one(
            "SELECT execution_id, revision, lineage_hash FROM calculation_executions "
            "WHERE execution_key = ? ORDER BY revision DESC LIMIT 1",
            (execution_key,),
        )
        if previous and not reprocess:
            if previous["lineage_hash"] != lineage_digest:
                raise PersistenceConflictError(
                    "Execution key already exists with different lineage; use reprocess=True"
                )
            return {**previous, "reused": True}

        revision = int(previous["revision"]) + 1 if previous else 1
        execution_id = hashlib.sha256(
            f"{execution_key}:{revision}:{lineage_digest}".encode()
        ).hexdigest()
        self.database.execute(
            "INSERT INTO calculation_executions "
            "(execution_id, execution_key, revision, previous_execution_id, "
            "reference_date, lineage_json, lineage_hash, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                execution_id,
                execution_key,
                revision,
                previous["execution_id"] if previous else None,
                reference_date.isoformat(),
                lineage_json,
                lineage_digest,
                "STARTED",
            ),
        )
        return {
            "execution_id": execution_id,
            "revision": revision,
            "lineage_hash": lineage_digest,
            "reused": False,
        }

    def persist_ecl_result(
        self,
        *,
        execution_id: str,
        contract_id: str,
        period: int,
        scenario_id: str,
        ecl_amount: Decimal,
        payload: Mapping[str, Any],
    ) -> str:
        result_payload = {**payload, "ecl_amount": ecl_amount}
        serialized = canonical_json(result_payload)
        digest = payload_hash(serialized)
        identity = (execution_id, contract_id, period, scenario_id)
        existing = self.database.fetch_one(
            "SELECT payload_hash FROM calculation_results WHERE execution_id = ? "
            "AND contract_id = ? AND period = ? AND scenario_id = ?",
            identity,
        )
        if existing:
            if existing["payload_hash"] != digest:
                raise PersistenceConflictError(
                    "ECL result identity already exists with different content"
                )
            return digest
        self.database.execute(
            "INSERT INTO calculation_results "
            "(execution_id, contract_id, period, scenario_id, ecl_amount, "
            "payload_json, payload_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (*identity, str(ecl_amount), serialized, digest),
        )
        return digest

    def complete_execution(self, execution_id: str) -> None:
        """Mark an execution complete after every result and lineage event persisted."""

        row = self.database.fetch_one(
            "SELECT status FROM calculation_executions WHERE execution_id = ?",
            (execution_id,),
        )
        if row is None:
            raise PersistenceConflictError("Cannot complete an unknown execution")
        if row["status"] == "COMPLETED":
            return
        updated = self.database.execute(
            "UPDATE calculation_executions SET status = ? " "WHERE execution_id = ? AND status = ?",
            ("COMPLETED", execution_id, "STARTED"),
        )
        if updated != 1:
            raise PersistenceConflictError("Execution is not in STARTED state")

    def record_lineage_event(
        self, *, execution_id: str, event_type: str, payload: Mapping[str, Any]
    ) -> str:
        serialized = canonical_json(payload)
        digest = payload_hash(serialized)
        event_id = hashlib.sha256(f"{execution_id}:{event_type}:{digest}".encode()).hexdigest()
        if self.database.fetch_one(
            "SELECT event_id FROM audit_lineage_events WHERE event_id = ?", (event_id,)
        ):
            return event_id
        self.database.execute(
            "INSERT INTO audit_lineage_events "
            "(event_id, execution_id, event_type, payload_json, payload_hash, occurred_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                event_id,
                execution_id,
                event_type,
                serialized,
                digest,
                datetime.now(UTC).isoformat(),
            ),
        )
        return event_id
