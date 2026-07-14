"""Point-in-time LGD feature dataset and demonstrative model candidates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from math import sqrt
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from sklearn.compose import ColumnTransformer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression, Ridge  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # type: ignore[import-untyped]

from ...data.synthetic.longitudinal import LongitudinalPortfolio, MonthlySnapshotRecord
from ...data.synthetic.macroeconomics import MacroeconomicBundle
from ...data.synthetic.population import SyntheticPortfolio
from ...domain.exceptions import DomainValidationError
from .realized import RealizedLGD
from .workout import LGDWorkoutDataset

NUMERIC_FEATURES = (
    "exposure_at_default",
    "collateral_appraised_value",
    "collateral_enforceable_share",
    "collateral_ltv",
    "days_past_due",
    "remaining_term_months",
    "gdp_growth",
    "inflation",
    "policy_rate",
    "unemployment",
    "household_debt",
)
CATEGORICAL_FEATURES = ("product_code", "collateral_type")


@dataclass(frozen=True, slots=True)
class LGDModelingRow:
    default_id: str
    default_date: date
    split: str
    product_code: str
    collateral_type: str
    exposure_at_default: Decimal
    collateral_appraised_value: Decimal
    collateral_enforceable_share: Decimal
    collateral_ltv: Decimal
    days_past_due: int
    remaining_term_months: int
    gdp_growth: Decimal
    inflation: Decimal
    policy_rate: Decimal
    unemployment: Decimal
    household_debt: Decimal
    target_lgd: Decimal
    target_cure: int
    target_full_loss: int


@dataclass(frozen=True, slots=True)
class LGDModelingDataset:
    rows: tuple[LGDModelingRow, ...]
    version: str
    validation_start_year: int
    censored_excluded: int


@dataclass(frozen=True, slots=True)
class LGDMetrics:
    sample_count: int
    mean_actual: float
    mean_prediction: float
    calibration_in_the_large_error: float
    mean_absolute_error: float
    root_mean_squared_error: float


@dataclass(frozen=True, slots=True)
class SegmentEstimate:
    product_code: str
    collateral_type: str
    observations: int
    mean_lgd: float


@dataclass(frozen=True, slots=True)
class LGDCandidate:
    name: str
    approach: str
    validation_metrics: LGDMetrics
    model: Any
    secondary_models: tuple[Any, ...]
    approval_status: str
    rationale: str


@dataclass(frozen=True, slots=True)
class LGDModelComparison:
    segmented_baseline: LGDCandidate
    one_stage_regression: LGDCandidate
    two_stage_cure_severity: LGDCandidate
    one_inflated_regression: LGDCandidate
    segment_estimates: tuple[SegmentEstimate, ...]
    selected_for_validation: str
    selection_basis: str


def _months_between(start: date, end: date) -> int:
    return max(0, (end.year - start.year) * 12 + end.month - start.month)


def build_lgd_modeling_dataset(
    workout: LGDWorkoutDataset,
    realized: tuple[RealizedLGD, ...],
    population: SyntheticPortfolio,
    history: LongitudinalPortfolio,
    macro: MacroeconomicBundle,
    *,
    validation_start_year: int = 2022,
) -> LGDModelingDataset:
    if len(workout.records) != len(realized):
        raise DomainValidationError("workout and realized LGD datasets must have equal length")
    contracts = {item.contract_id: item for item in population.contracts}
    snapshots: dict[str, list[MonthlySnapshotRecord]] = {}
    for item in history.snapshots:
        snapshots.setdefault(item.contract_id, []).append(item)
    macro_rows = sorted(macro.observed, key=lambda item: item.reference_date)
    rows: list[LGDModelingRow] = []
    censored = 0
    for source, target in zip(workout.records, realized, strict=True):
        if source.default_id != target.default_id:
            raise DomainValidationError("workout and realized LGD default order differs")
        if source.is_censored:
            censored += 1
            continue
        contract = contracts[source.contract_id]
        prior_snapshots = [
            item
            for item in snapshots.get(source.contract_id, [])
            if item.reference_date < source.default_date
        ]
        prior_macro = [item for item in macro_rows if item.reference_date <= source.default_date]
        if not prior_snapshots or not prior_macro:
            raise DomainValidationError("point-in-time LGD feature evidence is missing")
        snapshot = max(prior_snapshots, key=lambda item: item.reference_date)
        macro_row = prior_macro[-1]
        enforceable_value = source.collateral_appraised_value * source.collateral_enforceable_share
        ltv = (
            source.exposure_at_default / enforceable_value
            if enforceable_value > 0
            else Decimal("10")
        )
        rows.append(
            LGDModelingRow(
                source.default_id,
                source.default_date,
                "validation" if source.default_date.year >= validation_start_year else "train",
                source.product_code,
                source.collateral_type or "none",
                source.exposure_at_default,
                source.collateral_appraised_value,
                source.collateral_enforceable_share,
                min(ltv, Decimal("10")),
                snapshot.days_past_due,
                _months_between(source.default_date, contract.maturity_date),
                macro_row.gdp_growth,
                macro_row.inflation,
                macro_row.policy_rate,
                macro_row.unemployment,
                macro_row.household_debt,
                target.realized_lgd,
                int(target.outcome_type == "cure_lgd"),
                int(target.realized_lgd == Decimal("1")),
            )
        )
    return LGDModelingDataset(tuple(rows), "0.1.0", validation_start_year, censored)


def _frame(rows: list[LGDModelingRow]) -> pd.DataFrame:
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


def _regression_pipeline() -> Pipeline:
    features = ColumnTransformer(
        (
            ("numeric", StandardScaler(), list(NUMERIC_FEATURES)),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(CATEGORICAL_FEATURES),
            ),
        )
    )
    return Pipeline((("features", features), ("model", Ridge(alpha=10.0))))


def _classification_pipeline() -> Pipeline:
    features = ColumnTransformer(
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
            ("features", features),
            ("model", LogisticRegression(max_iter=2000, random_state=20260714)),
        )
    )


def _metrics(actual: np.ndarray, prediction: np.ndarray) -> LGDMetrics:
    errors = prediction - actual
    return LGDMetrics(
        len(actual),
        float(actual.mean()),
        float(prediction.mean()),
        abs(float(prediction.mean() - actual.mean())),
        float(np.abs(errors).mean()),
        sqrt(float(np.square(errors).mean())),
    )


def _segment_baseline(
    train: list[LGDModelingRow], validation: list[LGDModelingRow]
) -> tuple[np.ndarray, tuple[SegmentEstimate, ...]]:
    overall = float(np.mean([float(item.target_lgd) for item in train]))
    grouped: dict[tuple[str, str], list[float]] = {}
    for item in train:
        grouped.setdefault((item.product_code, item.collateral_type), []).append(
            float(item.target_lgd)
        )
    estimates = tuple(
        SegmentEstimate(product, collateral, len(values), float(np.mean(values)))
        for (product, collateral), values in sorted(grouped.items())
    )
    lookup = {(item.product_code, item.collateral_type): item.mean_lgd for item in estimates}
    prediction = np.asarray(
        [lookup.get((item.product_code, item.collateral_type), overall) for item in validation]
    )
    return prediction, estimates


def fit_lgd_models(dataset: LGDModelingDataset) -> LGDModelComparison:
    train = [item for item in dataset.rows if item.split == "train"]
    validation = [item for item in dataset.rows if item.split == "validation"]
    if not train or not validation:
        raise DomainValidationError("LGD modeling requires train and validation rows")
    actual = np.asarray([float(item.target_lgd) for item in validation])

    baseline_prediction, estimates = _segment_baseline(train, validation)
    baseline = LGDCandidate(
        "segmented_mean",
        "product_and_collateral_segment_mean",
        _metrics(actual, baseline_prediction),
        None,
        (),
        "demonstrative_not_approved",
        "Reference estimate; sparse synthetic segments are not institutionally credible.",
    )

    one_stage_model = _regression_pipeline()
    one_stage_model.fit(_frame(train), [float(item.target_lgd) for item in train])
    one_stage_prediction = np.clip(one_stage_model.predict(_frame(validation)), 0.0, 1.0)
    one_stage = LGDCandidate(
        "ridge_one_stage",
        "bounded_one_stage_regression",
        _metrics(actual, one_stage_prediction),
        one_stage_model,
        (),
        "demonstrative_not_approved",
        "Small synthetic sample; bounds are applied only to predictions.",
    )

    cure_target = np.asarray([item.target_cure for item in train])
    if len(set(cure_target.tolist())) != 2:
        raise DomainValidationError("two-stage LGD requires cure and non-cure training rows")
    cure_classifier = _classification_pipeline()
    cure_classifier.fit(_frame(train), cure_target)
    cure_model = _regression_pipeline()
    loss_model = _regression_pipeline()
    cure_rows = [item for item in train if item.target_cure]
    loss_rows = [item for item in train if not item.target_cure]
    cure_model.fit(_frame(cure_rows), [float(item.target_lgd) for item in cure_rows])
    loss_model.fit(_frame(loss_rows), [float(item.target_lgd) for item in loss_rows])
    cure_probability = cure_classifier.predict_proba(_frame(validation))[:, 1]
    cure_severity = np.clip(cure_model.predict(_frame(validation)), 0.0, 1.0)
    loss_severity = np.clip(loss_model.predict(_frame(validation)), 0.0, 1.0)
    two_stage_prediction = cure_probability * cure_severity + (1 - cure_probability) * loss_severity
    two_stage = LGDCandidate(
        "cure_probability_and_severity",
        "two_stage_cure_probability_plus_conditional_severity",
        _metrics(actual, two_stage_prediction),
        cure_classifier,
        (cure_model, loss_model),
        "demonstrative_not_approved",
        "Cure and loss severities are separated, but the cure training subset is sparse.",
    )

    full_loss_target = np.asarray([item.target_full_loss for item in train])
    if len(set(full_loss_target.tolist())) != 2:
        raise DomainValidationError("one-inflated LGD requires full and fractional loss rows")
    full_loss_classifier = _classification_pipeline()
    full_loss_classifier.fit(_frame(train), full_loss_target)
    fractional_rows = [item for item in train if not item.target_full_loss]
    fractional_model = _regression_pipeline()
    fractional_model.fit(
        _frame(fractional_rows), [float(item.target_lgd) for item in fractional_rows]
    )
    probability_full = full_loss_classifier.predict_proba(_frame(validation))[:, 1]
    fractional_prediction = np.clip(fractional_model.predict(_frame(validation)), 0.0, 1.0)
    inflated_prediction = probability_full + (1 - probability_full) * fractional_prediction
    inflated = LGDCandidate(
        "one_inflated_ridge",
        "probability_of_full_loss_plus_fractional_severity",
        _metrics(actual, inflated_prediction),
        full_loss_classifier,
        (fractional_model,),
        "demonstrative_not_approved",
        "Six exact full losses make one-inflation relevant; zero inflation and beta-only "
        "regression are not supported by this sample.",
    )

    candidates = (baseline, one_stage, two_stage, inflated)
    selected = min(candidates, key=lambda item: item.validation_metrics.root_mean_squared_error)
    return LGDModelComparison(
        baseline,
        one_stage,
        two_stage,
        inflated,
        estimates,
        selected.name,
        "Lowest pre-validation temporal holdout RMSE; selection is provisional and not approval.",
    )
