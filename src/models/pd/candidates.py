"""PD challenger models, calibration object and small-segment transitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.calibration import CalibratedClassifierCV  # type: ignore[import-untyped]
from sklearn.compose import ColumnTransformer  # type: ignore[import-untyped]
from sklearn.ensemble import HistGradientBoostingClassifier  # type: ignore[import-untyped]
from sklearn.frozen import FrozenEstimator  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import OneHotEncoder  # type: ignore[import-untyped]

from ...data.synthetic.modeling import ModelingDatasets, PDModelingRow
from ...domain.exceptions import DomainValidationError
from .baselines import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    ModelMetrics,
    _frame,
    _metrics,
)


@dataclass(frozen=True, slots=True)
class CalibratedCandidate:
    name: str
    target: str
    uncalibrated_pipeline: Any
    calibrated_pipeline: Any | None
    validation_metrics_pre_calibration: ModelMetrics
    oot_metrics_post_calibration: ModelMetrics | None
    calibration_method: str | None


@dataclass(frozen=True, slots=True)
class TransitionProbability:
    product_code: str
    from_rating: str
    to_rating: str
    observations: int
    probability: float


@dataclass(frozen=True, slots=True)
class CandidateRegistryEntry:
    model_name: str
    role: str
    approval_status: str
    rationale: str


@dataclass(frozen=True, slots=True)
class CandidateComparison:
    calibrated_gradient_boosting_12m: CalibratedCandidate
    survival_gradient_boosting_hazard: CalibratedCandidate
    transition_probabilities: tuple[TransitionProbability, ...]
    registry: tuple[CandidateRegistryEntry, ...]


def _tree_pipeline() -> Pipeline:
    transformer = ColumnTransformer(
        (
            ("numeric", "passthrough", list(NUMERIC_FEATURES)),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(CATEGORICAL_FEATURES),
            ),
        )
    )
    return Pipeline(
        (
            ("features", transformer),
            (
                "model",
                HistGradientBoostingClassifier(
                    learning_rate=0.05,
                    max_depth=3,
                    max_iter=150,
                    min_samples_leaf=20,
                    random_state=20260714,
                ),
            ),
        )
    )


def _balanced_weights(target: np.ndarray) -> np.ndarray:
    positives = int(target.sum())
    negatives = len(target) - positives
    if positives == 0 or negatives == 0:
        raise DomainValidationError("candidate training requires both target classes")
    return np.where(target == 1, len(target) / (2 * positives), len(target) / (2 * negatives))


def _fit_candidate(
    train: list[PDModelingRow],
    validation: list[PDModelingRow],
    calibration: list[PDModelingRow],
    oot: list[PDModelingRow],
    *,
    target_name: str,
    model_name: str,
    calibrate: bool,
) -> CalibratedCandidate:
    target_train = np.asarray([getattr(item, target_name) for item in train], dtype=int)
    target_validation = np.asarray([getattr(item, target_name) for item in validation], dtype=int)
    pipeline = _tree_pipeline()
    pipeline.fit(
        _frame(train),
        target_train,
        model__sample_weight=_balanced_weights(target_train),
    )
    prediction = pipeline.predict_proba(_frame(validation))[:, 1]
    calibrated = None
    oot_metrics = None
    method = None
    if calibrate:
        target_calibration = np.asarray(
            [getattr(item, target_name) for item in calibration], dtype=int
        )
        if len(set(target_calibration.tolist())) != 2:
            raise DomainValidationError("calibration split requires both target classes")
        calibrated = CalibratedClassifierCV(FrozenEstimator(pipeline), method="isotonic")
        calibrated.fit(_frame(calibration), target_calibration)
        method = "isotonic"
        target_oot = np.asarray([getattr(item, target_name) for item in oot], dtype=int)
        oot_prediction = calibrated.predict_proba(_frame(oot))[:, 1]
        oot_metrics = _metrics(target_oot, oot_prediction)
    return CalibratedCandidate(
        model_name,
        target_name,
        pipeline,
        calibrated,
        _metrics(target_validation, prediction),
        oot_metrics,
        method,
    )


def _transition_matrices(
    train: list[PDModelingRow],
) -> tuple[TransitionProbability, ...]:
    by_contract: dict[str, list[PDModelingRow]] = {}
    for item in train:
        by_contract.setdefault(item.contract_id, []).append(item)
    counts: dict[tuple[str, str, str], int] = {}
    totals: dict[tuple[str, str], int] = {}
    for rows in by_contract.values():
        rows.sort(key=lambda item: item.observation_date)
        for left, right in zip(rows[:-1], rows[1:], strict=True):
            key = (left.product_code, left.rating, right.rating)
            counts[key] = counts.get(key, 0) + 1
            total_key = (left.product_code, left.rating)
            totals[total_key] = totals.get(total_key, 0) + 1
    return tuple(
        TransitionProbability(product, source, target, count, count / totals[(product, source)])
        for (product, source, target), count in sorted(counts.items())
    )


def fit_candidate_models(modeling: ModelingDatasets) -> CandidateComparison:
    train = [item for item in modeling.pd if item.split == "train"]
    validation = [item for item in modeling.pd if item.split == "validation"]
    calibration = [item for item in modeling.pd if item.split == "calibration"]
    oot = [item for item in modeling.pd if item.split == "oot"]
    boosting = _fit_candidate(
        train,
        validation,
        calibration,
        oot,
        target_name="target_default_12m",
        model_name="hist_gradient_boosting_12m",
        calibrate=True,
    )
    survival = _fit_candidate(
        train,
        validation,
        calibration,
        oot,
        target_name="target_hazard_1m",
        model_name="hist_gradient_boosting_discrete_hazard",
        calibrate=False,
    )
    registry = (
        CandidateRegistryEntry(
            "logistic_12m",
            "provisional_champion",
            "oot_failed_not_approved",
            "Explainable reference retained after frozen OOT calibration failure; "
            "no approved champion.",
        ),
        CandidateRegistryEntry(
            boosting.name,
            "challenger",
            "oot_evaluated_not_approved",
            "Isotonic calibrator used OOT once for audit; registry role was not selected on OOT.",
        ),
        CandidateRegistryEntry(
            survival.name,
            "challenger",
            "insufficient_hazard_events",
            "Discrete survival candidate retained, but monthly event counts are sparse.",
        ),
        CandidateRegistryEntry(
            "rating_transition_matrix",
            "small_segment_challenger",
            "pending_validation",
            "Empirical train-only transitions for segments where model estimation is unstable.",
        ),
    )
    return CandidateComparison(boosting, survival, _transition_matrices(train), registry)
