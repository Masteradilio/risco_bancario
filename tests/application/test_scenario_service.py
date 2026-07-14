import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.application.services import ScenarioSnapshotCache, load_scenario_set
from src.domain.exceptions import DomainValidationError
from src.domain.scenarios import ScenarioApprovalStatus, ScenarioKind


def test_service_exposes_four_monthly_macro_trajectories() -> None:
    scenario_set = load_scenario_set(seed=91)
    assert scenario_set.reference_date == date(2026, 1, 1)
    assert {item.kind for item in scenario_set.trajectories} == set(ScenarioKind)
    assert {item.name for item in scenario_set.trajectories} == {
        "Otimista",
        "Base",
        "Pessimista",
        "Stress",
    }
    assert {len(item.periods) for item in scenario_set.trajectories} == {60}
    assert all(
        len(period.variables) == 6 for item in scenario_set.trajectories for period in item.periods
    )


def test_probability_weights_sum_to_one_and_stress_is_unweighted() -> None:
    scenario_set = load_scenario_set(seed=91)
    probability_weight = sum(
        (item.weight for item in scenario_set.trajectories if item.kind != ScenarioKind.STRESS),
        Decimal("0"),
    )
    stress = next(item for item in scenario_set.trajectories if item.kind == ScenarioKind.STRESS)
    assert probability_weight == Decimal("1.00000000")
    assert stress.weight == Decimal("0E-8")


def test_domain_rejects_invalid_probability_weights() -> None:
    scenario_set = load_scenario_set(seed=91)
    trajectories = list(scenario_set.trajectories)
    trajectories[0] = replace(trajectories[0], weight=Decimal("0.14"))
    with pytest.raises(DomainValidationError, match="weights must sum to one"):
        replace(scenario_set, trajectories=tuple(trajectories))


def test_service_versions_source_and_preserves_non_approval() -> None:
    scenario_set = load_scenario_set(seed=91)
    assert scenario_set.version == "2026.07.1"
    assert scenario_set.approval_status == ScenarioApprovalStatus.NOT_APPROVED
    assert scenario_set.approved_by is None
    assert scenario_set.approval_date is None
    assert len(scenario_set.source_snapshot_hash) == 64


def test_approved_scenario_set_requires_approval_metadata() -> None:
    scenario_set = load_scenario_set(seed=91)
    with pytest.raises(DomainValidationError, match="requires approver"):
        replace(scenario_set, approval_status=ScenarioApprovalStatus.APPROVED)


def test_snapshot_cache_is_content_addressed_and_reproducible(tmp_path) -> None:
    cache = ScenarioSnapshotCache(tmp_path)
    retrieved_at = datetime(2026, 7, 14, 12, tzinfo=UTC)
    payload = {"series": [{"period": "2026-01", "value": "4.50"}]}
    first = cache.store(
        provider="provider",
        source_version="v1",
        retrieved_at=retrieved_at,
        payload=payload,
    )
    second = cache.store(
        provider="provider",
        source_version="v1",
        retrieved_at=retrieved_at,
        payload=payload,
    )
    loaded = cache.load(first.path)
    assert first.path == second.path
    assert loaded.payload == payload
    assert loaded.payload_hash == first.payload_hash
    assert loaded.retrieved_at == retrieved_at


def test_snapshot_cache_rejects_tampered_payload(tmp_path) -> None:
    cache = ScenarioSnapshotCache(tmp_path)
    snapshot = cache.store(
        provider="provider",
        source_version="v1",
        retrieved_at=datetime(2026, 7, 14, 12, tzinfo=UTC),
        payload={"value": "1"},
    )
    document = json.loads(snapshot.path.read_text(encoding="utf-8"))
    document["payload"]["value"] = "2"
    snapshot.path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="hash mismatch"):
        cache.load(snapshot.path)
