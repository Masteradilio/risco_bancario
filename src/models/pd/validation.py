"""Frozen OOT validation report for synthetic PD models."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.stats import binomtest  # type: ignore[import-untyped]
from sklearn.metrics import (  # type: ignore[import-untyped]
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
    roc_curve,
)

from ...data.synthetic.modeling import ModelingDatasets, PDModelingRow
from .baselines import _frame, fit_explainable_baselines
from .calibration import calibrate_explainable_pd


@dataclass(frozen=True, slots=True)
class DiscriminationMetrics:
    roc_auc: float
    gini: float
    ks: float
    pr_auc: float


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    lower_bound: float
    upper_bound: float
    row_count: int
    event_count: int
    mean_prediction: float
    observed_rate: float
    absolute_error: float


@dataclass(frozen=True, slots=True)
class ProbabilisticMetrics:
    brier_score: float
    log_loss: float
    expected_calibration_error: float


@dataclass(frozen=True, slots=True)
class BinomialRatingTest:
    rating: str
    row_count: int
    observed_events: int
    expected_events: float
    p_value: float
    reject_at_5_percent: bool


@dataclass(frozen=True, slots=True)
class SegmentValidation:
    dimension: str
    value: str
    row_count: int
    event_count: int
    observed_rate: float
    mean_prediction: float
    observed_to_expected: float | None
    absolute_calibration_error: float
    brier_score: float


@dataclass(frozen=True, slots=True)
class StabilityResult:
    metric: str
    reference_split: str
    comparison_split: str
    population_stability_index: float
    interpretation: str


@dataclass(frozen=True, slots=True)
class PDValidationReport:
    model_name: str
    modeling_version: str
    evaluation_split: str
    sample_count: int
    event_count: int
    discrimination: DiscriminationMetrics
    probabilistic: ProbabilisticMetrics
    calibration_bins: tuple[CalibrationBin, ...]
    binomial_rating_tests: tuple[BinomialRatingTest, ...]
    segments: tuple[SegmentValidation, ...]
    stability: StabilityResult
    backtesting_status: str
    bias_analysis_status: str
    approval_status: str
    evidence_scope: str


def _target(rows: list[PDModelingRow]) -> np.ndarray:
    return np.asarray([item.target_default_12m == 1 for item in rows], dtype=int)


def _calibration_bins(
    target: np.ndarray, prediction: np.ndarray, bins: int = 10
) -> tuple[CalibrationBin, ...]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    result: list[CalibrationBin] = []
    for index in range(bins):
        lower = float(edges[index])
        upper = float(edges[index + 1])
        mask = (prediction >= lower) & (
            prediction <= upper if index == bins - 1 else prediction < upper
        )
        if not np.any(mask):
            continue
        group_target = target[mask]
        group_prediction = prediction[mask]
        observed = float(group_target.mean())
        mean_prediction = float(group_prediction.mean())
        result.append(
            CalibrationBin(
                lower,
                upper,
                len(group_target),
                int(group_target.sum()),
                mean_prediction,
                observed,
                abs(mean_prediction - observed),
            )
        )
    return tuple(result)


def _segment(
    dimension: str,
    value: str,
    rows: list[PDModelingRow],
    prediction: np.ndarray,
) -> SegmentValidation:
    target = _target(rows)
    observed = float(target.mean())
    expected = float(prediction.mean())
    return SegmentValidation(
        dimension,
        value,
        len(rows),
        int(target.sum()),
        observed,
        expected,
        observed / expected if expected > 0 else None,
        abs(observed - expected),
        float(brier_score_loss(target, prediction)),
    )


def _segments(rows: list[PDModelingRow], prediction: np.ndarray) -> tuple[SegmentValidation, ...]:
    dimensions: dict[str, Callable[[PDModelingRow], str]] = {
        "rating": lambda row: row.rating,
        "product": lambda row: row.product_code,
        "vintage": lambda row: row.origination_cohort[:4],
    }
    result: list[SegmentValidation] = []
    for dimension, key in dimensions.items():
        for value in sorted({key(item) for item in rows}):
            indices = [index for index, item in enumerate(rows) if key(item) == value]
            result.append(
                _segment(
                    dimension,
                    value,
                    [rows[index] for index in indices],
                    prediction[indices],
                )
            )
    return tuple(result)


def _psi(reference: np.ndarray, comparison: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    reference_counts, _ = np.histogram(reference, bins=edges)
    comparison_counts, _ = np.histogram(comparison, bins=edges)
    epsilon = 1e-6
    reference_share = np.clip(reference_counts / len(reference), epsilon, None)
    comparison_share = np.clip(comparison_counts / len(comparison), epsilon, None)
    return float(
        np.sum((comparison_share - reference_share) * np.log(comparison_share / reference_share))
    )


def validate_frozen_pd(modeling: ModelingDatasets) -> PDValidationReport:
    """Evaluate a frozen calibrated baseline; never use OOT to alter the model."""
    calibrated = calibrate_explainable_pd(modeling)
    oot = [item for item in modeling.pd if item.split == "oot"]
    target = _target(oot)
    prediction = calibrated.calibrated_pipeline.predict_proba(_frame(oot))[:, 1]
    auc = float(roc_auc_score(target, prediction))
    false_positive_rate, true_positive_rate, _ = roc_curve(target, prediction)
    ks = float(np.max(true_positive_rate - false_positive_rate))
    bins = _calibration_bins(target, prediction)
    ece = sum(item.row_count * item.absolute_error for item in bins) / len(target)

    rating_tests: list[BinomialRatingTest] = []
    for rating in sorted({item.rating for item in oot}):
        indices = [index for index, item in enumerate(oot) if item.rating == rating]
        observed = int(target[indices].sum())
        probability = float(prediction[indices].mean())
        result = binomtest(observed, len(indices), probability)
        rating_tests.append(
            BinomialRatingTest(
                rating,
                len(indices),
                observed,
                len(indices) * probability,
                float(result.pvalue),
                bool(result.pvalue < 0.05),
            )
        )

    baseline = fit_explainable_baselines(modeling).logistic_12m.pipeline
    calibration_rows = [item for item in modeling.pd if item.split == "calibration"]
    backtesting = [item for item in modeling.pd if item.split == "backtesting"]
    reference_score = baseline.predict_proba(_frame(calibration_rows))[:, 1]
    backtesting_score = baseline.predict_proba(_frame(backtesting))[:, 1]
    psi = _psi(reference_score, backtesting_score)
    interpretation = (
        "high_shift" if psi >= 0.25 else "moderate_shift" if psi >= 0.1 else "low_shift"
    )
    return PDValidationReport(
        "logistic_12m_isotonic_frozen",
        modeling.version,
        "oot",
        len(oot),
        int(target.sum()),
        DiscriminationMetrics(
            auc,
            2 * auc - 1,
            ks,
            float(average_precision_score(target, prediction)),
        ),
        ProbabilisticMetrics(
            float(brier_score_loss(target, prediction)),
            float(log_loss(target, prediction, labels=[0, 1])),
            float(ece),
        ),
        bins,
        tuple(rating_tests),
        _segments(oot, prediction),
        StabilityResult("uncalibrated_pd_score", "calibration", "backtesting", psi, interpretation),
        "pending_target_maturation",
        "segment_diagnostics_only_no_protected_attributes",
        "not_approved",
        "synthetic_demonstrative_only",
    )
