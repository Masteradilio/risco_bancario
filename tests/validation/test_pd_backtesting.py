import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.exceptions import DomainValidationError
from src.validation.backtesting import (
    DEFAULT_PD_BACKTEST_POLICY,
    PDBacktestDecision,
    PDBacktestObservation,
    backtest_pd,
    load_pd_backtest_policy,
    render_pd_backtest_report,
)


def observations(
    split: str,
    *,
    prediction: str = "0.10",
    events: int = 4,
) -> tuple[PDBacktestObservation, ...]:
    result = []
    for horizon in (1, 12):
        for index in range(40):
            result.append(
                PDBacktestObservation(
                    f"{split}-{horizon}-{index}",
                    date(2022 if split == "calibration" else 2024, 1, 1),
                    horizon,
                    Decimal(prediction),
                    int(index < events),
                    "A2",
                    "personal_loan",
                    "2020",
                    split,
                )
            )
    return tuple(result)


def evaluate(**changes):
    values = {
        "model_id": "pd_baseline",
        "model_version": "2026.07.1",
        "reference": observations("calibration"),
        "evaluation": observations("oot"),
    }
    values.update(changes)
    return backtest_pd(**values)


def test_backtest_covers_horizon_rating_product_and_vintage() -> None:
    report = evaluate()
    assert report.decision == PDBacktestDecision.PASSED
    assert {item.horizon_months for item in report.metrics} == {1, 12}
    assert {item.dimension for item in report.metrics} == {
        "aggregate",
        "rating",
        "product",
        "vintage",
    }
    assert all(item.coverage_passed for item in report.metrics)


def test_metrics_reconcile_predicted_observed_coverage_and_intervals() -> None:
    metric = evaluate().metrics[0]
    assert metric.row_count == 40
    assert metric.event_count == 4
    assert metric.mean_prediction == Decimal("0.10")
    assert metric.observed_rate == Decimal("0.1")
    assert metric.observed_to_expected == Decimal("1")
    assert metric.confidence_lower <= metric.observed_rate <= metric.confidence_upper
    assert metric.prediction_inside_interval


def test_material_miscalibration_rejects_the_model() -> None:
    report = evaluate(evaluation=observations("oot", prediction="0.40"))
    assert report.decision == PDBacktestDecision.REJECTED
    assert "aggregate coverage failed" in report.decision_reasons[0]


def test_calibration_drift_is_measured_and_can_reject() -> None:
    report = evaluate(evaluation=observations("oot", prediction="0.14"))
    assert report.decision == PDBacktestDecision.REJECTED
    assert all(item.error_change == Decimal("0.04") for item in report.calibration_drift)
    assert "calibration drift exceeded" in report.decision_reasons[-1]


def test_unlabeled_future_population_is_reserved_not_scored() -> None:
    report = evaluate(unlabeled_future_observations=80)
    assert report.decision == PDBacktestDecision.PASSED_WITH_RESERVATIONS
    assert report.unlabeled_future_observations == 80
    assert "awaiting target maturation" in report.decision_reasons[-1]


def test_report_is_reproducible_independent_of_input_order() -> None:
    first = evaluate()
    second = evaluate(
        reference=tuple(reversed(observations("calibration"))),
        evaluation=tuple(reversed(observations("oot"))),
    )
    assert first.report_hash == second.report_hash
    assert first.evidence_hash == second.evidence_hash
    assert len(first.evidence_hash) == 64
    assert render_pd_backtest_report(first) == render_pd_backtest_report(second)
    assert "not institutional model approval" in render_pd_backtest_report(first)


@pytest.mark.parametrize(
    "change",
    [
        {"predicted_pd": Decimal("1.01")},
        {"observed_default": 2},
        {"horizon_months": 0},
    ],
)
def test_observations_fail_closed(change: dict) -> None:
    values = {
        "observation_id": "row-1",
        "observation_date": date(2024, 1, 1),
        "horizon_months": 12,
        "predicted_pd": Decimal("0.1"),
        "observed_default": 0,
        "rating": "A2",
        "product": "loan",
        "vintage": "2020",
        "split": "oot",
    }
    values.update(change)
    with pytest.raises(DomainValidationError):
        PDBacktestObservation(**values)


def test_missing_horizon_duplicate_or_same_split_is_rejected() -> None:
    only_one_horizon = tuple(item for item in observations("oot") if item.horizon_months == 12)
    with pytest.raises(DomainValidationError, match="horizon is absent"):
        evaluate(evaluation=only_one_horizon)
    with pytest.raises(DomainValidationError, match="duplicate"):
        evaluate(evaluation=(*observations("oot"), observations("oot")[0]))
    with pytest.raises(DomainValidationError, match="splits must differ"):
        evaluate(evaluation=observations("calibration"))


def test_policy_is_strict_versioned_and_hashed(tmp_path) -> None:
    policy = load_pd_backtest_policy()
    assert policy.version == "2026.07.1"
    assert len(policy.policy_hash) == 64
    payload = json.loads(DEFAULT_PD_BACKTEST_POLICY.read_text(encoding="utf-8"))
    payload["minimum_segment_observations"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="positive integers"):
        load_pd_backtest_policy(path)


def test_committed_synthetic_evidence_is_rejected_and_versioned() -> None:
    evidence = json.loads(
        Path("evidence/validation/pd/2026.07.1/report.json").read_text(encoding="utf-8")
    )
    assert evidence["decision"] == "rejected"
    assert evidence["unlabeled_future_observations"] == 182
    assert len(evidence["metrics"]) == 30
    assert evidence["report_hash"] == (
        "b3b3edcdead414bff3c08284bdd9d47fb4f0fd0c37768d492bb66098b01b9199"
    )
