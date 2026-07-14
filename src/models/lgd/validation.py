"""Temporal LGD validation, stability and downturn sensitivity report."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import numpy as np

from ...domain.exceptions import DomainValidationError
from .modeling import (
    LGDCandidate,
    LGDMetrics,
    LGDModelComparison,
    LGDModelingDataset,
    LGDModelingRow,
    SegmentEstimate,
    _frame,
    _metrics,
)


@dataclass(frozen=True, slots=True)
class LGDValidationPolicy:
    policy_version: str
    effective_from: date
    evidence_status: str
    minimum_validation_observations: int
    maximum_mae: Decimal
    maximum_rmse: Decimal
    maximum_band_calibration_error: Decimal
    minimum_observations_per_cohort: int
    minimum_observations_per_product: int
    minimum_downturn_observations: int
    calibration_bands: int
    require_independent_oot_after_selection: bool
    downturn_definition: str
    downturn_usage: str
    sha256: str


@dataclass(frozen=True, slots=True)
class LGDPrediction:
    default_id: str
    default_date: date
    product_code: str
    actual_lgd: float
    predicted_lgd: float
    error: float


@dataclass(frozen=True, slots=True)
class LGDCalibrationBand:
    band: int
    observations: int
    minimum_prediction: float
    maximum_prediction: float
    mean_prediction: float
    mean_actual: float
    calibration_error: float


@dataclass(frozen=True, slots=True)
class LGDCohortBacktest:
    cohort: str
    observations: int
    mean_prediction: float
    mean_actual: float
    mean_absolute_error: float


@dataclass(frozen=True, slots=True)
class LGDProductStability:
    product_code: str
    train_observations: int
    validation_observations: int
    train_mean_lgd: float
    validation_mean_lgd: float
    mean_shift: float
    status: str


@dataclass(frozen=True, slots=True)
class LGDDownturnAnalysis:
    definition: str
    threshold: float
    observations: int
    observed_mean_lgd: float
    pit_mean_prediction: float
    downturn_addon: float
    usage: str
    status: str


@dataclass(frozen=True, slots=True)
class LGDValidationReport:
    model_name: str
    predictions: tuple[LGDPrediction, ...]
    metrics: LGDMetrics
    calibration_bands: tuple[LGDCalibrationBand, ...]
    cohort_backtests: tuple[LGDCohortBacktest, ...]
    product_stability: tuple[LGDProductStability, ...]
    downturn_analysis: LGDDownturnAnalysis
    approval_status: str
    blockers: tuple[str, ...]
    policy_version: str
    policy_sha256: str


def load_lgd_validation_policy(path: Path) -> LGDValidationPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document["schema_version"] != "1.0.0":
        raise DomainValidationError("unsupported LGD validation policy schema")
    policy = LGDValidationPolicy(
        document["policy_version"],
        date.fromisoformat(document["effective_from"]),
        document["evidence_status"],
        int(document["minimum_validation_observations"]),
        Decimal(document["maximum_mae"]),
        Decimal(document["maximum_rmse"]),
        Decimal(document["maximum_band_calibration_error"]),
        int(document["minimum_observations_per_cohort"]),
        int(document["minimum_observations_per_product"]),
        int(document["minimum_downturn_observations"]),
        int(document["calibration_bands"]),
        bool(document["require_independent_oot_after_selection"]),
        document["downturn_definition"],
        document["downturn_usage"],
        sha256(raw).hexdigest(),
    )
    if (
        policy.minimum_validation_observations <= 0
        or policy.maximum_mae <= 0
        or policy.maximum_rmse <= 0
        or policy.maximum_band_calibration_error <= 0
        or policy.calibration_bands <= 1
    ):
        raise DomainValidationError("LGD validation thresholds are invalid")
    return policy


def _selected_candidate(comparison: LGDModelComparison) -> LGDCandidate:
    candidates = (
        comparison.segmented_baseline,
        comparison.one_stage_regression,
        comparison.two_stage_cure_severity,
        comparison.one_inflated_regression,
    )
    selected = next(
        (item for item in candidates if item.name == comparison.selected_for_validation), None
    )
    if selected is None:
        raise DomainValidationError("selected LGD candidate is not in the comparison")
    return selected


def _segment_prediction(
    rows: list[LGDModelingRow], estimates: tuple[SegmentEstimate, ...]
) -> np.ndarray:
    total = sum(item.observations for item in estimates)
    if total <= 0:
        raise DomainValidationError("segmented LGD baseline has no estimates")
    fallback = sum(item.observations * item.mean_lgd for item in estimates) / total
    lookup = {(item.product_code, item.collateral_type): item.mean_lgd for item in estimates}
    return np.asarray(
        [lookup.get((item.product_code, item.collateral_type), fallback) for item in rows]
    )


def _predict(
    candidate: LGDCandidate,
    rows: list[LGDModelingRow],
    estimates: tuple[SegmentEstimate, ...],
) -> np.ndarray:
    if candidate.name == "segmented_mean":
        return _segment_prediction(rows, estimates)
    if candidate.name == "ridge_one_stage":
        return np.asarray(np.clip(candidate.model.predict(_frame(rows)), 0.0, 1.0), dtype=float)
    if candidate.name == "cure_probability_and_severity":
        cure_model, loss_model = candidate.secondary_models
        probability = candidate.model.predict_proba(_frame(rows))[:, 1]
        cure = np.clip(cure_model.predict(_frame(rows)), 0.0, 1.0)
        loss = np.clip(loss_model.predict(_frame(rows)), 0.0, 1.0)
        return np.asarray(probability * cure + (1 - probability) * loss, dtype=float)
    if candidate.name == "one_inflated_ridge":
        (fractional_model,) = candidate.secondary_models
        probability = candidate.model.predict_proba(_frame(rows))[:, 1]
        fractional = np.clip(fractional_model.predict(_frame(rows)), 0.0, 1.0)
        return np.asarray(probability + (1 - probability) * fractional, dtype=float)
    raise DomainValidationError("LGD candidate prediction strategy is unsupported")


def _calibration_bands(
    actual: np.ndarray, prediction: np.ndarray, bands: int
) -> tuple[LGDCalibrationBand, ...]:
    chunks = np.array_split(np.argsort(prediction), bands)
    return tuple(
        LGDCalibrationBand(
            index,
            len(chunk),
            float(prediction[chunk].min()),
            float(prediction[chunk].max()),
            float(prediction[chunk].mean()),
            float(actual[chunk].mean()),
            abs(float(prediction[chunk].mean() - actual[chunk].mean())),
        )
        for index, chunk in enumerate(chunks, start=1)
        if len(chunk)
    )


def _cohort(value: date) -> str:
    return f"{value.year}-Q{(value.month - 1) // 3 + 1}"


def _cohort_backtests(
    rows: list[LGDModelingRow], actual: np.ndarray, prediction: np.ndarray
) -> tuple[LGDCohortBacktest, ...]:
    result: list[LGDCohortBacktest] = []
    for cohort in sorted({_cohort(item.default_date) for item in rows}):
        indices = np.asarray(
            [index for index, item in enumerate(rows) if _cohort(item.default_date) == cohort]
        )
        result.append(
            LGDCohortBacktest(
                cohort,
                len(indices),
                float(prediction[indices].mean()),
                float(actual[indices].mean()),
                float(np.abs(prediction[indices] - actual[indices]).mean()),
            )
        )
    return tuple(result)


def _product_stability(
    train: list[LGDModelingRow], validation: list[LGDModelingRow]
) -> tuple[LGDProductStability, ...]:
    result: list[LGDProductStability] = []
    for product in sorted({item.product_code for item in (*train, *validation)}):
        train_values = [float(item.target_lgd) for item in train if item.product_code == product]
        validation_values = [
            float(item.target_lgd) for item in validation if item.product_code == product
        ]
        train_mean = float(np.mean(train_values)) if train_values else float("nan")
        validation_mean = float(np.mean(validation_values)) if validation_values else float("nan")
        shift = validation_mean - train_mean if train_values and validation_values else float("nan")
        result.append(
            LGDProductStability(
                product,
                len(train_values),
                len(validation_values),
                train_mean,
                validation_mean,
                shift,
                "descriptive_only_sparse_sample",
            )
        )
    return tuple(result)


def _downturn_analysis(
    rows: tuple[LGDModelingRow, ...], pit_mean: float, policy: LGDValidationPolicy
) -> LGDDownturnAnalysis:
    scores = np.asarray([float(item.unemployment - item.gdp_growth) for item in rows])
    threshold = float(np.quantile(scores, 0.75))
    indices = np.where(scores >= threshold)[0]
    observed = float(np.mean([float(rows[index].target_lgd) for index in indices]))
    return LGDDownturnAnalysis(
        policy.downturn_definition,
        threshold,
        len(indices),
        observed,
        pit_mean,
        max(0.0, observed - pit_mean),
        policy.downturn_usage,
        "descriptive_sensitivity_not_approved",
    )


def validate_lgd_model(
    dataset: LGDModelingDataset,
    comparison: LGDModelComparison,
    policy: LGDValidationPolicy,
) -> LGDValidationReport:
    train = [item for item in dataset.rows if item.split == "train"]
    validation = [item for item in dataset.rows if item.split == "validation"]
    if not train or not validation:
        raise DomainValidationError("LGD validation requires train and validation rows")
    candidate = _selected_candidate(comparison)
    prediction = _predict(candidate, validation, comparison.segment_estimates)
    actual = np.asarray([float(item.target_lgd) for item in validation])
    metrics = _metrics(actual, prediction)
    bands = _calibration_bands(actual, prediction, policy.calibration_bands)
    cohorts = _cohort_backtests(validation, actual, prediction)
    products = _product_stability(train, validation)
    downturn = _downturn_analysis(dataset.rows, metrics.mean_prediction, policy)
    blockers: list[str] = []
    if metrics.sample_count < policy.minimum_validation_observations:
        blockers.append("validation_sample_below_minimum")
    if Decimal(str(metrics.mean_absolute_error)) > policy.maximum_mae:
        blockers.append("mae_above_limit")
    if Decimal(str(metrics.root_mean_squared_error)) > policy.maximum_rmse:
        blockers.append("rmse_above_limit")
    if any(
        Decimal(str(item.calibration_error)) > policy.maximum_band_calibration_error
        for item in bands
    ):
        blockers.append("band_calibration_error_above_limit")
    if any(item.observations < policy.minimum_observations_per_cohort for item in cohorts):
        blockers.append("cohort_sample_below_minimum")
    if any(
        item.validation_observations < policy.minimum_observations_per_product for item in products
    ):
        blockers.append("product_sample_below_minimum")
    if downturn.observations < policy.minimum_downturn_observations:
        blockers.append("downturn_sample_below_minimum")
    if policy.require_independent_oot_after_selection:
        blockers.append("no_independent_oot_after_selection")
    if policy.evidence_status != "institutionally_validated":
        blockers.append("validation_evidence_not_institutionally_validated")
    predictions = tuple(
        LGDPrediction(
            row.default_id,
            row.default_date,
            row.product_code,
            float(row.target_lgd),
            float(predicted),
            float(predicted - float(row.target_lgd)),
        )
        for row, predicted in zip(validation, prediction, strict=True)
    )
    return LGDValidationReport(
        candidate.name,
        predictions,
        metrics,
        bands,
        cohorts,
        products,
        downturn,
        "not_approved" if blockers else "approved",
        tuple(blockers),
        policy.policy_version,
        policy.sha256,
    )
