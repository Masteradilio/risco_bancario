"""W3C trace-context propagation using context-local correlation identifiers."""

from __future__ import annotations

import re
import secrets
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token

TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_span_id: ContextVar[str | None] = ContextVar("span_id", default=None)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_job_id: ContextVar[str | None] = ContextVar("job_id", default=None)


def current_context() -> dict[str, str | None]:
    return {
        "trace_id": _trace_id.get(),
        "span_id": _span_id.get(),
        "request_id": _request_id.get(),
        "job_id": _job_id.get(),
    }


def _identifier(bytes_count: int) -> str:
    value = "0" * (bytes_count * 2)
    while set(value) == {"0"}:
        value = secrets.token_hex(bytes_count)
    return value


@contextmanager
def request_context(traceparent: str | None, request_id: str | None) -> Generator[str]:
    match = TRACEPARENT.fullmatch(traceparent or "")
    inbound_trace = match.group(1) if match and set(match.group(1)) != {"0"} else None
    trace_id = inbound_trace or _identifier(16)
    span_id = _identifier(8)
    safe_request_id = request_id if request_id and len(request_id) <= 128 else _identifier(16)
    tokens: tuple[tuple[ContextVar[str | None], Token[str | None]], ...] = (
        (_trace_id, _trace_id.set(trace_id)),
        (_span_id, _span_id.set(span_id)),
        (_request_id, _request_id.set(safe_request_id)),
    )
    try:
        yield f"00-{trace_id}-{span_id}-01"
    finally:
        for variable, token in reversed(tokens):
            variable.reset(token)


@contextmanager
def job_context(job_id: str) -> Generator[None]:
    token = _job_id.set(job_id)
    try:
        yield
    finally:
        _job_id.reset(token)
