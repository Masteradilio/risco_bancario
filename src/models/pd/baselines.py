"""Explainable point-in-time logistic and discrete-hazard PD baselines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from sklearn.compose import ColumnTransformer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.metrics import (  # type: ignore[import-untyped]
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # type: ignore[import-untyped]

from ...data.synthetic.modeling import ModelingDatasets, PDModelingRow
from ...domain.exceptions import DomainValidationError

NUMERIC_FEATURES = (
    "balance",
    "credit_limit",
    "utilization",
    "days_past_due",
    "behavior_score",
    "gdp_growth",
    "inflation",
    "policy_rate",
    "unemployment",
    "household_debt",
)
CATEGORICAL_FEATURES = ("product_code", "rating")


@dataclass(frozen=True, slots=True)
class ModelMetrics:
    sample_count: int
    event_count: int
    event_rate: float
    mean_prediction: float
    calibration_in_the_large_error: float
    brier_score: float
    log_loss: float
    roc_auc: float
    average_precision: float


@dataclass(frozen=True, slots=True)
class ModelCoefficient:
    feature: str
    coefficient: float


@dataclass(frozen=True, slots=True)
class RatingBand:
    grade: str
    minimum_pd: float
    maximum_pd: float
    mean_pd: float
    observed_default_rate: float
    count: int


@dataclass(frozen=True, slots=True)
class BaselineModel:
    name: str
    target: str
    pipeline: Any
    validation_metrics: ModelMetrics
    coefficients: tuple[ModelCoefficient, ...]
    train_count: int
    calibration_count: int


@dataclass(frozen=True, slots=True)
class BaselineComparison:
    logistic_12m: BaselineModel
    discrete_hazard_1m: BaselineModel
    rating_bands: tuple[RatingBand, ...]


def _frame(rows: list[PDModelingRow]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                feature: (
                    float(getattr(row, feature))
                    if feature in NUMERIC_FEATURES
                    else getattr(row, feature)
                )
                for feature in (*NUMERIC_FEATURES, *CATEGORICAL_FEATURES)
            }
            for row in rows
        ]
    )


def _pipeline() -> Pipeline:
    transformer = ColumnTransformer(
        (
            ("numeric", StandardScaler(), list(NUMERIC_FEATURES)),
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
                LogisticRegression(class_weight="balanced", max_iter=2000, random_state=20260714),
            ),
        )
    )


def _metrics(target: np.ndarray, prediction: np.ndarray) -> ModelMetrics:
    if len(set(target.tolist())) != 2:
        raise DomainValidationError("evaluation split must contain events and non-events")
    event_rate = float(target.mean())
    mean_prediction = float(prediction.mean())
    return ModelMetrics(
        len(target),
        int(target.sum()),
        event_rate,
        mean_prediction,
        abs(mean_prediction - event_rate),
        float(brier_score_loss(target, prediction)),
        float(log_loss(target, prediction, labels=[0, 1])),
        float(roc_auc_score(target, prediction)),
        float(average_precision_score(target, prediction)),
    )


def _fit(
    train: list[PDModelingRow],
    validation: list[PDModelingRow],
    calibration: list[PDModelingRow],
    *,
    target: str,
    name: str,
) -> BaselineModel:
    y_train = np.asarray([getattr(row, target) for row in train], dtype=int)
    y_validation = np.asarray([getattr(row, target) for row in validation], dtype=int)
    if len(set(y_train.tolist())) != 2:
        raise DomainValidationError(f"training target {target} requires both classes")
    pipeline = _pipeline()
    pipeline.fit(_frame(train), y_train)
    prediction = pipeline.predict_proba(_frame(validation))[:, 1]
    feature_names = pipeline.named_steps["features"].get_feature_names_out()
    coefficients = pipeline.named_steps["model"].coef_[0]
    coefficient_table = tuple(
        ModelCoefficient(str(feature), float(value))
        for feature, value in zip(feature_names, coefficients, strict=True)
    )
    return BaselineModel(
        name,
        target,
        pipeline,
        _metrics(y_validation, prediction),
        coefficient_table,
        len(train),
        len(calibration),
    )


def _rating_bands(
    model: BaselineModel, calibration: list[PDModelingRow], bands: int = 5
) -> tuple[RatingBand, ...]:
    prediction = model.pipeline.predict_proba(_frame(calibration))[:, 1]
    target = np.asarray([item.target_default_12m for item in calibration], dtype=int)
    order = np.argsort(prediction)
    chunks = np.array_split(order, bands)
    result: list[RatingBand] = []
    for index, chunk in enumerate(chunks, start=1):
        values = prediction[chunk]
        outcomes = target[chunk]
        result.append(
            RatingBand(
                f"R{index}",
                float(values.min()),
                float(values.max()),
                float(values.mean()),
                float(outcomes.mean()),
                len(chunk),
            )
        )
    return tuple(result)


def fit_explainable_baselines(modeling: ModelingDatasets) -> BaselineComparison:
    train = [item for item in modeling.pd if item.split == "train"]
    validation = [item for item in modeling.pd if item.split == "validation"]
    calibration = [item for item in modeling.pd if item.split == "calibration"]
    logistic = _fit(
        train,
        validation,
        calibration,
        target="target_default_12m",
        name="logistic_12m",
    )
    hazard = _fit(
        train,
        validation,
        calibration,
        target="target_hazard_1m",
        name="discrete_time_logistic_hazard",
    )
    return BaselineComparison(logistic, hazard, _rating_bands(logistic, calibration))
