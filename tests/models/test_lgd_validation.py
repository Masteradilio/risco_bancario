import json
from dataclasses import replace
from datetime import date
from decimal import Decimal
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
    build_lgd_modeling_dataset,
    build_lgd_workout_dataset,
    calculate_realized_lgd_dataset,
    fit_lgd_models,
    load_lgd_validation_policy,
    load_realized_lgd_policy,
    validate_lgd_model,
)
from src.models.lgd.modeling import LGDCandidate
from src.models.lgd.validation import _predict, _segment_prediction

REALIZED_POLICY = Path("config/lgd_policy/2026.07.1.json")
VALIDATION_POLICY = Path("config/lgd_validation/2026.07.1.json")


@pytest.fixture(scope="module")
def validation_bundle():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    workout = build_lgd_workout_dataset(population, events, observation_end_date=date(2025, 12, 1))
    realized = calculate_realized_lgd_dataset(workout, load_realized_lgd_policy(REALIZED_POLICY))
    dataset = build_lgd_modeling_dataset(
        workout,
        realized,
        population,
        history,
        generate_macroeconomic_bundle(seed=91),
    )
    comparison = fit_lgd_models(dataset)
    policy = load_lgd_validation_policy(VALIDATION_POLICY)
    return dataset, comparison, policy, validate_lgd_model(dataset, comparison, policy)


def test_compares_selected_predictions_with_realized_lgd(validation_bundle) -> None:
    _, _, _, report = validation_bundle

    assert report.model_name == "ridge_one_stage"
    assert len(report.predictions) == 10
    assert all(0 <= item.predicted_lgd <= 1 for item in report.predictions)
    assert report.metrics.mean_actual == pytest.approx(0.568916737)
    assert report.metrics.root_mean_squared_error == pytest.approx(0.452034988)


def test_calibration_bands_reconcile_holdout_and_are_ordered(validation_bundle) -> None:
    _, _, _, report = validation_bundle

    assert sum(item.observations for item in report.calibration_bands) == 10
    assert [item.observations for item in report.calibration_bands] == [4, 3, 3]
    assert all(
        left.maximum_prediction <= right.minimum_prediction
        for left, right in zip(
            report.calibration_bands[:-1], report.calibration_bands[1:], strict=True
        )
    )


def test_backtests_every_validation_cohort(validation_bundle) -> None:
    _, _, _, report = validation_bundle

    assert sum(item.observations for item in report.cohort_backtests) == 10
    assert {item.cohort[:4] for item in report.cohort_backtests} == {"2022", "2023"}
    assert all(item.mean_absolute_error >= 0 for item in report.cohort_backtests)


def test_reports_product_stability_without_hiding_sparse_segments(validation_bundle) -> None:
    _, _, _, report = validation_bundle

    assert {item.product_code for item in report.product_stability} == {
        "acquired_distressed",
        "credit_card",
        "mortgage",
        "vehicle_finance",
    }
    assert all(item.status == "descriptive_only_sparse_sample" for item in report.product_stability)
    assert any(item.validation_observations == 0 for item in report.product_stability)


def test_keeps_downturn_sensitivity_separate_from_pit_ecl(validation_bundle) -> None:
    _, _, policy, report = validation_bundle
    analysis = report.downturn_analysis

    assert analysis.observations > 0
    assert analysis.downturn_addon >= 0
    assert analysis.usage == "sensitivity_only_not_used_in_ecl_pit"
    assert analysis.definition == policy.downturn_definition
    assert analysis.status == "descriptive_sensitivity_not_approved"


def test_fails_approval_against_predefined_validation_thresholds(validation_bundle) -> None:
    _, _, _, report = validation_bundle

    assert report.approval_status == "not_approved"
    assert {
        "validation_sample_below_minimum",
        "mae_above_limit",
        "rmse_above_limit",
        "cohort_sample_below_minimum",
        "product_sample_below_minimum",
        "downturn_sample_below_minimum",
        "no_independent_oot_after_selection",
        "validation_evidence_not_institutionally_validated",
    } <= set(report.blockers)


def test_policy_lineage_is_hashed_and_unknown_selection_fails(validation_bundle) -> None:
    dataset, comparison, policy, report = validation_bundle

    assert report.policy_version == "2026.07.1"
    assert report.policy_sha256 == policy.sha256
    broken = replace(comparison, selected_for_validation="unknown")
    with pytest.raises(DomainValidationError, match="not in the comparison"):
        validate_lgd_model(dataset, broken, policy)


def test_lgd_validation_policy_and_empty_dataset_fail_closed(
    validation_bundle, tmp_path: Path
) -> None:
    document = json.loads(VALIDATION_POLICY.read_text(encoding="utf-8"))
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document | {"schema_version": "2.0.0"}), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="policy schema"):
        load_lgd_validation_policy(path)
    document["calibration_bands"] = 1
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="thresholds"):
        load_lgd_validation_policy(path)

    dataset, comparison, policy, _ = validation_bundle
    empty_train = replace(
        dataset, rows=tuple(replace(row, split="validation") for row in dataset.rows)
    )
    with pytest.raises(DomainValidationError, match="requires train and validation"):
        validate_lgd_model(empty_train, comparison, policy)


def test_lgd_prediction_dispatch_covers_every_candidate_and_rejects_unknown(
    validation_bundle,
) -> None:
    dataset, comparison, _, _ = validation_bundle
    rows = [row for row in dataset.rows if row.split == "validation"]
    for candidate in (
        comparison.segmented_baseline,
        comparison.one_stage_regression,
        comparison.two_stage_cure_severity,
        comparison.one_inflated_regression,
    ):
        assert len(_predict(candidate, rows, comparison.segment_estimates)) == len(rows)
    with pytest.raises(DomainValidationError, match="has no estimates"):
        _segment_prediction(rows, ())
    unsupported = LGDCandidate(
        "unsupported",
        "none",
        comparison.one_stage_regression.validation_metrics,
        None,
        (),
        "not_approved",
        "test",
    )
    with pytest.raises(DomainValidationError, match="strategy is unsupported"):
        _predict(unsupported, rows, comparison.segment_estimates)


def test_lgd_validation_can_clear_every_governance_blocker(validation_bundle) -> None:
    dataset, comparison, policy, _ = validation_bundle
    lenient = replace(
        policy,
        minimum_validation_observations=0,
        maximum_mae=Decimal("999"),
        maximum_rmse=Decimal("999"),
        maximum_band_calibration_error=Decimal("999"),
        minimum_observations_per_cohort=0,
        minimum_observations_per_product=0,
        minimum_downturn_observations=0,
        require_independent_oot_after_selection=False,
        evidence_status="institutionally_validated",
    )
    report = validate_lgd_model(dataset, comparison, lenient)
    assert report.blockers == ()
    assert report.approval_status == "approved"
