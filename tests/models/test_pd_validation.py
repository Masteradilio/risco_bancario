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
from src.models.pd import validate_frozen_pd


@pytest.fixture(scope="module")
def report():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    modeling = build_modeling_datasets(
        population, history, events, generate_macroeconomic_bundle(91)
    )
    return modeling, validate_frozen_pd(modeling)


def test_discrimination_metrics_include_auc_gini_ks_and_pr_auc(report) -> None:
    _, result = report
    assert result.discrimination.gini == pytest.approx(2 * result.discrimination.roc_auc - 1)
    assert 0 <= result.discrimination.ks <= 1
    assert 0 <= result.discrimination.pr_auc <= 1


def test_probabilistic_metrics_and_calibration_plot_are_reconciled(report) -> None:
    _, result = report
    assert 0 <= result.probabilistic.brier_score <= 1
    assert result.probabilistic.log_loss >= 0
    assert sum(item.row_count for item in result.calibration_bins) == result.sample_count
    expected_ece = (
        sum(item.row_count * item.absolute_error for item in result.calibration_bins)
        / result.sample_count
    )
    assert result.probabilistic.expected_calibration_error == pytest.approx(expected_ece)


def test_exact_binomial_tests_are_reported_by_rating(report) -> None:
    _, result = report
    assert result.binomial_rating_tests
    assert sum(item.row_count for item in result.binomial_rating_tests) == result.sample_count
    assert all(0 <= item.p_value <= 1 for item in result.binomial_rating_tests)


def test_observed_expected_and_bias_slices_cover_available_segments(report) -> None:
    _, result = report
    assert {item.dimension for item in result.segments} == {
        "rating",
        "product",
        "vintage",
    }
    assert all(math.isfinite(item.brier_score) for item in result.segments)
    assert result.bias_analysis_status == "segment_diagnostics_only_no_protected_attributes"


def test_stability_uses_unlabeled_backtesting_without_fabricating_performance(report) -> None:
    modeling, result = report
    assert result.stability.population_stability_index >= 0
    assert result.stability.reference_split == "calibration"
    assert result.stability.comparison_split == "backtesting"
    assert result.backtesting_status == "pending_target_maturation"
    assert all(
        item.target_default_12m is None for item in modeling.pd if item.split == "backtesting"
    )


def test_validation_scope_cannot_be_misread_as_model_approval(report) -> None:
    _, result = report
    assert result.evaluation_split == "oot"
    assert result.approval_status == "not_approved"
    assert result.evidence_scope == "synthetic_demonstrative_only"
