"""Explicit retention for ephemeral security and batch-processing records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ..infrastructure.database import DatabaseManager

DEFAULT_POLICY_PATH = Path("config/security/retention.json")


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    expired_sessions_days: int
    expired_confirmations_days: int
    finished_jobs_days: int
    generated_exports_days: int
    policy_version: str

    def __post_init__(self) -> None:
        values = (
            self.expired_sessions_days,
            self.expired_confirmations_days,
            self.finished_jobs_days,
            self.generated_exports_days,
        )
        if any(value <= 0 for value in values) or not self.policy_version:
            raise ValueError("retention periods and policy version must be positive")


@dataclass(frozen=True, slots=True)
class RetentionResult:
    deleted_sessions: int
    deleted_confirmations: int
    deleted_jobs: int
    policy_version: str


def load_retention_policy(path: Path = DEFAULT_POLICY_PATH) -> RetentionPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return RetentionPolicy(
        expired_sessions_days=int(payload["expired_sessions_days"]),
        expired_confirmations_days=int(payload["expired_confirmations_days"]),
        finished_jobs_days=int(payload["finished_jobs_days"]),
        generated_exports_days=int(payload["generated_exports_days"]),
        policy_version=str(payload["policy_version"]),
    )


def purge_ephemeral_records(
    database: DatabaseManager,
    policy: RetentionPolicy,
    *,
    now: datetime | None = None,
) -> RetentionResult:
    """Delete only explicitly ephemeral records; evidence and audit tables are untouched."""
    current = (now or datetime.now(UTC)).astimezone(UTC)
    session_cutoff = (current - timedelta(days=policy.expired_sessions_days)).isoformat()
    confirmation_cutoff = (current - timedelta(days=policy.expired_confirmations_days)).isoformat()
    job_cutoff = (current - timedelta(days=policy.finished_jobs_days)).isoformat()
    sessions = database.execute(
        "DELETE FROM security_sessions WHERE expires_at < ?",
        (session_cutoff,),
    )
    confirmations = database.execute(
        "DELETE FROM security_confirmations WHERE expires_at < ?",
        (confirmation_cutoff,),
    )
    jobs = database.execute(
        "DELETE FROM calculation_jobs WHERE status IN (?, ?) AND finished_at < ?",
        ("SUCCEEDED", "FAILED", job_cutoff),
    )
    return RetentionResult(sessions, confirmations, jobs, policy.policy_version)
