"""Leakage-controlled temporal calibration for the explainable 12-month PD."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
from sklearn.calibration import CalibratedClassifierCV  # type: ignore[import-untyped]
from sklearn.frozen import FrozenEstimator  # type: ignore[import-untyped]
from sklearn.metrics import brier_score_loss  # type: ignore[import-untyped]

from ...data.synthetic.modeling import ModelingDatasets, PDModelingRow
from ...domain.exceptions import DomainValidationError
from .baselines import ModelMetrics, _frame, _metrics, fit_explainable_baselines

SPLIT_ORDER = ("train", "validation", "calibration", "oot", "backtesting")


@dataclass(frozen=True, slots=True)
class TemporalSplitSummary:
    split: str
    start_date: date
    end_date: date
    row_count: int
    event_count: int | None
    targets_complete: bool


@dataclass(frozen=True, slots=True)
class CalibrationMethodResult:
    method: str
    validation_holdout_metrics: ModelMetrics


@dataclass(frozen=True, slots=True)
class CalibrationSlice:
    dimension: str
    value: str
    row_count: int
    event_count: int
    observed_rate: float
    mean_prediction: float
    absolute_calibration_error: float
    brier_score: float


@dataclass(frozen=True, slots=True)
class TemporalCalibrationResult:
    selected_method: str
    method_comparison: tuple[CalibrationMethodResult, ...]
    calibrated_pipeline: Any
    oot_metrics: ModelMetrics
    oot_slices: tuple[CalibrationSlice, ...]
    split_summary: tuple[TemporalSplitSummary, ...]
    embargo_months: int
    approval_status: str


def summarize_temporal_splits(modeling: ModelingDatasets) -> tuple[TemporalSplitSummary, ...]:
    summaries: list[TemporalSplitSummary] = []
    prior_end: date | None = None
    for split in SPLIT_ORDER:
        rows = [item for item in modeling.pd if item.split == split]
        if not rows:
            raise DomainValidationError(f"temporal split is empty: {split}")
        start = min(item.observation_date for item in rows)
        end = max(item.observation_date for item in rows)
        if prior_end is not None and start <= prior_end:
            raise DomainValidationError("temporal splits must be strictly ordered")
        targets_complete = all(item.target_default_12m is not None for item in rows)
        events = (
            len([item for item in rows if item.target_default_12m == 1])
            if targets_complete
            else None
        )
        summaries.append(
            TemporalSplitSummary(split, start, end, len(rows), events, targets_complete)
        )
        prior_end = end
    return tuple(summaries)


def _calibrator(base_pipeline: Any, rows: list[PDModelingRow], method: str) -> Any:
    target = _target(rows)
    if len(set(target.tolist())) != 2:
        raise DomainValidationError(f"calibrator {method} requires both target classes")
    model = CalibratedClassifierCV(FrozenEstimator(base_pipeline), method=method)
    model.fit(_frame(rows), target)
    return model


def _target(rows: list[PDModelingRow]) -> np.ndarray:
    if any(item.target_default_12m is None for item in rows):
        raise DomainValidationError("calibration requires mature 12-month targets")
    return np.asarray([item.target_default_12m == 1 for item in rows], dtype=int)


def _slice(
    dimension: str,
    value: str,
    rows: list[PDModelingRow],
    prediction: np.ndarray,
) -> CalibrationSlice:
    target = _target(rows)
    observed = float(target.mean())
    mean_prediction = float(prediction.mean())
    return CalibrationSlice(
        dimension,
        value,
        len(rows),
        int(target.sum()),
        observed,
        mean_prediction,
        abs(mean_prediction - observed),
        float(brier_score_loss(target, prediction)),
    )


def _slice_metrics(
    rows: list[PDModelingRow], prediction: np.ndarray
) -> tuple[CalibrationSlice, ...]:
    dimensions: dict[str, Callable[[PDModelingRow], str]] = {
        "rating": lambda row: row.rating,
        "product": lambda row: row.product_code,
        "vintage": lambda row: row.origination_cohort[:4],
    }
    result: list[CalibrationSlice] = []
    for dimension, key in dimensions.items():
        values = sorted({key(item) for item in rows})
        for value in values:
            indices = [index for index, item in enumerate(rows) if key(item) == value]
            group_rows = [rows[index] for index in indices]
            result.append(_slice(dimension, value, group_rows, prediction[indices]))
    return tuple(result)


def calibrate_explainable_pd(modeling: ModelingDatasets) -> TemporalCalibrationResult:
    """Select calibration on validation, fit on calibration and evaluate OOT once."""
    split_summary = summarize_temporal_splits(modeling)
    baseline = fit_explainable_baselines(modeling).logistic_12m
    validation = sorted(
        (item for item in modeling.pd if item.split == "validation"),
        key=lambda item: (item.observation_date, item.contract_id),
    )
    validation_dates = sorted({item.observation_date for item in validation})
    midpoint = validation_dates[len(validation_dates) // 2]
    selection_fit = [item for item in validation if item.observation_date < midpoint]
    selection_holdout = [item for item in validation if item.observation_date >= midpoint]
    holdout_target = _target(selection_holdout)
    comparisons: list[CalibrationMethodResult] = []
    for method in ("sigmoid", "isotonic"):
        candidate = _calibrator(baseline.pipeline, selection_fit, method)
        prediction = candidate.predict_proba(_frame(selection_holdout))[:, 1]
        comparisons.append(CalibrationMethodResult(method, _metrics(holdout_target, prediction)))
    comparisons.sort(
        key=lambda item: (
            item.validation_holdout_metrics.brier_score,
            item.validation_holdout_metrics.calibration_in_the_large_error,
            item.method,
        )
    )
    selected = comparisons[0].method
    calibration = [item for item in modeling.pd if item.split == "calibration"]
    calibrated = _calibrator(baseline.pipeline, calibration, selected)
    oot = [item for item in modeling.pd if item.split == "oot"]
    oot_target = _target(oot)
    oot_prediction = calibrated.predict_proba(_frame(oot))[:, 1]
    return TemporalCalibrationResult(
        selected,
        tuple(comparisons),
        calibrated,
        _metrics(oot_target, oot_prediction),
        _slice_metrics(oot, oot_prediction),
        split_summary,
        12,
        "synthetic_validation_not_approved",
    )
