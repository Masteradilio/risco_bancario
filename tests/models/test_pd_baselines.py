import math

import pytest

from src.data.synthetic import (
    PopulationConfig,
    build_modeling_datasets,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)
from src.models.pd import fit_explainable_baselines


@pytest.fixture(scope="module")
def comparison():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    modeling = build_modeling_datasets(
        population, history, events, generate_macroeconomic_bundle(91)
    )
    return fit_explainable_baselines(modeling)


def test_logistic_and_discrete_hazard_baselines_fit_separate_targets(comparison) -> None:
    assert comparison.logistic_12m.target == "target_default_12m"
    assert comparison.discrete_hazard_1m.target == "target_hazard_1m"
    assert comparison.logistic_12m.train_count == comparison.discrete_hazard_1m.train_count


def test_validation_metrics_cover_discrimination_and_calibration(comparison) -> None:
    for model in (comparison.logistic_12m, comparison.discrete_hazard_1m):
        metrics = model.validation_metrics
        assert metrics.sample_count > metrics.event_count > 0
        assert all(
            math.isfinite(value)
            for value in (
                metrics.brier_score,
                metrics.log_loss,
                metrics.roc_auc,
                metrics.average_precision,
                metrics.calibration_in_the_large_error,
            )
        )
        assert 0 <= metrics.roc_auc <= 1


def test_coefficient_table_is_explainable_and_excludes_targets(comparison) -> None:
    coefficients = comparison.logistic_12m.coefficients
    assert coefficients
    assert any("days_past_due" in item.feature for item in coefficients)
    assert all(
        "target" not in item.feature and "future" not in item.feature for item in coefficients
    )


def test_rating_bands_are_derived_from_calibration_pd_distribution(comparison) -> None:
    bands = comparison.rating_bands
    assert [item.grade for item in bands] == ["R1", "R2", "R3", "R4", "R5"]
    assert sum(item.count for item in bands) == comparison.logistic_12m.calibration_count
    assert all(
        left.maximum_pd <= right.minimum_pd
        for left, right in zip(bands[:-1], bands[1:], strict=True)
    )
    assert all(0 <= item.observed_default_rate <= 1 for item in bands)


def test_training_is_deterministic(comparison) -> None:
    first = [item.coefficient for item in comparison.logistic_12m.coefficients]
    second = [
        item.coefficient
        for item in fit_explainable_baselines(_modeling_bundle()).logistic_12m.coefficients
    ]
    assert first == second


def _modeling_bundle():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    return build_modeling_datasets(population, history, events, generate_macroeconomic_bundle(91))
