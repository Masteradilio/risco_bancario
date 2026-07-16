from dataclasses import replace
from datetime import date

import pytest

from src.data.synthetic import (
    PopulationConfig,
    build_modeling_datasets,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)
from src.domain.exceptions import DomainValidationError
from src.models.pd import calibrate_explainable_pd
from src.models.pd.baselines import _pipeline
from src.models.pd.calibration import _calibrator, _target, summarize_temporal_splits


@pytest.fixture(scope="module")
def calibrated():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    modeling = build_modeling_datasets(
        population, history, events, generate_macroeconomic_bundle(91)
    )
    return modeling, calibrate_explainable_pd(modeling)


def test_temporal_splits_are_purged_and_future_backtest_is_unlabeled(calibrated) -> None:
    modeling, result = calibrated
    summaries = {item.split: item for item in result.split_summary}
    assert summaries["train"].end_date == date(2018, 12, 1)
    assert summaries["validation"].start_date == date(2020, 1, 1)
    assert summaries["calibration"].start_date == date(2022, 1, 1)
    assert summaries["oot"].start_date == date(2024, 1, 1)
    assert summaries["backtesting"].start_date == date(2025, 1, 1)
    assert result.embargo_months == 12
    assert not summaries["backtesting"].targets_complete
    assert all(
        row.target_default_12m is None and row.target_hazard_1m is None
        for row in modeling.pd
        if row.split == "backtesting"
    )


def test_calibration_method_is_selected_without_oot(calibrated) -> None:
    _, result = calibrated
    assert {item.method for item in result.method_comparison} == {"sigmoid", "isotonic"}
    best = min(
        result.method_comparison,
        key=lambda item: (
            item.validation_holdout_metrics.brier_score,
            item.validation_holdout_metrics.calibration_in_the_large_error,
            item.method,
        ),
    )
    assert result.selected_method == best.method


def test_final_calibrator_has_single_oot_evaluation(calibrated) -> None:
    _, result = calibrated
    assert result.oot_metrics.sample_count > 0
    assert result.oot_metrics.event_count > 0
    assert result.approval_status == "synthetic_validation_not_approved"


def test_oot_calibration_is_sliced_by_rating_product_and_vintage(calibrated) -> None:
    _, result = calibrated
    assert {item.dimension for item in result.oot_slices} == {
        "rating",
        "product",
        "vintage",
    }
    assert all(0 <= item.brier_score <= 1 for item in result.oot_slices)
    assert all(item.row_count > 0 for item in result.oot_slices)


def test_origination_cohort_is_metadata_not_a_model_feature(calibrated) -> None:
    modeling, _ = calibrated
    assert all(item.origination_cohort for item in modeling.pd)


def test_calibration_rejects_empty_overlapping_immature_and_single_class_splits(
    calibrated,
) -> None:
    modeling, _ = calibrated
    without_train = replace(modeling, pd=tuple(row for row in modeling.pd if row.split != "train"))
    with pytest.raises(DomainValidationError, match="temporal split is empty"):
        summarize_temporal_splits(without_train)

    rows = list(modeling.pd)
    validation_index = next(index for index, row in enumerate(rows) if row.split == "validation")
    rows[validation_index] = replace(rows[validation_index], observation_date=date(2018, 1, 1))
    with pytest.raises(DomainValidationError, match="strictly ordered"):
        summarize_temporal_splits(replace(modeling, pd=tuple(rows)))

    immature = [row for row in modeling.pd if row.split == "backtesting"]
    with pytest.raises(DomainValidationError, match="mature"):
        _target(immature)
    single_class = [
        row for row in modeling.pd if row.split == "calibration" and row.target_default_12m == 0
    ]
    with pytest.raises(DomainValidationError, match="both target classes"):
        _calibrator(_pipeline(), single_class, "isotonic")
