from dataclasses import replace
from datetime import date

import pytest

from src.application.services import load_scenario_set
from src.domain.exceptions import DomainValidationError
from src.ecl.calculation import (
    Stage2CalculationMode,
    Stage2ContractInput,
    Stage2RiskPeriod,
    calculate_stage2_ecl,
)
from src.models.forward_looking import load_macro_risk_policy


def _month(month: int) -> date:
    return date(2026 + (month - 1) // 12, (month - 1) % 12 + 1, 1)


def _periods(months: int, prepayment: str = "0") -> tuple[Stage2RiskPeriod, ...]:
    return tuple(
        Stage2RiskPeriod(
            _month(month),
            "0.008",
            "0.45",
            str(max(200, 1500 - (month - 1) * 50)),
            "300",
            "0.50",
            prepayment,
        )
        for month in range(1, months + 1)
    )


def _contract(
    *,
    contractual: int = 18,
    extension: int = 0,
    extension_probability: str = "0",
    prepayment: str = "0",
    eir: str = "0.12",
    mode: Stage2CalculationMode = Stage2CalculationMode.INDIVIDUAL,
    group: str | None = None,
) -> Stage2ContractInput:
    return Stage2ContractInput(
        "CTR-STAGE2",
        date(2025, 12, 31),
        eir,
        contractual,
        extension,
        extension_probability,
        _periods(contractual + extension, prepayment),
        mode,
        group,
        "portfolio",
    )


def test_stage2_uses_every_month_of_remaining_lifetime() -> None:
    result = calculate_stage2_ecl(
        _contract(contractual=18), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    assert result.contractual_months == 18
    assert result.behavioral_horizon_months == 18
    assert result.measurement_basis == "lifetime_ecl_behavioral_term"
    assert all(len(item.periods) == 18 for item in result.scenario_ecl.scenario_results)


def test_expected_prepayment_reduces_lifetime_ecl() -> None:
    no_prepayment = calculate_stage2_ecl(
        _contract(prepayment="0"), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    with_prepayment = calculate_stage2_ecl(
        _contract(prepayment="0.03"), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    assert (
        with_prepayment.scenario_ecl.probability_weighted_ecl
        < no_prepayment.scenario_ecl.probability_weighted_ecl
    )


def test_expected_extension_adds_probability_weighted_behavioral_term() -> None:
    contractual = calculate_stage2_ecl(
        _contract(contractual=12), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    extended = calculate_stage2_ecl(
        _contract(contractual=12, extension=6, extension_probability="0.50"),
        load_scenario_set(seed=91),
        load_macro_risk_policy(),
    )
    assert extended.behavioral_horizon_months == 18
    assert (
        extended.scenario_ecl.probability_weighted_ecl
        > contractual.scenario_ecl.probability_weighted_ecl
    )


def test_individual_and_collective_modes_preserve_calculation_and_metadata() -> None:
    individual = calculate_stage2_ecl(
        _contract(), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    collective = calculate_stage2_ecl(
        _contract(mode=Stage2CalculationMode.COLLECTIVE, group="POOL-MORTGAGE"),
        load_scenario_set(seed=91),
        load_macro_risk_policy(),
    )
    assert individual.calculation_mode == Stage2CalculationMode.INDIVIDUAL
    assert collective.calculation_mode == Stage2CalculationMode.COLLECTIVE
    assert collective.homogeneous_group_id == "POOL-MORTGAGE"
    assert (
        individual.scenario_ecl.probability_weighted_ecl
        == collective.scenario_ecl.probability_weighted_ecl
    )


def test_original_eir_discounting_reduces_lifetime_ecl() -> None:
    zero = calculate_stage2_ecl(
        _contract(eir="0"), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    discounted = calculate_stage2_ecl(
        _contract(eir="0.20"), load_scenario_set(seed=91), load_macro_risk_policy()
    )
    assert (
        discounted.scenario_ecl.probability_weighted_ecl
        < zero.scenario_ecl.probability_weighted_ecl
    )


def test_stage2_rejects_inconsistent_term_and_mode() -> None:
    with pytest.raises(DomainValidationError, match="cover contractual"):
        replace(_contract(), contractual_months=17)
    with pytest.raises(DomainValidationError, match="requires extension months"):
        _contract(extension_probability="0.50")
    with pytest.raises(DomainValidationError, match="requires homogeneous"):
        _contract(mode=Stage2CalculationMode.COLLECTIVE)
    with pytest.raises(DomainValidationError, match="cannot use"):
        _contract(group="POOL")


def test_stage2_rejects_periods_outside_scenario_horizon() -> None:
    contract = _contract(contractual=60, extension=1, extension_probability="0.5")
    with pytest.raises(DomainValidationError, match="exceeds scenario horizon"):
        calculate_stage2_ecl(contract, load_scenario_set(seed=91), load_macro_risk_policy())
