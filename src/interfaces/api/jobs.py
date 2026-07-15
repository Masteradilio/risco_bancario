"""Persisted job status for asynchronous portfolio requests."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ...infrastructure.database import DatabaseManager


class JobStore:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def create(self, request_json: str) -> str:
        job_id = str(uuid4())
        self.database.execute(
            "INSERT INTO calculation_jobs "
            "(job_id, status, request_hash, request_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                job_id,
                "PENDING",
                hashlib.sha256(request_json.encode()).hexdigest(),
                request_json,
                datetime.now(UTC).isoformat(),
            ),
        )
        return job_id

    def running(self, job_id: str) -> None:
        self.database.execute(
            "UPDATE calculation_jobs SET status = ?, started_at = ? WHERE job_id = ?",
            ("RUNNING", datetime.now(UTC).isoformat(), job_id),
        )

    def succeeded(self, job_id: str, result: list[dict[str, Any]]) -> None:
        self.database.execute(
            "UPDATE calculation_jobs SET status = ?, result_json = ?, finished_at = ? "
            "WHERE job_id = ?",
            ("SUCCEEDED", json.dumps(result), datetime.now(UTC).isoformat(), job_id),
        )

    def failed(self, job_id: str, error_code: str) -> None:
        self.database.execute(
            "UPDATE calculation_jobs SET status = ?, error_code = ?, finished_at = ? "
            "WHERE job_id = ?",
            ("FAILED", error_code, datetime.now(UTC).isoformat(), job_id),
        )

    def get(self, job_id: str) -> dict[str, Any] | None:
        return self.database.fetch_one(
            "SELECT job_id, status, request_hash, result_json, error_code "
            "FROM calculation_jobs WHERE job_id = ?",
            (job_id,),
        )
