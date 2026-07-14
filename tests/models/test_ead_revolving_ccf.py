from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.data.synthetic import (
    PopulationConfig,
    generate_credit_events,
    generate_monthly_history,
    generate_population,
)
from src.domain.exceptions import DomainValidationError
from src.models.ead import (
    build_revolving_ccf_dataset,
    calculate_realized_ccf,
    fit_revolving_ccf_model,
    load_revolving_ccf_policy,
    predict_revolving_ccf,
)

POLICY_PATH = Path("config/ccf_policy/2026.07.1.json")


@pytest.fixture(scope="module")
def ccf_bundle():
    policy = load_revolving_ccf_policy(POLICY_PATH)
    population = generate_population(
        PopulationConfig(
            seed=policy.development_seed,
            clients=policy.development_clients,
            contracts_per_client=policy.development_contracts_per_client,
        )
    )
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    dataset = build_revolving_ccf_dataset(population, history, events, policy)
    return policy, dataset


def test_calculates_realized_ccf_from_available_limit() -> None:
    result = calculate_realized_ccf(
        observation_date=date(2025, 1, 1),
        default_date=date(2025, 7, 1),
        observed_balance=Decimal("40"),
        observed_limit=Decimal("100"),
        limit_at_default=Decimal("100"),
        ead_at_default=Decimal("70"),
        policy=load_revolving_ccf_policy(POLICY_PATH),
    )

    assert result.available_limit == Decimal("60")
    assert result.incremental_drawdown == Decimal("30")
    assert result.raw_ccf == Decimal("0.50000000")
    assert result.realized_ccf == Decimal("0.50000000")
    assert result.limit_status == "unchanged"


def test_identifies_reduced_and_cancelled_limits() -> None:
    policy = load_revolving_ccf_policy(POLICY_PATH)
    reduced = calculate_realized_ccf(
        observation_date=date(2025, 1, 1),
        default_date=date(2025, 7, 1),
        observed_balance=Decimal("40"),
        observed_limit=Decimal("100"),
        limit_at_default=Decimal("80"),
        ead_at_default=Decimal("70"),
        policy=policy,
    )
    cancelled = calculate_realized_ccf(
        observation_date=date(2025, 1, 1),
        default_date=date(2025, 7, 1),
        observed_balance=Decimal("0"),
        observed_limit=Decimal("100"),
        limit_at_default=Decimal("0"),
        ead_at_default=Decimal("0"),
        policy=policy,
    )

    assert reduced.limit_status == "reduced"
    assert cancelled.limit_status == "cancelled"
    assert cancelled.realized_ccf == Decimal("0E-8")


def test_preserves_raw_ccf_above_one_and_caps_modeling_target() -> None:
    result = calculate_realized_ccf(
        observation_date=date(2025, 1, 1),
        default_date=date(2025, 7, 1),
        observed_balance=Decimal("20"),
        observed_limit=Decimal("100"),
        limit_at_default=Decimal("150"),
        ead_at_default=Decimal("120"),
        policy=load_revolving_ccf_policy(POLICY_PATH),
    )

    assert result.raw_ccf == Decimal("1.25000000")
    assert result.realized_ccf == Decimal("1.00000000")
    assert result.bound_action == "capped_at_one"
    assert result.limit_status == "increased"


def test_zero_available_limit_is_undefined_and_excluded_from_modeling() -> None:
    result = calculate_realized_ccf(
        observation_date=date(2025, 1, 1),
        default_date=date(2025, 7, 1),
        observed_balance=Decimal("100"),
        observed_limit=Decimal("100"),
        limit_at_default=Decimal("100"),
        ead_at_default=Decimal("100"),
        policy=load_revolving_ccf_policy(POLICY_PATH),
    )

    assert result.ccf_defined is False
    assert result.raw_ccf is None
    assert result.realized_ccf is None
    assert result.bound_action == "undefined_zero_available_limit"


def test_development_dataset_has_products_utilization_and_horizons(ccf_bundle) -> None:
    policy, dataset = ccf_bundle

    assert dataset.defaults == 12
    assert len(dataset.rows) >= 20
    assert dataset.skipped_missing_horizon > 0
    assert {item.product_code for item in dataset.rows} == {"credit_card", "overdraft"}
    assert {item.horizon_months for item in dataset.rows} == set(policy.horizons_months)
    assert all(item.observation_date < item.default_date for item in dataset.rows)
    assert len({item.utilization for item in dataset.rows}) > 5
    assert {item.policy_sha256 for item in dataset.rows} == {policy.sha256}


def test_model_varies_by_product_utilization_and_horizon(ccf_bundle) -> None:
    _, dataset = ccf_bundle
    model = fit_revolving_ccf_model(dataset)
    validation = tuple(item for item in dataset.rows if item.split == "validation")
    prediction = predict_revolving_ccf(model, validation)
    feature_names = {item.feature for item in model.coefficients}

    assert model.training_metrics.observations >= 5
    assert model.status == "demonstrative_not_approved"
    assert max(prediction) > min(prediction)
    assert "numeric__utilization" in feature_names
    assert "numeric__horizon_months" in feature_names
    assert any("product_code" in item for item in feature_names)


def test_temporal_and_balance_contracts_fail_closed() -> None:
    policy = load_revolving_ccf_policy(POLICY_PATH)

    with pytest.raises(DomainValidationError, match="precede"):
        calculate_realized_ccf(
            observation_date=date(2025, 7, 1),
            default_date=date(2025, 7, 1),
            observed_balance=Decimal("40"),
            observed_limit=Decimal("100"),
            limit_at_default=Decimal("100"),
            ead_at_default=Decimal("70"),
            policy=policy,
        )
    with pytest.raises(DomainValidationError, match="exceeds"):
        calculate_realized_ccf(
            observation_date=date(2025, 1, 1),
            default_date=date(2025, 7, 1),
            observed_balance=Decimal("120"),
            observed_limit=Decimal("100"),
            limit_at_default=Decimal("100"),
            ead_at_default=Decimal("120"),
            policy=policy,
        )
