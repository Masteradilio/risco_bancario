import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.exceptions import DomainValidationError
from src.validation.backtesting import (
    DEFAULT_LGD_BACKTEST_POLICY,
    LGDBacktestDecision,
    LGDBacktestObservation,
    backtest_lgd,
    load_lgd_backtest_policy,
    render_lgd_backtest_report,
)


def evidence(
    *,
    closed_count: int = 100,
    predicted: str = "0.40",
    actual: str = "0.40",
) -> tuple[LGDBacktestObservation, ...]:
    closed = tuple(
        LGDBacktestObservation(
            f"closed-{index}",
            "2022-Q1",
            "mortgage",
            Decimal("100"),
            Decimal(predicted),
            Decimal(actual),
            Decimal("60"),
            "closed",
            index % 2 == 0,
            Decimal("25") if index % 2 else Decimal("0"),
            index % 3 == 0,
        )
        for index in range(closed_count)
    )
    opened = (
        LGDBacktestObservation(
            "open-1",
            "2025-Q1",
            "credit_card",
            Decimal("80"),
            None,
            None,
            Decimal("10"),
            "open",
            False,
            Decimal("0"),
            False,
        ),
        LGDBacktestObservation(
            "open-2",
            "2025-Q1",
            "vehicle_finance",
            Decimal("120"),
            Decimal("0.50"),
            None,
            Decimal("30"),
            "open",
            True,
            Decimal("20"),
            True,
        ),
    )
    return (*closed, *opened)


def evaluate(**changes):
    values = {
        "model_id": "ridge_one_stage",
        "model_version": "synthetic-2026.07.1",
        "observations": evidence(),
    }
    values.update(changes)
    return backtest_lgd(**values)


def test_closed_workouts_reconcile_lgd_and_recoveries() -> None:
    report = evaluate()
    aggregate = report.closed_metrics[0]
    assert report.decision == LGDBacktestDecision.PASSED
    assert aggregate.observations == 100
    assert aggregate.mean_predicted_lgd == Decimal("0.40")
    assert aggregate.mean_actual_lgd == Decimal("0.40")
    assert aggregate.predicted_recovery == aggregate.realized_recovery == Decimal("6000.00")
    assert aggregate.passed


def test_closed_metrics_cover_cohort_cure_writeoff_and_collateral() -> None:
    report = evaluate()
    assert {item.dimension for item in report.closed_metrics} == {
        "aggregate",
        "cohort",
        "outcome",
        "collateral",
    }
    assert {item.value for item in report.closed_metrics if item.dimension == "outcome"} == {
        "cure",
        "writeoff",
    }
    assert {item.value for item in report.closed_metrics if item.dimension == "collateral"} == {
        "with_collateral",
        "without_collateral",
    }


def test_open_cohorts_are_inventoried_without_final_performance() -> None:
    cohort = evaluate().open_cohorts[0]
    assert cohort.observations == 2
    assert cohort.exposure_at_default == Decimal("200")
    assert cohort.recovery_to_date == Decimal("40")
    assert cohort.cures == cohort.writeoffs == cohort.collateralized == 1
    assert cohort.predictions_available == 1
    assert cohort.performance_status == "not_scored_until_workout_closure"


def test_small_sample_or_material_error_rejects() -> None:
    small = evaluate(observations=evidence(closed_count=10))
    assert small.decision == LGDBacktestDecision.REJECTED
    assert "sample below" in small.decision_reasons[0]
    inaccurate = evaluate(observations=evidence(predicted="0.80", actual="0.20"))
    assert inaccurate.decision == LGDBacktestDecision.REJECTED
    assert "MAE or RMSE" in inaccurate.decision_reasons[-1]


def test_report_and_evidence_hashes_are_order_independent() -> None:
    first = evaluate()
    second = evaluate(observations=tuple(reversed(evidence())))
    assert first.evidence_hash == second.evidence_hash
    assert first.report_hash == second.report_hash
    assert render_lgd_backtest_report(first) == render_lgd_backtest_report(second)
    assert "not institutional model approval" in render_lgd_backtest_report(first)


@pytest.mark.parametrize(
    "change",
    [
        {"exposure_at_default": Decimal("0")},
        {"predicted_lgd": Decimal("1.01")},
        {"actual_lgd": Decimal("-0.01")},
        {"writeoff_amount": Decimal("-1")},
        {"cohort_status": "unknown"},
    ],
)
def test_observation_contract_fails_closed(change: dict) -> None:
    values = {
        "default_id": "DEF-1",
        "cohort": "2022-Q1",
        "product": "loan",
        "exposure_at_default": Decimal("100"),
        "predicted_lgd": Decimal("0.5"),
        "actual_lgd": Decimal("0.4"),
        "discounted_net_recovery": Decimal("60"),
        "cohort_status": "closed",
        "cured": False,
        "writeoff_amount": Decimal("0"),
        "collateral_present": False,
    }
    values.update(change)
    with pytest.raises(DomainValidationError):
        LGDBacktestObservation(**values)


def test_open_cannot_carry_final_lgd_and_closed_requires_outcome() -> None:
    row = evidence()[0]
    with pytest.raises(DomainValidationError, match="open.*cannot carry"):
        LGDBacktestObservation(
            row.default_id,
            row.cohort,
            row.product,
            row.exposure_at_default,
            row.predicted_lgd,
            row.actual_lgd,
            row.discounted_net_recovery,
            "open",
            row.cured,
            row.writeoff_amount,
            row.collateral_present,
        )


def test_duplicate_evidence_or_missing_cohort_class_fails() -> None:
    rows = evidence()
    with pytest.raises(DomainValidationError, match="unique"):
        evaluate(observations=(*rows, rows[0]))
    with pytest.raises(DomainValidationError, match="both closed and open"):
        evaluate(observations=tuple(item for item in rows if item.cohort_status == "closed"))


def test_policy_is_strict_versioned_and_hashed(tmp_path) -> None:
    policy = load_lgd_backtest_policy()
    assert policy.version == "2026.07.1"
    assert len(policy.policy_hash) == 64
    payload = json.loads(DEFAULT_LGD_BACKTEST_POLICY.read_text(encoding="utf-8"))
    payload["minimum_closed_observations"] = False
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="positive integers"):
        load_lgd_backtest_policy(path)


def test_committed_synthetic_evidence_is_rejected_and_versioned() -> None:
    evidence = json.loads(
        Path("evidence/validation/lgd/2026.07.1/report.json").read_text(encoding="utf-8")
    )
    assert evidence["decision"] == "rejected"
    assert len(evidence["closed_metrics"]) == 12
    assert sum(item["observations"] for item in evidence["open_cohorts"]) == 7
    assert evidence["report_hash"] == (
        "3f2a7abcbeb33d5b455bdede10f372966fed1312ea532e39b49b30d16191cb30"
    )
