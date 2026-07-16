import numpy as np
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
from src.models.pd import fit_candidate_models
from src.models.pd.candidates import _balanced_weights, _fit_candidate


@pytest.fixture(scope="module")
def candidates():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    modeling = build_modeling_datasets(
        population, history, events, generate_macroeconomic_bundle(91)
    )
    return fit_candidate_models(modeling), modeling


def test_gradient_boosting_is_fitted_and_calibrated_on_reserved_split(candidates) -> None:
    comparison, modeling = candidates
    model = comparison.calibrated_gradient_boosting_12m
    assert model.calibration_method == "isotonic"
    assert model.calibrated_pipeline is not None
    assert model.oot_metrics_post_calibration is not None
    assert model.oot_metrics_post_calibration.event_count > 0
    calibration = [item for item in modeling.pd if item.split == "calibration"]
    from src.models.pd.baselines import _frame

    prediction = model.calibrated_pipeline.predict_proba(_frame(calibration))[:, 1]
    assert all(0 <= item <= 1 for item in prediction)


def test_survival_gradient_boosting_models_monthly_hazard(candidates) -> None:
    comparison, _ = candidates
    survival = comparison.survival_gradient_boosting_hazard
    assert survival.target == "target_hazard_1m"
    assert survival.calibrated_pipeline is None
    assert survival.validation_metrics_pre_calibration.event_count > 0


def test_transition_probabilities_sum_to_one_by_product_and_origin_rating(candidates) -> None:
    comparison, _ = candidates
    totals: dict[tuple[str, str], float] = {}
    for item in comparison.transition_probabilities:
        key = (item.product_code, item.from_rating)
        totals[key] = totals.get(key, 0.0) + item.probability
    assert totals
    assert all(abs(value - 1) < 1e-12 for value in totals.values())


def test_registry_preserves_provisional_champion_and_challengers(candidates) -> None:
    comparison, _ = candidates
    roles = {item.role for item in comparison.registry}
    assert "provisional_champion" in roles
    assert "challenger" in roles
    assert "small_segment_challenger" in roles
    assert all(item.approval_status != "approved" for item in comparison.registry)
    champion = next(item for item in comparison.registry if item.role == "provisional_champion")
    assert champion.approval_status == "oot_failed_not_approved"
    assert "no approved champion" in champion.rationale


def test_candidate_validation_metrics_are_finite(candidates) -> None:
    comparison, _ = candidates
    for model in (
        comparison.calibrated_gradient_boosting_12m,
        comparison.survival_gradient_boosting_hazard,
    ):
        metrics = model.validation_metrics_pre_calibration
        assert 0 <= metrics.roc_auc <= 1
        assert metrics.brier_score >= 0


def test_candidate_training_and_calibration_require_both_classes(candidates) -> None:
    _, modeling = candidates
    with pytest.raises(DomainValidationError, match="both target classes"):
        _balanced_weights(np.asarray([0, 0]))

    train = [row for row in modeling.pd if row.split == "train"]
    validation = [row for row in modeling.pd if row.split == "validation"]
    calibration = [
        row for row in modeling.pd if row.split == "calibration" and row.target_default_12m == 0
    ]
    oot = [row for row in modeling.pd if row.split == "oot"]
    with pytest.raises(DomainValidationError, match="calibration split requires"):
        _fit_candidate(
            train,
            validation,
            calibration,
            oot,
            target_name="target_default_12m",
            model_name="invalid",
            calibrate=True,
        )
