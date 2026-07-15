"""Structured JSON logging with request, trace, and job correlation."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from ..observability.context import current_context

EXTRA_FIELDS = (
    "event",
    "method",
    "route",
    "status_code",
    "duration_seconds",
    "job_type",
    "job_status",
    "contract_count",
    "recovered_jobs",
)


class JsonFormatter(logging.Formatter):
    """Serialize allowlisted operational fields without payload or credential leakage."""

    def __init__(self, **defaults: Any) -> None:
        super().__init__()
        self.defaults = defaults

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, UTC).isoformat().replace("+00:00", "Z")
        log_data: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **self.defaults,
        }
        context = current_context()
        for key, value in context.items():
            if value is not None:
                log_data[key] = value
        for key in EXTRA_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                log_data[key] = value
        if record.exc_info:
            exception_type = record.exc_info[0]
            log_data["exception_type"] = (
                exception_type.__name__ if exception_type else "UnknownException"
            )
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False, separators=(",", ":"), default=str)


def setup_json_logging(level: int | None = None) -> None:
    """Install one idempotent JSON handler on the process root logger."""
    root = logging.getLogger()
    if any(getattr(handler, "_risk_json_handler", False) for handler in root.handlers):
        return
    handler = logging.StreamHandler()
    handler._risk_json_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(
        JsonFormatter(
            service="risco-bancario-api",
            service_version=os.getenv("APP_VERSION", "unreleased"),
            environment=os.getenv("APP_ENV", "local"),
        )
    )
    root.addHandler(handler)
    selected_level: int | str = level if level is not None else os.getenv("LOG_LEVEL", "INFO")
    root.setLevel(selected_level)
