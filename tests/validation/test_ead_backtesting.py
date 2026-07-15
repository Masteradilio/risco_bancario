import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.exceptions import DomainValidationError
from src.validation.backtesting import (
    DEFAULT_EAD_BACKTEST_POLICY,
    EADBacktestDecision,
    EADBacktestObservation,
    backtest_ead,
    load_ead_backtest_policy,
    render_ead_backtest_report,
)


def evidence(
    *,
    amortized_count: int = 30,
    revolving_count: int = 100,
    predicted_ccf: str = "0.20",
    actual_ccf: str = "0.20",
) -> tuple[EADBacktestObservation, ...]:
    amortized = tuple(
        EADBacktestObservation(
            f"amortized-{index}",
            "amortized",
            "mortgage",
            Decimal("100"),
            Decimal("100"),
            "not_applicable",
        )
        for index in range(amortized_count)
    )
    revolving = tuple(
        EADBacktestObservation(
            f"revolving-{index}",
            "revolving",
            "credit_card",
            Decimal("60"),
            Decimal("60"),
            "medium",
            Decimal(predicted_ccf),
            Decimal(actual_ccf),
        )
        for index in range(revolving_count)
    )
    return (*amortized, *revolving)


def evaluate(**changes):
    values = {
        "model_id": "ead_amortized_and_revolving_ccf",
        "model_version": "synthetic-2026.07.1",
        "observations": evidence(),
    }
    values.update(changes)
    return backtest_ead(**values)


def test_balance_drawdown_and_ccf_reconcile_when_predictions_match() -> None:
    report = evaluate()
    assert report.decision == EADBacktestDecision.PASSED
    amortized, revolving = report.metrics[:2]
    assert amortized.observations == 30
    assert amortized.ead_mae == amortized.ead_rmse == 0
    assert revolving.observations == 100
    assert revolving.ccf_mae == revolving.ccf_rmse == 0
    assert revolving.mean_predicted_ccf == revolving.mean_actual_ccf == Decimal("0.20")


def test_revolving_is_segmented_by_product_and_utilization_band() -> None:
    report = evaluate()
    assert {item.dimension for item in report.metrics if item.component == "revolving"} == {
        "aggregate",
        "product",
        "utilization_band",
    }
    assert any(
        item.dimension == "utilization_band" and item.value == "medium" for item in report.metrics
    )


def test_ccf_error_or_small_sample_rejects() -> None:
    inaccurate = evaluate(observations=evidence(predicted_ccf="0.60", actual_ccf="0.10"))
    assert inaccurate.decision == EADBacktestDecision.REJECTED
    assert "revolving error" in inaccurate.decision_reasons[-1]
    small = evaluate(observations=evidence(revolving_count=4))
    assert small.decision == EADBacktestDecision.REJECTED
    assert "revolving sample" in small.decision_reasons[-1]


def test_segment_volume_creates_reservation_after_aggregate_passes() -> None:
    observations = evidence(revolving_count=100)
    split = tuple(
        EADBacktestObservation(
            item.observation_id,
            item.component,
            (
                "overdraft"
                if item.component == "revolving" and int(item.observation_id.rsplit("-", 1)[1]) < 5
                else item.product
            ),
            item.predicted_ead,
            item.actual_ead,
            item.utilization_band,
            item.predicted_ccf,
            item.actual_ccf,
        )
        for index, item in enumerate(observations)
    )
    assert evaluate(observations=split).decision == EADBacktestDecision.PASSED_WITH_RESERVATIONS


def test_report_and_evidence_hashes_are_order_independent() -> None:
    first = evaluate()
    second = evaluate(observations=tuple(reversed(evidence())))
    assert first.evidence_hash == second.evidence_hash
    assert first.report_hash == second.report_hash
    assert render_ead_backtest_report(first) == render_ead_backtest_report(second)
    assert "off_balance_without_realized_history" in render_ead_backtest_report(first)


@pytest.mark.parametrize(
    "change",
    [
        {"predicted_ead": Decimal("-1")},
        {"actual_ead": Decimal("-1")},
        {"component": "unknown"},
        {"predicted_ccf": Decimal("1.1")},
        {"actual_ccf": Decimal("-0.1")},
    ],
)
def test_observation_contract_fails_closed(change: dict) -> None:
    values = {
        "observation_id": "row-1",
        "component": "revolving",
        "product": "card",
        "predicted_ead": Decimal("60"),
        "actual_ead": Decimal("60"),
        "utilization_band": "medium",
        "predicted_ccf": Decimal("0.2"),
        "actual_ccf": Decimal("0.2"),
    }
    values.update(change)
    with pytest.raises(DomainValidationError):
        EADBacktestObservation(**values)


def test_component_specific_ccf_contract_is_enforced() -> None:
    with pytest.raises(DomainValidationError, match="require.*CCF"):
        EADBacktestObservation("row", "revolving", "card", Decimal("1"), Decimal("1"), "low")
    with pytest.raises(DomainValidationError, match="cannot carry CCF"):
        EADBacktestObservation(
            "row",
            "amortized",
            "loan",
            Decimal("1"),
            Decimal("1"),
            "not_applicable",
            Decimal("0"),
            Decimal("0"),
        )


def test_duplicate_or_missing_component_evidence_fails() -> None:
    rows = evidence()
    with pytest.raises(DomainValidationError, match="unique"):
        evaluate(observations=(*rows, rows[0]))
    with pytest.raises(DomainValidationError, match="amortized and revolving"):
        evaluate(observations=tuple(item for item in rows if item.component == "amortized"))


def test_policy_is_strict_versioned_and_hashed(tmp_path) -> None:
    policy = load_ead_backtest_policy()
    assert policy.version == "2026.07.1"
    assert len(policy.policy_hash) == 64
    payload = json.loads(DEFAULT_EAD_BACKTEST_POLICY.read_text(encoding="utf-8"))
    payload["minimum_revolving_observations"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="positive integers"):
        load_ead_backtest_policy(path)


def test_committed_synthetic_evidence_is_rejected_and_versioned() -> None:
    evidence = json.loads(
        Path("evidence/validation/ead/2026.07.1/report.json").read_text(encoding="utf-8")
    )
    assert evidence["decision"] == "rejected"
    assert len(evidence["metrics"]) == 9
    assert evidence["excluded_components"] == ["off_balance_without_realized_history"]
    assert evidence["report_hash"] == (
        "8d402a738f436b8643c2ce3dce46cffcd9f70276f92bc2112297ef82b6e953a5"
    )
