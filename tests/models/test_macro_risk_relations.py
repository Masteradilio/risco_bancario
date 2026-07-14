from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from src.application.services import load_scenario_set
from src.domain.exceptions import DomainValidationError
from src.domain.scenarios import MacroTrajectoryPoint, MacroVariable
from src.models.forward_looking import (
    build_macro_risk_paths,
    calculate_macro_risk_multipliers,
    load_macro_risk_policy,
)


def _point(**overrides: str) -> MacroTrajectoryPoint:
    values = {
        "gdp_growth": "2.20",
        "inflation": "4.50",
        "policy_rate": "9.00",
        "unemployment": "7.50",
        "household_debt": "49.00",
        "risk_pressure": "0.00",
    }
    values.update(overrides)
    return MacroTrajectoryPoint(
        date(2026, 1, 1), tuple(MacroVariable(name, value) for name, value in values.items())
    )


def test_policy_is_versioned_and_explicitly_not_estimated() -> None:
    policy = load_macro_risk_policy()
    assert policy.policy_version == "2026.07.1"
    assert policy.evidence_status == "demonstrative_not_estimated_not_approved"
    assert len(policy.sha256) == 64


def test_anchor_values_produce_unit_multipliers() -> None:
    policy = load_macro_risk_policy()
    result = calculate_macro_risk_multipliers("base", _point(), "portfolio", policy)
    assert (result.pd, result.lgd, result.ead, result.ccf) == (
        Decimal("1.00000000"),
        Decimal("1.00000000"),
        Decimal("1.00000000"),
        Decimal("1.00000000"),
    )


def test_paths_cover_every_period_component_and_scenario() -> None:
    scenario_set = load_scenario_set(seed=91)
    paths = build_macro_risk_paths(scenario_set, "portfolio", load_macro_risk_policy())
    assert len(paths) == 240
    assert {item.scenario_id for item in paths} == {"upside", "base", "downside", "stress"}
    assert all(item.pd > 0 and item.lgd > 0 and item.ead > 0 and item.ccf > 0 for item in paths)


def test_terminal_severity_orders_all_risk_components() -> None:
    scenario_set = load_scenario_set(seed=91)
    paths = build_macro_risk_paths(scenario_set, "portfolio", load_macro_risk_policy())
    terminal = {
        item.scenario_id: item for item in paths if item.reference_date == date(2030, 12, 1)
    }
    for component in ("pd", "lgd", "ead", "ccf"):
        assert getattr(terminal["upside"], component) < getattr(terminal["base"], component)
        assert getattr(terminal["base"], component) < getattr(terminal["downside"], component)
        assert getattr(terminal["downside"], component) < getattr(terminal["stress"], component)


def test_revolving_segment_has_stronger_ead_and_ccf_response() -> None:
    policy = load_macro_risk_policy()
    adverse = _point(unemployment="10.50", risk_pressure="3.00")
    portfolio = calculate_macro_risk_multipliers("downside", adverse, "portfolio", policy)
    revolving = calculate_macro_risk_multipliers("downside", adverse, "revolving", policy)
    assert revolving.ead > portfolio.ead
    assert revolving.ccf > portfolio.ccf


def test_quadratic_terms_create_non_linear_adverse_response() -> None:
    policy = load_macro_risk_policy()
    one_point = calculate_macro_risk_multipliers(
        "downside", _point(unemployment="8.50"), "portfolio", policy
    )
    two_points = calculate_macro_risk_multipliers(
        "stress", _point(unemployment="9.50"), "portfolio", policy
    )
    assert two_points.pd - Decimal("1") > (one_point.pd - Decimal("1")) * 2


def test_missing_variable_and_unknown_segment_are_rejected() -> None:
    policy = load_macro_risk_policy()
    point = _point()
    incomplete = replace(point, variables=point.variables[:-1])
    with pytest.raises(DomainValidationError, match="missing variables"):
        calculate_macro_risk_multipliers("base", incomplete, "portfolio", policy)
    with pytest.raises(DomainValidationError, match="unknown macro risk segment"):
        calculate_macro_risk_multipliers("base", point, "unknown", policy)
