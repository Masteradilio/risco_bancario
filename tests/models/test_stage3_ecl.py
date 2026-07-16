from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from src.application.services import load_scenario_set
from src.domain.exceptions import DomainValidationError
from src.ecl.stage3 import (
    Stage3CashFlowPeriod,
    Stage3ContractInput,
    Stage3ScenarioProjection,
    calculate_stage3_ecl,
)

SCENARIOS = ("upside", "base", "downside", "stress")


def _projections(
    receipts: dict[str, str] | None = None,
    *,
    collateral: str = "0",
    guarantee: str = "0",
    costs: str = "0",
    cure: bool = False,
) -> tuple[Stage3ScenarioProjection, ...]:
    values = receipts or {scenario_id: "60" for scenario_id in SCENARIOS}
    return tuple(
        Stage3ScenarioProjection(
            scenario_id,
            (
                Stage3CashFlowPeriod(
                    date(2026, 1, 1),
                    "100",
                    values[scenario_id],
                    collateral_recovery=collateral,
                    guarantee_recovery=guarantee,
                    collection_costs=costs,
                    cure_event=cure,
                ),
            ),
        )
        for scenario_id in SCENARIOS
    )


def _contract(
    projections: tuple[Stage3ScenarioProjection, ...], eir: str = "0"
) -> Stage3ContractInput:
    return Stage3ContractInput("CTR-STAGE3", date(2025, 12, 31), "1000", "200", eir, projections)


def test_cash_shortfall_matches_manual_receipts_recovery_and_costs() -> None:
    projections = _projections(collateral="20", costs="5")
    result = calculate_stage3_ecl(_contract(projections), load_scenario_set(seed=91))
    assert {item.ecl for item in result.scenario_results} == {Decimal("25.00")}
    period = result.scenario_results[0].periods[0]
    assert period.expected_cash_inflows == Decimal("80.00")
    assert period.cash_shortfall == Decimal("25.00")
    assert result.probability_weighted_ecl == Decimal("25.00")


def test_stage3_integrates_each_scenario_before_weighting() -> None:
    receipts = {"upside": "80", "base": "60", "downside": "40", "stress": "20"}
    result = calculate_stage3_ecl(_contract(_projections(receipts)), load_scenario_set(seed=91))
    ecls = {item.scenario_id: item.ecl for item in result.scenario_results}
    assert ecls == {
        "upside": Decimal("20.00"),
        "base": Decimal("40.00"),
        "downside": Decimal("60.00"),
        "stress": Decimal("80.00"),
    }
    assert result.probability_weighted_ecl == Decimal("40.00")
    assert result.stress_ecl == Decimal("80.00")


def test_guarantees_reduce_and_collection_costs_increase_shortfall() -> None:
    baseline = calculate_stage3_ecl(_contract(_projections()), load_scenario_set(seed=91))
    guaranteed = calculate_stage3_ecl(
        _contract(_projections(guarantee="15")), load_scenario_set(seed=91)
    )
    costly = calculate_stage3_ecl(_contract(_projections(costs="10")), load_scenario_set(seed=91))
    assert guaranteed.probability_weighted_ecl == baseline.probability_weighted_ecl - Decimal("15")
    assert costly.probability_weighted_ecl == baseline.probability_weighted_ecl + Decimal("10")


def test_original_eir_discounts_cash_shortfalls() -> None:
    zero = calculate_stage3_ecl(_contract(_projections()), load_scenario_set(seed=91))
    discounted = calculate_stage3_ecl(
        _contract(_projections(), eir="0.20"), load_scenario_set(seed=91)
    )
    assert discounted.probability_weighted_ecl < zero.probability_weighted_ecl
    assert discounted.scenario_results[0].periods[0].discount_factor < Decimal("1")


def test_cure_and_writeoff_are_explicit_without_double_counting() -> None:
    cure = calculate_stage3_ecl(_contract(_projections(cure=True)), load_scenario_set(seed=91))
    assert all(item.cured for item in cure.scenario_results)
    writeoff_projections = tuple(
        Stage3ScenarioProjection(
            scenario_id,
            (
                Stage3CashFlowPeriod(date(2026, 1, 1), "100", writeoff_amount="100"),
                Stage3CashFlowPeriod(date(2026, 2, 1), "0", post_writeoff_recovery="20"),
            ),
        )
        for scenario_id in SCENARIOS
    )
    written_off = calculate_stage3_ecl(_contract(writeoff_projections), load_scenario_set(seed=91))
    assert written_off.probability_weighted_ecl == Decimal("80.00")
    assert all(item.total_writeoff == Decimal("100.00") for item in written_off.scenario_results)


def test_stage3_interest_uses_net_carrying_amount() -> None:
    result = calculate_stage3_ecl(_contract(_projections(), eir="0.12"), load_scenario_set(seed=91))
    assert result.net_carrying_amount == Decimal("800.00")
    assert result.monthly_interest_revenue == Decimal("8.00")
    assert result.interest_basis == "net_carrying_amount_for_credit_impaired_asset"


def test_post_writeoff_recovery_and_multiple_cures_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="requires prior write-off"):
        Stage3ScenarioProjection(
            "base",
            (Stage3CashFlowPeriod(date(2026, 1, 1), "0", post_writeoff_recovery="1"),),
        )
    with pytest.raises(DomainValidationError, match="at most one cure"):
        Stage3ScenarioProjection(
            "base",
            (
                Stage3CashFlowPeriod(date(2026, 1, 1), "0", cure_event=True),
                Stage3CashFlowPeriod(date(2026, 2, 1), "0", cure_event=True),
            ),
        )


def test_stage3_requires_complete_aligned_scenario_projections() -> None:
    scenario_set = load_scenario_set(seed=91)
    with pytest.raises(DomainValidationError, match="each scenario"):
        calculate_stage3_ecl(_contract(_projections()[:-1]), scenario_set)
    misaligned = list(_projections())
    misaligned[-1] = replace(
        misaligned[-1],
        periods=(replace(misaligned[-1].periods[0], reference_date=date(2026, 2, 1)),),
    )
    with pytest.raises(DomainValidationError, match="share cash-flow dates"):
        calculate_stage3_ecl(_contract(tuple(misaligned)), scenario_set)
    with pytest.raises(DomainValidationError, match="cannot exceed"):
        replace(_contract(_projections()), opening_loss_allowance="1001")


def test_stage3_projection_and_contract_boundaries_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="requires periods"):
        Stage3ScenarioProjection("base", ())
    period = Stage3CashFlowPeriod(date(2026, 1, 1), "100")
    with pytest.raises(DomainValidationError, match="unique and ordered"):
        Stage3ScenarioProjection("base", (period, period))
    with pytest.raises(DomainValidationError, match="requires scenario projections"):
        _contract(())
    reporting_date = date(2026, 1, 1)
    invalid_reporting_date = replace(_contract(_projections()), reporting_date=reporting_date)
    with pytest.raises(DomainValidationError, match="must follow reporting date"):
        calculate_stage3_ecl(invalid_reporting_date, load_scenario_set(seed=91))
