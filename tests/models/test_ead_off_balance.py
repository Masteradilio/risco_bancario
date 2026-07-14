from collections import Counter
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

import pytest

from src.data.synthetic import PopulationConfig, generate_monthly_history, generate_population
from src.domain.exceptions import DomainValidationError
from src.models.ead import (
    build_off_balance_portfolio_projections,
    load_off_balance_ead_policy,
    project_off_balance_ead,
)

POLICY_PATH = Path("config/off_balance_ead_policy/2026.07.1.json")
QUANTUM = Decimal("0.00000001")


def test_projects_loan_commitment_utilization_probability_and_ead() -> None:
    policy = load_off_balance_ead_policy(POLICY_PATH)

    result = project_off_balance_ead(
        facility_type="commitment",
        horizon_months=12,
        original_limit=Decimal("100"),
        current_limit=Decimal("100"),
        current_drawn=Decimal("20"),
        risk_multiplier=Decimal("1"),
        policy=policy,
    )
    expected_monthly = Decimal("0.044")
    expected_probability = Decimal("1") - (Decimal("1") - expected_monthly) ** 12
    expected_incremental = Decimal("80") * expected_probability * Decimal("0.75")

    assert result.current_utilization == Decimal("0.20000000")
    assert result.monthly_utilization_probability == Decimal("0.04400000")
    assert result.cumulative_utilization_probability == expected_probability.quantize(
        QUANTUM, rounding=ROUND_HALF_EVEN
    )
    assert result.expected_incremental_utilization == expected_incremental.quantize(
        QUANTUM, rounding=ROUND_HALF_EVEN
    )
    assert result.projected_ead == (Decimal("20") + expected_incremental).quantize(
        QUANTUM, rounding=ROUND_HALF_EVEN
    )


def test_projects_financial_guarantee_call_separately() -> None:
    result = project_off_balance_ead(
        facility_type="financial_guarantee",
        horizon_months=12,
        original_limit=Decimal("200"),
        current_limit=Decimal("200"),
        current_drawn=Decimal("0"),
        risk_multiplier=Decimal("1"),
        policy=load_off_balance_ead_policy(POLICY_PATH),
    )
    expected_probability = Decimal("1") - Decimal("0.975") ** 12

    assert result.cumulative_utilization_probability == expected_probability.quantize(QUANTUM)
    assert result.conditional_utilized_share == Decimal("1.00000000")
    assert result.projected_ead == (Decimal("200") * expected_probability).quantize(QUANTUM)
    assert result.facility_type == "financial_guarantee"


def test_projection_increases_with_horizon_and_risk_multiplier() -> None:
    policy = load_off_balance_ead_policy(POLICY_PATH)

    low = project_off_balance_ead(
        facility_type="commitment",
        horizon_months=6,
        original_limit=Decimal("100"),
        current_limit=Decimal("100"),
        current_drawn=Decimal("0"),
        risk_multiplier=Decimal("0.75"),
        policy=policy,
    )
    base = project_off_balance_ead(
        facility_type="commitment",
        horizon_months=12,
        original_limit=Decimal("100"),
        current_limit=Decimal("100"),
        current_drawn=Decimal("0"),
        risk_multiplier=Decimal("1"),
        policy=policy,
    )
    high = project_off_balance_ead(
        facility_type="commitment",
        horizon_months=12,
        original_limit=Decimal("100"),
        current_limit=Decimal("100"),
        current_drawn=Decimal("0"),
        risk_multiplier=Decimal("1.5"),
        policy=policy,
    )

    assert low.projected_ead < base.projected_ead < high.projected_ead


def test_cancelled_limit_has_zero_incremental_ead() -> None:
    result = project_off_balance_ead(
        facility_type="commitment",
        horizon_months=12,
        original_limit=Decimal("100"),
        current_limit=Decimal("0"),
        current_drawn=Decimal("0"),
        risk_multiplier=Decimal("1"),
        policy=load_off_balance_ead_policy(POLICY_PATH),
    )

    assert result.limit_status == "cancelled"
    assert result.available_amount == 0
    assert result.expected_incremental_utilization == 0
    assert result.projected_ead == 0


def test_reduced_limit_uses_current_enforceable_amount() -> None:
    result = project_off_balance_ead(
        facility_type="commitment",
        horizon_months=12,
        original_limit=Decimal("100"),
        current_limit=Decimal("80"),
        current_drawn=Decimal("20"),
        risk_multiplier=Decimal("1"),
        policy=load_off_balance_ead_policy(POLICY_PATH),
    )

    assert result.limit_status == "reduced"
    assert result.available_amount == Decimal("60.00000000")
    assert result.projected_ead <= Decimal("80")


def test_portfolio_projects_commitments_and_guarantees_with_lineage() -> None:
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    policy = load_off_balance_ead_policy(POLICY_PATH)

    results = build_off_balance_portfolio_projections(population, history, policy)

    assert len(results) == 20
    assert Counter(item.product_code for item in results) == {
        "credit_commitment": 10,
        "financial_guarantee": 10,
    }
    assert {item.projection.status for item in results} == {"parameterized_not_estimated"}
    assert {item.projection.policy_sha256 for item in results} == {policy.sha256}


def test_invalid_facility_limit_and_risk_fail_closed() -> None:
    policy = load_off_balance_ead_policy(POLICY_PATH)
    common = {
        "horizon_months": 12,
        "original_limit": Decimal("100"),
        "current_limit": Decimal("100"),
        "current_drawn": Decimal("0"),
        "risk_multiplier": Decimal("1"),
        "policy": policy,
    }

    with pytest.raises(DomainValidationError, match="facility"):
        project_off_balance_ead(facility_type="unknown", **common)
    with pytest.raises(DomainValidationError, match="limit"):
        project_off_balance_ead(
            facility_type="commitment", **{**common, "current_limit": Decimal("120")}
        )
    with pytest.raises(DomainValidationError, match="bounds"):
        project_off_balance_ead(
            facility_type="commitment", **{**common, "risk_multiplier": Decimal("4")}
        )
