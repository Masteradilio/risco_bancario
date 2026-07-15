import json
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError
from src.validation.backtesting import (
    DEFAULT_ECL_BACKTEST_POLICY,
    ECLAttributionPath,
    ECLBacktestDecision,
    ECLBacktestObservation,
    backtest_ecl,
    load_ecl_backtest_policy,
    render_ecl_backtest_report,
)

COMPONENTS = ("volume", "stage", "pd", "lgd", "ead", "scenario", "overlay")


def path() -> ECLAttributionPath:
    values = ("11", "13", "12", "14", "15", "16", "17")
    return ECLAttributionPath(
        Decimal("10"),
        tuple(
            (component, Decimal(value)) for component, value in zip(COMPONENTS, values, strict=True)
        ),
    )


def evidence(
    count: int = 100, *, realized: str | None = "10", include_paths: bool = True
) -> tuple[ECLBacktestObservation, ...]:
    return tuple(
        ECLBacktestObservation(
            f"row-{index}",
            Decimal("10"),
            None if realized is None else Decimal(realized),
            "2022" if index % 2 else "2021",
            "downturn" if index % 2 else "normal",
            path() if include_paths else None,
        )
        for index in range(count)
    )


def evaluate(**changes):
    values = {
        "methodology_id": "probability_weighted_ecl",
        "methodology_version": "synthetic-2026.07.1",
        "observations": evidence(),
    }
    values.update(changes)
    return backtest_ecl(**values)


def test_initial_ecl_is_compared_with_realized_loss_by_vintage_and_cycle() -> None:
    report = evaluate()
    assert report.decision == ECLBacktestDecision.PASSED
    assert report.mature_observations == 100
    assert {item.dimension for item in report.outcome_metrics} == {
        "aggregate",
        "vintage",
        "economic_cycle",
    }
    assert report.outcome_metrics[0].bias == 0


def test_ordered_attribution_reconciles_all_required_components() -> None:
    report = evaluate()
    assert report.attribution_observations == 100
    first = [item for item in report.attributions if item.observation_id == "row-0"]
    assert [item.component for item in first] == list(COMPONENTS)
    assert sum((item.amount for item in first), Decimal("0")) == Decimal("7")


def test_missing_maturity_or_snapshots_rejects_without_fabrication() -> None:
    report = evaluate(observations=evidence(8, realized=None, include_paths=False))
    assert report.decision == ECLBacktestDecision.REJECTED
    assert report.mature_observations == 0
    assert report.outcome_metrics == ()
    assert report.attributions == ()
    rendered = render_ecl_backtest_report(report)
    assert "performance was not computed" in rendered
    assert "not replaced by fabricated losses" in rendered


def test_small_sample_or_material_bias_rejects() -> None:
    assert evaluate(observations=evidence(10)).decision == ECLBacktestDecision.REJECTED
    biased = evaluate(observations=evidence(realized="5"))
    assert biased.decision == ECLBacktestDecision.REJECTED
    assert "bias exceeds" in biased.decision_reasons[-1]


def test_report_and_evidence_hashes_are_order_independent() -> None:
    first = evaluate()
    second = evaluate(observations=tuple(reversed(evidence())))
    assert first.evidence_hash == second.evidence_hash
    assert first.report_hash == second.report_hash
    assert render_ecl_backtest_report(first) == render_ecl_backtest_report(second)


@pytest.mark.parametrize(
    "change",
    [
        {"initial_ecl": Decimal("-1")},
        {"realized_loss": Decimal("-1")},
        {"vintage": ""},
        {"economic_cycle": ""},
    ],
)
def test_observation_contract_fails_closed(change: dict) -> None:
    values = {
        "observation_id": "row",
        "initial_ecl": Decimal("10"),
        "realized_loss": Decimal("10"),
        "vintage": "2021",
        "economic_cycle": "normal",
        "attribution_path": path(),
    }
    values.update(change)
    with pytest.raises(DomainValidationError):
        ECLBacktestObservation(**values)


def test_attribution_opening_order_and_uniqueness_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="opening"):
        ECLBacktestObservation(
            "row",
            Decimal("10"),
            Decimal("10"),
            "2021",
            "normal",
            ECLAttributionPath(Decimal("9"), path().steps),
        )
    wrong = ECLAttributionPath(Decimal("10"), tuple(reversed(path().steps)))
    with pytest.raises(DomainValidationError, match="order"):
        evaluate(
            observations=(
                ECLBacktestObservation(
                    "row", Decimal("10"), Decimal("10"), "2021", "normal", wrong
                ),
            )
        )
    with pytest.raises(DomainValidationError, match="unique"):
        ECLAttributionPath(Decimal("10"), (("pd", Decimal("11")), ("pd", Decimal("12"))))


def test_duplicate_evidence_fails() -> None:
    rows = evidence()
    with pytest.raises(DomainValidationError, match="unique"):
        evaluate(observations=(*rows, rows[0]))


def test_policy_is_strict_versioned_and_hashed(tmp_path) -> None:
    policy = load_ecl_backtest_policy()
    assert policy.version == "2026.07.1"
    assert len(policy.policy_hash) == 64
    payload = json.loads(DEFAULT_ECL_BACKTEST_POLICY.read_text(encoding="utf-8"))
    payload["minimum_mature_observations"] = False
    target = tmp_path / "invalid.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="positive integer"):
        load_ecl_backtest_policy(target)
