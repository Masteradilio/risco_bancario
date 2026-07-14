from datetime import date
from decimal import Decimal

import pytest

from src.application.services import load_scenario_set
from src.domain.exceptions import DomainValidationError
from src.ecl.calculation import POCICashFlow, POCIScenarioCashFlows, measure_poci_scenarios

RECOGNITION = date(2026, 1, 1)
PAYMENT = date(2027, 1, 1)


def _cashflow(amount: str) -> tuple[POCICashFlow, ...]:
    return (POCICashFlow(PAYMENT, amount),)


def _scenarios(values: dict[str, str]) -> tuple[POCIScenarioCashFlows, ...]:
    return tuple(
        POCIScenarioCashFlows(scenario_id, _cashflow(values[scenario_id]))
        for scenario_id in ("upside", "base", "downside", "stress")
    )


def _measure(values: dict[str, str]):
    return measure_poci_scenarios(
        "CTR-POCI",
        RECOGNITION,
        "80",
        _cashflow("110"),
        _cashflow("88"),
        _scenarios(values),
        load_scenario_set(seed=91),
    )


def test_poci_uses_credit_adjusted_eir_for_all_scenarios() -> None:
    result = _measure({"upside": "99", "base": "88", "downside": "77", "stress": "66"})
    assert result.credit_adjusted_eir == Decimal("0.10000000")
    assert result.interest_presentation_basis == "credit_adjusted_eir_on_amortized_cost"
    assert {item.initial_lifetime_ecl for item in result.scenario_results} == {
        Decimal("20.00000000")
    }


def test_poci_recognizes_probability_weighted_lifetime_changes() -> None:
    result = _measure({"upside": "99", "base": "88", "downside": "77", "stress": "66"})
    current = {item.scenario_id: item.current_lifetime_ecl for item in result.scenario_results}
    assert current == {
        "upside": Decimal("10.00000000"),
        "base": Decimal("20.00000000"),
        "downside": Decimal("30.00000000"),
        "stress": Decimal("40.00000000"),
    }
    assert result.probability_weighted_lifetime_ecl == Decimal("20.00")
    assert result.probability_weighted_lifetime_change == Decimal("0.00")


def test_poci_scenario_disclosure_separates_gain_loss_and_stress() -> None:
    result = _measure({"upside": "99", "base": "88", "downside": "77", "stress": "66"})
    classifications = {
        item.scenario_id: item.change_classification for item in result.scenario_results
    }
    assert classifications == {
        "upside": "impairment_gain",
        "base": "no_change",
        "downside": "impairment_loss",
        "stress": "impairment_loss",
    }
    assert result.presentation == "no_change"
    assert result.stress_lifetime_ecl == Decimal("40.00000000")


def test_adverse_weighted_change_is_presented_as_impairment_loss() -> None:
    result = _measure(
        {scenario_id: "77" for scenario_id in ("upside", "base", "downside", "stress")}
    )
    assert result.probability_weighted_lifetime_ecl == Decimal("30.00")
    assert result.probability_weighted_lifetime_change == Decimal("10.00")
    assert result.presentation == "impairment_loss"


def test_favorable_weighted_change_is_presented_as_impairment_gain() -> None:
    result = _measure(
        {scenario_id: "99" for scenario_id in ("upside", "base", "downside", "stress")}
    )
    assert result.probability_weighted_lifetime_ecl == Decimal("10.00")
    assert result.probability_weighted_lifetime_change == Decimal("-10.00")
    assert result.presentation == "impairment_gain"


def test_poci_requires_complete_unique_scenario_cashflows() -> None:
    flows = _scenarios({"upside": "99", "base": "88", "downside": "77", "stress": "66"})
    with pytest.raises(DomainValidationError, match="each scenario"):
        measure_poci_scenarios(
            "CTR",
            RECOGNITION,
            "80",
            _cashflow("110"),
            _cashflow("88"),
            flows[:-1],
            load_scenario_set(seed=91),
        )
    with pytest.raises(DomainValidationError, match="each scenario"):
        measure_poci_scenarios(
            "CTR",
            RECOGNITION,
            "80",
            _cashflow("110"),
            _cashflow("88"),
            flows[:-1] + (flows[0],),
            load_scenario_set(seed=91),
        )


def test_poci_rejects_scenario_receipts_above_contract_and_carries_versions() -> None:
    values = {scenario_id: "88" for scenario_id in ("upside", "base", "downside", "stress")}
    values["base"] = "111"
    with pytest.raises(DomainValidationError, match="cannot exceed"):
        _measure(values)
    valid = _measure({scenario_id: "88" for scenario_id in values})
    assert valid.scenario_version == "2026.07.1"
    assert len(valid.scenario_source_hash) == 64
    assert valid.status == "synthetic_unapproved"
