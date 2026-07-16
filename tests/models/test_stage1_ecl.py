from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from src.application.services import load_scenario_set
from src.domain.exceptions import DomainValidationError
from src.ecl.calculation import (
    Stage1ContractInput,
    Stage1RiskPeriod,
    calculate_stage1_ecl,
)
from src.ecl.discounting import effective_interest_discount_factor, present_value
from src.models.forward_looking import load_macro_risk_policy


def _periods(months: int = 12, lifetime_lgd: str = "0.40") -> tuple[Stage1RiskPeriod, ...]:
    return tuple(
        Stage1RiskPeriod(
            date(2026, month, 1),
            "0.01",
            lifetime_lgd,
            str(1000 - (month - 1) * 50),
            "200",
            "0.50",
        )
        for month in range(1, months + 1)
    )


def _contract(
    months: int = 12, eir: str = "0.12", lifetime_lgd: str = "0.40"
) -> Stage1ContractInput:
    return Stage1ContractInput(
        "CTR-STAGE1",
        date(2025, 12, 31),
        eir,
        _periods(months, lifetime_lgd),
        "portfolio",
    )


def test_original_eir_discount_factor_matches_manual_annual_point() -> None:
    assert effective_interest_discount_factor("0.12", 12) == Decimal("0.89285714")
    assert effective_interest_discount_factor("0", 7) == Decimal("1.00000000")
    assert present_value("112", effective_interest_discount_factor("0.12", 12)) == Decimal("100.00")


def test_stage1_restricts_default_events_to_next_twelve_months() -> None:
    periods = _periods() + (
        Stage1RiskPeriod(date(2027, 1, 1), "0.01", "0.40", "400", "200", "0.50"),
    )
    with pytest.raises(DomainValidationError, match="one to twelve"):
        replace(_contract(), periods=periods)


def test_stage1_calculates_every_period_and_scenario_for_contract() -> None:
    result = calculate_stage1_ecl(_contract(), load_scenario_set(seed=91), load_macro_risk_policy())
    assert result.contract_id == "CTR-STAGE1"
    assert result.horizon_months == 12
    assert result.measurement_basis == "defaults_possible_next_12m_with_lifetime_losses"
    assert len(result.scenario_ecl.scenario_results) == 4
    assert all(len(item.periods) == 12 for item in result.scenario_ecl.scenario_results)
    assert result.scenario_ecl.probability_weighted_ecl > 0


def test_short_remaining_term_uses_only_available_default_months() -> None:
    result = calculate_stage1_ecl(
        _contract(months=6), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    assert result.horizon_months == 6
    assert all(len(item.periods) == 6 for item in result.scenario_ecl.scenario_results)


def test_lifetime_lgd_drives_loss_associated_with_each_possible_default() -> None:
    low = calculate_stage1_ecl(
        _contract(lifetime_lgd="0.20"),
        load_scenario_set(seed=91),
        load_macro_risk_policy(),
    )
    high = calculate_stage1_ecl(
        _contract(lifetime_lgd="0.60"),
        load_scenario_set(seed=91),
        load_macro_risk_policy(),
    )
    assert high.scenario_ecl.probability_weighted_ecl > low.scenario_ecl.probability_weighted_ecl


def test_original_eir_discounting_reduces_stage1_ecl() -> None:
    undiscounted = calculate_stage1_ecl(
        _contract(eir="0"), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    discounted = calculate_stage1_ecl(
        _contract(eir="0.20"), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    assert (
        discounted.scenario_ecl.probability_weighted_ecl
        < undiscounted.scenario_ecl.probability_weighted_ecl
    )
    discounts = discounted.scenario_ecl.scenario_results[0].periods
    assert discounts[0].discount_factor > discounts[-1].discount_factor


def test_stage1_rejects_past_and_misaligned_periods() -> None:
    with pytest.raises(DomainValidationError, match="follow reporting date"):
        replace(
            _contract(months=1),
            periods=(Stage1RiskPeriod(date(2025, 12, 1), "0.01", "0.4", "100"),),
        )
    misaligned = replace(
        _contract(months=1), periods=(replace(_periods(1)[0], reference_date=date(2026, 2, 1)),)
    )
    with pytest.raises(DomainValidationError, match="align"):
        calculate_stage1_ecl(misaligned, load_scenario_set(seed=91), load_macro_risk_policy())


def test_stage1_rejects_periods_out_of_chronological_order() -> None:
    periods = _periods(2)
    with pytest.raises(DomainValidationError, match="chronologically ordered"):
        replace(_contract(months=2), periods=tuple(reversed(periods)))
