from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.database import DatabaseSettings
from src.infrastructure.logging import JsonFormatter, setup_json_logging
from src.infrastructure.observability import middleware as middleware_module
from src.infrastructure.observability.context import job_context, request_context
from src.infrastructure.observability.metrics import MetricsRegistry
from src.infrastructure.observability.middleware import configure_observability
from src.interfaces.api import create_app
from src.security.settings import SecuritySettings

ROOT = Path(__file__).resolve().parents[2]


def test_json_logs_include_utc_trace_request_and_job_correlation() -> None:
    formatter = JsonFormatter(service="test", environment="test")
    record = logging.LogRecord(
        "risk.test", logging.INFO, __file__, 10, "processed %s", ("item",), None
    )
    record.event = "test.completed"

    with request_context(None, "request-1"):
        with job_context("job-1"):
            payload = json.loads(formatter.format(record))

    assert payload["timestamp"].endswith("Z")
    assert payload["message"] == "processed item"
    assert payload["event"] == "test.completed"
    assert payload["request_id"] == "request-1"
    assert payload["job_id"] == "job-1"
    assert len(payload["trace_id"]) == 32 and len(payload["span_id"]) == 16


def test_json_logs_capture_exception_metadata_and_setup_is_idempotent() -> None:
    formatter = JsonFormatter()
    try:
        raise ValueError("expected")
    except ValueError:
        record = logging.LogRecord(
            "risk.test", logging.ERROR, __file__, 1, "failed", (), sys.exc_info()
        )
    payload = json.loads(formatter.format(record))
    assert payload["exception_type"] == "ValueError"
    assert "expected" in payload["exception"]

    root = logging.getLogger()
    before = len(root.handlers)
    setup_json_logging(logging.WARNING)
    after_first = len(root.handlers)
    setup_json_logging(logging.INFO)
    assert len(root.handlers) == after_first
    assert after_first in {before, before + 1}


def test_w3c_trace_is_propagated_with_a_new_server_span() -> None:
    inbound = "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"
    with request_context(inbound, None) as outbound:
        parts = outbound.split("-")
        assert parts[1] == inbound.split("-")[1]
        assert parts[2] != inbound.split("-")[2]


def test_metrics_use_bounded_labels_and_prometheus_histograms() -> None:
    metrics = MetricsRegistry(environment="test", version="abc")
    metrics.observe_http("GET", "/api/v1/ecl/jobs/{job_id}", 200, 0.04)
    metrics.job_started("ecl_portfolio")
    metrics.job_finished("ecl_portfolio", "succeeded", 0.2)
    rendered = metrics.render()

    assert 'route="/api/v1/ecl/jobs/{job_id}"' in rendered
    assert 'status_class="2xx"' in rendered
    assert "risco_http_request_duration_seconds_bucket" in rendered
    assert 'risco_jobs_total{job_type="ecl_portfolio",status="succeeded"} 1' in rendered
    assert 'risco_jobs_in_progress{job_type="ecl_portfolio"} 0' in rendered


def test_api_exposes_metrics_and_request_correlation(tmp_path: Path) -> None:
    app = create_app(
        DatabaseSettings(sqlite_path=tmp_path / "api.sqlite3"),
        SecuritySettings(jwt_secret="o" * 48),
    )
    client = TestClient(app)

    response = client.get("/health", headers={"X-Request-ID": "external-request"})
    metrics = client.get("/metrics")

    assert response.headers["X-Request-ID"] == "external-request"
    assert response.headers["traceparent"].startswith("00-")
    assert metrics.status_code == 200
    assert 'route="/health"' in metrics.text
    assert "risco_application_info" in metrics.text


def test_observability_records_failed_requests_and_optional_request_id(
    monkeypatch,
) -> None:
    app = FastAPI()
    metrics = configure_observability(app)

    @app.get("/failure")
    def failure() -> None:
        raise RuntimeError("expected")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/failure")
    assert response.status_code == 500
    assert 'route="/failure"' in metrics.render()
    assert 'status_class="5xx"' in metrics.render()

    monkeypatch.setattr(
        middleware_module,
        "current_context",
        lambda: {"request_id": None, "trace_id": "a" * 32, "span_id": "b" * 16, "job_id": None},
    )
    app = FastAPI()
    configure_observability(app)

    @app.get("/ok")
    def ok() -> dict[str, bool]:
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/ok")
    assert "X-Request-ID" not in response.headers


def test_prometheus_alerts_and_grafana_dashboard_are_provisioned() -> None:
    alerts = yaml.safe_load(
        (ROOT / "config/observability/alert_rules.yml").read_text(encoding="utf-8")
    )
    dashboard = json.loads(
        (ROOT / "config/observability/grafana/dashboards/platform.json").read_text(encoding="utf-8")
    )
    alert_names = {rule["alert"] for group in alerts["groups"] for rule in group["rules"]}

    assert {"RiscoApiUnavailable", "RiscoApiHighServerErrorRatio"} <= alert_names
    assert {"RiscoPortfolioJobFailure", "RiscoPortfolioJobStuck"} <= alert_names
    assert len(dashboard["panels"]) >= 4
    expressions = [target["expr"] for panel in dashboard["panels"] for target in panel["targets"]]
    assert any("risco_jobs_total" in expression for expression in expressions)
