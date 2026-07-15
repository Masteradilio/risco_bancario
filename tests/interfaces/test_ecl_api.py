from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.infrastructure.database import DatabaseSettings
from src.infrastructure.database.repository import canonical_json
from src.interfaces.api.app import create_app
from src.interfaces.api.schemas import PortfolioRequest
from src.security.rbac import Role
from src.security.settings import SecuritySettings


def calculation_payload(*, execution_key: str = "portfolio:2026-06-30") -> dict[str, Any]:
    variables = {
        "gdp_growth": "2.20",
        "inflation": "4.50",
        "policy_rate": "9.00",
        "unemployment": "7.50",
        "household_debt": "49.00",
        "risk_pressure": "0.00",
    }
    scenarios = [
        {"scenario_id": "base", "name": "Base", "kind": "base", "weight": "0.50"},
        {"scenario_id": "upside", "name": "Up", "kind": "upside", "weight": "0.20"},
        {
            "scenario_id": "downside",
            "name": "Down",
            "kind": "downside",
            "weight": "0.30",
        },
        {"scenario_id": "stress", "name": "Stress", "kind": "stress", "weight": "0"},
    ]
    for scenario in scenarios:
        scenario["periods"] = [{"reference_date": "2026-07-01", "variables": variables}]
    return {
        "execution_key": execution_key,
        "contract_id": "C-API-1",
        "source_version": "synthetic-2026.1",
        "reference_date": "2026-06-30",
        "stage": 1,
        "stage_assessment": {
            "origination_stage": 1,
            "current_stage": 1,
            "origination_rating": "A",
            "current_rating": "B",
            "origination_lifetime_pd": "0.05",
            "current_lifetime_pd": "0.10",
            "reason_codes": ["RATING_DOWNGRADE"],
        },
        "segment": "portfolio",
        "periods": [
            {
                "reference_date": "2026-07-01",
                "conditional_hazard": "0.10",
                "lgd": "0.40",
                "drawn_ead": "100.00",
                "undrawn_amount": "0",
                "ccf": "0",
                "discount_factor": "1",
            }
        ],
        "scenario_version": "2026.1",
        "scenario_source_hash": "a" * 64,
        "scenarios": scenarios,
        "model_versions": {"pd": "1.0.0", "lgd": "1.0.0", "ead": "1.0.0"},
        "configuration_version": "2026.07.1",
        "configuration_hash": "b" * 64,
        "code_commit": "abcdef1",
    }


def client(tmp_path: Path) -> TestClient:
    app = create_app(
        DatabaseSettings(backend="sqlite", sqlite_path=tmp_path / "api.sqlite3"),
        SecuritySettings(jwt_secret="test-secret-that-is-at-least-32-bytes-long"),
    )
    auth = app.state.auth_service
    auth.create_user("manager", "Strong!Pass123", Role.MANAGER)
    token = auth.issue_token("manager", "Strong!Pass123")
    api = TestClient(app)
    api.headers.update({"Authorization": f"Bearer {token}"})
    return api


def test_openapi_exposes_versioned_ecl_product_routes(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        paths = api.get("/openapi.json").json()["paths"]

    assert "/api/v1/ecl/individual" in paths
    assert "/api/v1/ecl/portfolio" in paths
    assert "/api/v1/ecl/jobs/{job_id}" in paths
    assert "/api/v1/ecl/executions/{execution_id}" in paths


def test_individual_returns_period_and_scenario_decomposition(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        response = api.post("/api/v1/ecl/individual", json=calculation_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["probability_weighted_ecl"] == "4.00"
    assert body["stress_ecl"] == "4.00"
    assert len(body["scenarios"]) == 4
    assert body["scenarios"][0]["periods"][0]["expected_loss"] == "4.00"
    assert len(body["lineage_hash"]) == 64


def test_individual_retry_is_idempotent(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        first = api.post("/api/v1/ecl/individual", json=calculation_payload())
        second = api.post("/api/v1/ecl/individual", json=calculation_payload())

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["execution_id"] == first.json()["execution_id"]
    assert second.json()["reused"] is True


def test_execution_evidence_exposes_lineage_and_result_hashes(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        calculated = api.post("/api/v1/ecl/individual", json=calculation_payload()).json()
        response = api.get(f"/api/v1/ecl/executions/{calculated['execution_id']}")

    assert response.status_code == 200
    evidence = response.json()
    assert evidence["lineage"]["code_commit"] == "abcdef1"
    assert evidence["lineage"]["configuration_hash"] == "b" * 64
    assert len(evidence["results"]) == 4
    assert all(len(item["payload_hash"]) == 64 for item in evidence["results"])
    assert evidence["results"][0]["payload"]["stage_assessment"]["reason_codes"] == [
        "RATING_DOWNGRADE"
    ]
    assert evidence["results"][0]["payload"]["adjustments"]["status"] == "NOT_APPLIED"


def test_limitations_are_versioned_and_audited(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        response = api.get("/api/v1/validation/limitations")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "LIMITED"
    assert body["source_path"] == "docs/validation/LIMITATION_REGISTER.md"
    assert len(body["source_hash"]) == 64
    assert "Status dos Componentes" in body["content"]


def test_portfolio_job_is_persisted_and_processed(tmp_path: Path) -> None:
    payload = calculation_payload(execution_key="batch:2026-06-30")
    with client(tmp_path) as api:
        portfolio = {"calculations": [payload]}
        canonical_portfolio = PortfolioRequest.model_validate(portfolio).model_dump(mode="json")
        request_hash = hashlib.sha256(canonical_json(canonical_portfolio).encode()).hexdigest()
        confirmation = api.post(
            "/api/v1/security/confirmations",
            json={"action": "ecl:calculate:portfolio", "payload_hash": request_hash},
        ).json()
        accepted = api.post(
            "/api/v1/ecl/portfolio",
            json=portfolio,
            headers={"X-Confirmation-Id": confirmation["confirmation_id"]},
        )
        status_response = api.get(accepted.json()["status_url"])

    assert accepted.status_code == 202
    assert len(accepted.json()["job_id"]) == 36
    status_body = status_response.json()
    assert status_body["status"] == "SUCCEEDED"
    assert len(status_body["request_hash"]) == 64
    assert status_body["result"][0]["probability_weighted_ecl"] == "4.00"


def test_unknown_fields_and_invalid_stage_one_horizon_are_rejected(tmp_path: Path) -> None:
    payload = calculation_payload()
    payload["unknown"] = "silent-default-not-allowed"
    with client(tmp_path) as api:
        extra_response = api.post("/api/v1/ecl/individual", json=payload)
        payload = calculation_payload()
        payload["periods"] = payload["periods"] * 13
        horizon_response = api.post("/api/v1/ecl/individual", json=payload)

    assert extra_response.status_code == 422
    assert horizon_response.status_code == 422


def test_unknown_job_and_execution_return_not_found(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        job_response = api.get("/api/v1/ecl/jobs/missing")
        execution_response = api.get("/api/v1/ecl/executions/missing")

    assert job_response.status_code == 404
    assert execution_response.status_code == 404
