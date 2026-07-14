from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from src.application.services import load_scenario_set
from src.domain.exceptions import DomainValidationError
from src.domain.scenarios import MacroTrajectoryPoint, MacroVariable, ScenarioKind
from src.ecl.calculation import (
    BaselineRiskPeriod,
    calculate_probability_weighted_scenario_ecl,
)
from src.models.forward_looking import load_macro_risk_policy


def _baseline(months: int = 3) -> tuple[BaselineRiskPeriod, ...]:
    return tuple(
        BaselineRiskPeriod(
            date(2026, month, 1),
            "0.10",
            "0.50",
            "100.00",
            "100.00",
            "0.50",
            "1.00",
        )
        for month in range(1, months + 1)
    )


def _neutral_scenario_set(months: int = 2):
    scenario_set = load_scenario_set(seed=91)
    values = (
        MacroVariable("gdp_growth", "2.20"),
        MacroVariable("inflation", "4.50"),
        MacroVariable("policy_rate", "9.00"),
        MacroVariable("unemployment", "7.50"),
        MacroVariable("household_debt", "49.00"),
        MacroVariable("risk_pressure", "0.00"),
    )
    trajectories = tuple(
        replace(
            trajectory,
            periods=tuple(
                MacroTrajectoryPoint(date(2026, month, 1), values) for month in range(1, months + 1)
            ),
        )
        for trajectory in scenario_set.trajectories
    )
    return replace(scenario_set, trajectories=trajectories)


def test_neutral_two_period_scenario_matches_manual_integral() -> None:
    result = calculate_probability_weighted_scenario_ecl(
        _baseline(2), _neutral_scenario_set(2), "portfolio", load_macro_risk_policy()
    )
    assert {item.ecl for item in result.scenario_results} == {Decimal("14.25")}
    assert result.probability_weighted_ecl == Decimal("14.25")
    first = result.scenario_results[0].periods
    assert first[0].expected_loss == Decimal("7.50")
    assert first[1].expected_loss == Decimal("6.75")


def test_real_trajectories_generate_distinct_pd_lgd_ead_and_ccf_curves() -> None:
    result = calculate_probability_weighted_scenario_ecl(
        _baseline(), load_scenario_set(seed=91), "revolving", load_macro_risk_policy()
    )
    first_periods = {item.scenario_id: item.periods[0] for item in result.scenario_results}
    for field in ("conditional_hazard", "lgd", "ead", "ccf"):
        assert len({getattr(period, field) for period in first_periods.values()}) == 4


def test_each_scenario_is_integrated_before_probability_weighting() -> None:
    result = calculate_probability_weighted_scenario_ecl(
        _baseline(), load_scenario_set(seed=91), "portfolio", load_macro_risk_policy()
    )
    probabilistic = [item for item in result.scenario_results if item.kind != ScenarioKind.STRESS]
    assert all(
        item.ecl == sum(period.expected_loss for period in item.periods) for item in probabilistic
    )
    assert result.probability_weighted_ecl == sum(
        (item.weighted_contribution for item in probabilistic), Decimal("0")
    ).quantize(Decimal("0.01"))
    assert len({item.ecl for item in probabilistic}) == 3


def test_stress_is_reported_but_excluded_from_weighted_ecl() -> None:
    result = calculate_probability_weighted_scenario_ecl(
        _baseline(), load_scenario_set(seed=91), "portfolio", load_macro_risk_policy()
    )
    stress = next(item for item in result.scenario_results if item.kind == ScenarioKind.STRESS)
    assert stress.weight == Decimal("0E-8")
    assert stress.weighted_contribution == Decimal("0E-8")
    assert result.stress_ecl == stress.ecl
    assert stress.ecl > result.probability_weighted_ecl


def test_marginal_pd_uses_declining_survival() -> None:
    result = calculate_probability_weighted_scenario_ecl(
        _baseline(3), _neutral_scenario_set(3), "portfolio", load_macro_risk_policy()
    )
    periods = result.scenario_results[0].periods
    assert [item.marginal_pd for item in periods] == [
        Decimal("0.10000000"),
        Decimal("0.09000000"),
        Decimal("0.08100000"),
    ]
    assert sum(item.marginal_pd for item in periods) <= Decimal("1")


def test_ccf_applies_only_to_undrawn_amount() -> None:
    low_ccf = BaselineRiskPeriod(date(2026, 1, 1), "0.10", "0.50", "100", "0", "0.10", "1")
    high_ccf = replace(low_ccf, ccf="0.90")
    low = calculate_probability_weighted_scenario_ecl(
        (low_ccf,), load_scenario_set(seed=91), "revolving", load_macro_risk_policy()
    )
    high = calculate_probability_weighted_scenario_ecl(
        (high_ccf,), load_scenario_set(seed=91), "revolving", load_macro_risk_policy()
    )
    assert [item.periods[0].ead for item in low.scenario_results] == [
        item.periods[0].ead for item in high.scenario_results
    ]


def test_empty_misaligned_and_overlong_baselines_are_rejected() -> None:
    scenario_set = load_scenario_set(seed=91)
    policy = load_macro_risk_policy()
    with pytest.raises(DomainValidationError, match="must not be empty"):
        calculate_probability_weighted_scenario_ecl((), scenario_set, "portfolio", policy)
    misaligned = replace(_baseline(1)[0], reference_date=date(2025, 12, 1))
    with pytest.raises(DomainValidationError, match="align"):
        calculate_probability_weighted_scenario_ecl(
            (misaligned,), scenario_set, "portfolio", policy
        )
    overlong = tuple(
        BaselineRiskPeriod(
            date(2026 + index // 12, index % 12 + 1, 1), "0", "0", "0", "0", "0", "1"
        )
        for index in range(61)
    )
    with pytest.raises(DomainValidationError, match="exceeds"):
        calculate_probability_weighted_scenario_ecl(overlong, scenario_set, "portfolio", policy)
