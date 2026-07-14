from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from src.data.synthetic import (
    PopulationConfig,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)
from src.domain.exceptions import DomainValidationError
from src.models.lgd import (
    LGDModelingDataset,
    build_lgd_modeling_dataset,
    build_lgd_workout_dataset,
    calculate_realized_lgd_dataset,
    fit_lgd_models,
    load_realized_lgd_policy,
)


@pytest.fixture(scope="module")
def modeling_bundle():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    macro = generate_macroeconomic_bundle(seed=91)
    workout = build_lgd_workout_dataset(population, events, observation_end_date=date(2025, 12, 1))
    realized = calculate_realized_lgd_dataset(
        workout, load_realized_lgd_policy(Path("config/lgd_policy/2026.07.1.json"))
    )
    dataset = build_lgd_modeling_dataset(workout, realized, population, history, macro)
    return workout, realized, dataset


def test_modeling_dataset_excludes_censored_and_uses_temporal_split(modeling_bundle) -> None:
    _, _, dataset = modeling_bundle

    assert len(dataset.rows) == 25
    assert dataset.censored_excluded == 7
    assert sum(item.split == "train" for item in dataset.rows) == 15
    assert sum(item.split == "validation" for item in dataset.rows) == 10
    assert max(item.default_date.year for item in dataset.rows if item.split == "train") < 2022
    assert (
        min(item.default_date.year for item in dataset.rows if item.split == "validation") >= 2022
    )


def test_features_cover_collateral_ltv_product_arrears_term_and_macro(modeling_bundle) -> None:
    _, _, dataset = modeling_bundle

    assert any(item.collateral_type != "none" for item in dataset.rows)
    assert any(item.collateral_type == "none" for item in dataset.rows)
    assert all(item.collateral_ltv > 0 for item in dataset.rows)
    assert len({item.product_code for item in dataset.rows}) >= 3
    assert any(item.days_past_due > 0 for item in dataset.rows)
    assert any(item.remaining_term_months > 0 for item in dataset.rows)
    assert len({item.gdp_growth for item in dataset.rows}) > 1
    assert len({item.unemployment for item in dataset.rows}) > 1


def test_targets_reconcile_to_complete_realized_lgd(modeling_bundle) -> None:
    workout, realized, dataset = modeling_bundle
    expected = {
        source.default_id: result.realized_lgd
        for source, result in zip(workout.records, realized, strict=True)
        if not source.is_censored
    }

    assert {item.default_id: item.target_lgd for item in dataset.rows} == expected
    assert sum(item.target_full_loss for item in dataset.rows) == 6
    assert sum(item.target_cure for item in dataset.rows) == 9


def test_compares_all_lgd_candidates_on_same_temporal_holdout(modeling_bundle) -> None:
    comparison = fit_lgd_models(modeling_bundle[2])
    candidates = (
        comparison.segmented_baseline,
        comparison.one_stage_regression,
        comparison.two_stage_cure_severity,
        comparison.one_inflated_regression,
    )

    assert {item.name for item in candidates} == {
        "segmented_mean",
        "ridge_one_stage",
        "cure_probability_and_severity",
        "one_inflated_ridge",
    }
    assert all(item.validation_metrics.sample_count == 10 for item in candidates)
    assert all(0 <= item.validation_metrics.mean_prediction <= 1 for item in candidates)
    assert all(item.approval_status == "demonstrative_not_approved" for item in candidates)
    assert comparison.selected_for_validation in {item.name for item in candidates}
    assert comparison.segment_estimates


def test_one_inflated_candidate_records_why_beta_only_is_not_appropriate(
    modeling_bundle,
) -> None:
    candidate = fit_lgd_models(modeling_bundle[2]).one_inflated_regression

    assert "one-inflation" in candidate.rationale
    assert "beta-only" in candidate.rationale
    assert len(candidate.secondary_models) == 1


def test_modeling_dataset_rejects_misaligned_realized_rows(modeling_bundle) -> None:
    workout, realized, _ = modeling_bundle
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    macro = generate_macroeconomic_bundle(seed=91)

    with pytest.raises(DomainValidationError, match="equal length"):
        build_lgd_modeling_dataset(workout, realized[:-1], population, history, macro)


def test_modeling_requires_train_and_validation(modeling_bundle) -> None:
    dataset = modeling_bundle[2]
    validation_only = LGDModelingDataset(
        tuple(replace(item, split="validation") for item in dataset.rows),
        dataset.version,
        dataset.validation_start_year,
        dataset.censored_excluded,
    )

    with pytest.raises(DomainValidationError, match="train and validation"):
        fit_lgd_models(validation_only)
