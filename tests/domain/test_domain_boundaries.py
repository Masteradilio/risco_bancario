"""Boundary and fail-closed tests for shared domain primitives."""

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.application.services import load_scenario_set
from src.domain.cashflows import CashFlow, CashFlowType
from src.domain.conventions import decimal_from, money, non_empty, rate
from src.domain.counterparties import Counterparty, PartyType
from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.domain.scenarios import (
    MacroTrajectoryPoint,
    MacroVariable,
    Scenario,
    ScenarioApprovalStatus,
    ScenarioKind,
    ScenarioTrajectory,
)
from src.domain.staging import RiskSnapshot, Stage
from src.ecl.calculation import ECLResult, ScenarioECL
from src.ecl.discounting import effective_interest_discount_factor

REFERENCE_DATE = date(2026, 1, 1)
CALCULATED_AT = datetime(2026, 1, 2, tzinfo=UTC)


@pytest.mark.parametrize("value", ["not-a-number", Decimal("NaN"), Decimal("Infinity")])
def test_decimal_conventions_reject_invalid_or_non_finite_values(value: object) -> None:
    with pytest.raises(DomainValidationError):
        decimal_from(value, field="value")  # type: ignore[arg-type]


def test_numeric_and_identifier_conventions_reject_out_of_range_values() -> None:
    with pytest.raises(DomainValidationError, match="non-negative"):
        money("-0.01", field="amount")
    with pytest.raises(DomainValidationError, match="between 0 and 1"):
        rate("1.01", field="rate")
    with pytest.raises(DomainValidationError, match="must not be empty"):
        non_empty("  ", field="identifier")


def test_cash_flow_rejects_foreign_currency_and_negative_payment() -> None:
    with pytest.raises(DomainValidationError, match="BRL"):
        CashFlow("CT-1", REFERENCE_DATE, "1", CashFlowType.FEE, "USD")
    with pytest.raises(DomainValidationError, match="non-negative"):
        CashFlow("CT-1", REFERENCE_DATE, "-1", CashFlowType.PRINCIPAL)


def test_counterparty_rejects_blank_optional_group() -> None:
    with pytest.raises(DomainValidationError, match="economic_group_id"):
        Counterparty("CP-1", PartyType.LEGAL_ENTITY, REFERENCE_DATE, " ")


def test_risk_snapshot_rejects_negative_age_observation_order_and_blank_rating() -> None:
    base = {
        "snapshot_id": "SN-1",
        "contract_id": "CT-1",
        "reference_date": REFERENCE_DATE,
        "observed_at": CALCULATED_AT,
        "stage": Stage.STAGE_1,
        "days_past_due": 0,
        "pd_12m": "0.01",
        "pd_lifetime": "0.02",
        "policy_version": "v1",
    }
    with pytest.raises(DomainValidationError, match="non-negative"):
        RiskSnapshot(**(base | {"days_past_due": -1}))  # type: ignore[arg-type]
    with pytest.raises(TemporalConsistencyError, match="cannot precede"):
        RiskSnapshot(**(base | {"reference_date": date(2026, 1, 3)}))  # type: ignore[arg-type]
    with pytest.raises(DomainValidationError, match="rating"):
        RiskSnapshot(**(base | {"rating": " "}))  # type: ignore[arg-type]


def test_scenario_and_trajectory_reject_invalid_horizon_calendar_and_schema() -> None:
    variable = MacroVariable("gdp", "1")
    with pytest.raises(DomainValidationError, match="greater than zero"):
        Scenario("S", "Scenario", ScenarioKind.BASE, REFERENCE_DATE, 0, "1", "v1")
    with pytest.raises(DomainValidationError, match="month starts"):
        MacroTrajectoryPoint(date(2026, 1, 2), (variable,))
    with pytest.raises(DomainValidationError, match="requires macro"):
        MacroTrajectoryPoint(REFERENCE_DATE, ())
    with pytest.raises(DomainValidationError, match="unique"):
        MacroTrajectoryPoint(REFERENCE_DATE, (variable, variable))
    with pytest.raises(DomainValidationError, match="requires periods"):
        ScenarioTrajectory("S", "Scenario", ScenarioKind.BASE, "1", ())

    december = MacroTrajectoryPoint(date(2026, 12, 1), (variable,))
    january = MacroTrajectoryPoint(date(2027, 1, 1), (variable,))
    valid = ScenarioTrajectory("S", "Scenario", ScenarioKind.BASE, "1", (december, january))
    assert len(valid.periods) == 2
    with pytest.raises(DomainValidationError, match="consecutive"):
        replace(valid, periods=(december, replace(january, reference_date=date(2027, 2, 1))))
    with pytest.raises(DomainValidationError, match="schema"):
        replace(
            valid,
            periods=(december, replace(january, variables=(MacroVariable("inflation", "1"),))),
        )


def test_scenario_set_governance_fails_closed_for_each_cross_field_invariant() -> None:
    scenario_set = load_scenario_set(seed=91)
    by_kind = {trajectory.kind: trajectory for trajectory in scenario_set.trajectories}
    base = by_kind[ScenarioKind.BASE]
    upside = by_kind[ScenarioKind.UPSIDE]
    downside = by_kind[ScenarioKind.DOWNSIDE]
    stress = by_kind[ScenarioKind.STRESS]
    with pytest.raises(DomainValidationError, match="lowercase SHA-256"):
        replace(scenario_set, source_snapshot_hash="A" * 64)
    with pytest.raises(DomainValidationError, match="requires trajectories"):
        replace(scenario_set, trajectories=())
    with pytest.raises(DomainValidationError, match="one base"):
        replace(
            scenario_set,
            trajectories=(replace(base, kind=ScenarioKind.UPSIDE), upside, downside, stress),
        )
    with pytest.raises(DomainValidationError, match="ids must be unique"):
        replace(
            scenario_set,
            trajectories=(base, replace(upside, scenario_id=base.scenario_id), downside, stress),
        )
    with pytest.raises(DomainValidationError, match="weights must sum"):
        replace(scenario_set, trajectories=(replace(base, weight="0.10"), upside, downside, stress))
    with pytest.raises(DomainValidationError, match="zero probability"):
        replace(scenario_set, trajectories=(base, upside, downside, replace(stress, weight="0.01")))
    shifted = replace(
        base,
        periods=tuple(
            replace(
                point,
                reference_date=date(point.reference_date.year + 1, point.reference_date.month, 1),
            )
            for point in base.periods
        ),
    )
    with pytest.raises(DomainValidationError, match="share reference date"):
        replace(scenario_set, trajectories=(shifted, upside, downside, stress))
    with pytest.raises(DomainValidationError, match="share reference date"):
        replace(
            scenario_set,
            trajectories=(replace(base, periods=base.periods[:-1]), upside, downside, stress),
        )
    with pytest.raises(DomainValidationError, match="requires approver"):
        replace(
            scenario_set,
            approval_status=ScenarioApprovalStatus.APPROVED,
            approved_by=None,
            approval_date=None,
        )
    with pytest.raises(DomainValidationError, match="cannot carry"):
        replace(scenario_set, approved_by="approver", approval_date=REFERENCE_DATE)
    approved = replace(
        scenario_set,
        approval_status=ScenarioApprovalStatus.APPROVED,
        approved_by="approver",
        approval_date=REFERENCE_DATE,
    )
    assert approved.approved_by == "approver"


def _valid_ecl_result(**overrides: object) -> ECLResult:
    values: dict[str, object] = {
        "result_id": "R-1",
        "contract_id": "CT-1",
        "reference_date": REFERENCE_DATE,
        "calculated_at": CALCULATED_AT,
        "stage": Stage.STAGE_1,
        "economic_ecl": "10",
        "management_overlay": "0",
        "regulatory_floor": "0",
        "reported_ecl": "10",
        "scenario_results": (ScenarioECL("base", "1", "10"),),
        "model_version": "v1",
        "configuration_version": "v1",
        "configuration_hash": "hash",
    }
    values.update(overrides)
    return ECLResult(**values)  # type: ignore[arg-type]


def test_ecl_result_rejects_currency_empty_and_duplicate_scenarios() -> None:
    with pytest.raises(DomainValidationError, match="BRL"):
        _valid_ecl_result(currency="USD")
    with pytest.raises(DomainValidationError, match="must not be empty"):
        _valid_ecl_result(scenario_results=())
    duplicate = (ScenarioECL("base", "0.5", "10"), ScenarioECL("base", "0.5", "10"))
    with pytest.raises(DomainValidationError, match="must be unique"):
        _valid_ecl_result(scenario_results=duplicate)


def test_discount_factor_rejects_non_positive_horizon() -> None:
    with pytest.raises(DomainValidationError, match="must be positive"):
        effective_interest_discount_factor("0.10", 0)
