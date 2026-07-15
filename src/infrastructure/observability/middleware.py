"""FastAPI middleware for structured access logs, metrics, and trace propagation."""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

from ..logging import setup_json_logging
from .context import current_context, request_context
from .metrics import MetricsRegistry

logger = logging.getLogger("risco_bancario.http")


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return str(path) if path else "unmatched"


def configure_observability(application: FastAPI) -> MetricsRegistry:
    setup_json_logging()
    metrics = MetricsRegistry(
        environment=os.getenv("APP_ENV", "local"),
        version=os.getenv("APP_VERSION", "unreleased"),
    )
    application.state.metrics = metrics

    @application.middleware("http")
    async def observe_request(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = perf_counter()
        with request_context(
            request.headers.get("traceparent"), request.headers.get("x-request-id")
        ) as outbound_traceparent:
            logger.info(
                "HTTP request started",
                extra={"event": "http.request.started", "method": request.method},
            )
            try:
                response = await call_next(request)
            except Exception:
                duration = perf_counter() - started
                route = _route_template(request)
                metrics.observe_http(request.method, route, 500, duration)
                logger.exception(
                    "HTTP request failed",
                    extra={
                        "event": "http.request.failed",
                        "method": request.method,
                        "route": route,
                        "status_code": 500,
                        "duration_seconds": duration,
                    },
                )
                raise
            duration = perf_counter() - started
            route = _route_template(request)
            metrics.observe_http(request.method, route, response.status_code, duration)
            context = current_context()
            response.headers["traceparent"] = outbound_traceparent
            if context["request_id"]:
                response.headers["X-Request-ID"] = context["request_id"]
            logger.info(
                "HTTP request completed",
                extra={
                    "event": "http.request.completed",
                    "method": request.method,
                    "route": route,
                    "status_code": response.status_code,
                    "duration_seconds": duration,
                },
            )
            return response

    @application.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> PlainTextResponse:
        return PlainTextResponse(
            metrics.render(), media_type="text/plain; version=0.0.4; charset=utf-8"
        )

    return metrics
