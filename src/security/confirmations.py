"""One-time, payload-bound confirmation for critical operations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from ..infrastructure.database import DatabaseManager
from .settings import SecuritySettings


class ConfirmationError(ValueError):
    pass


def _utc_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value).astimezone(UTC)
    raise ConfirmationError("invalid persisted timestamp")


class ConfirmationService:
    def __init__(self, database: DatabaseManager, settings: SecuritySettings) -> None:
        self.database = database
        self.settings = settings

    def issue(self, user_id: str, action: str, payload_hash: str) -> str:
        if len(payload_hash) != 64 or any(
            character not in "0123456789abcdef" for character in payload_hash
        ):
            raise ConfirmationError("payload_hash must be a lowercase SHA-256")
        now = datetime.now(UTC)
        confirmation_id = str(uuid4())
        self.database.execute(
            "INSERT INTO security_confirmations "
            "(confirmation_id, user_id, action, payload_hash, expires_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                confirmation_id,
                user_id,
                action,
                payload_hash,
                (now + timedelta(minutes=self.settings.confirmation_minutes)).isoformat(),
                now.isoformat(),
            ),
        )
        return confirmation_id

    def consume(self, confirmation_id: str, user_id: str, action: str, payload_hash: str) -> None:
        row = self.database.fetch_one(
            "SELECT user_id, action, payload_hash, expires_at, consumed_at "
            "FROM security_confirmations WHERE confirmation_id = ?",
            (confirmation_id,),
        )
        if (
            row is None
            or row["user_id"] != user_id
            or row["action"] != action
            or row["payload_hash"] != payload_hash
            or row["consumed_at"] is not None
            or _utc_timestamp(row["expires_at"]) <= datetime.now(UTC)
        ):
            raise ConfirmationError("invalid, expired, or consumed confirmation")
        updated = self.database.execute(
            "UPDATE security_confirmations SET consumed_at = ? "
            "WHERE confirmation_id = ? AND consumed_at IS NULL",
            (datetime.now(UTC).isoformat(), confirmation_id),
        )
        if updated != 1:
            raise ConfirmationError("confirmation was already consumed")
