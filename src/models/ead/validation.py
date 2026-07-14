"""Consolidated validation for amortized, revolving and off-balance EAD."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from hashlib import sha256
from math import sqrt
from pathlib import Path
from typing import cast

import numpy as np

from ...domain.exceptions import DomainValidationError
from .amortized import AmortizedDefaultEADDataset
from .off_balance import OffBalanceEADPolicy, project_off_balance_ead
from .revolving_ccf import (
    RevolvingCCFDataset,
    RevolvingCCFModel,
    RevolvingCCFRow,
    predict_revolving_ccf,
)


@dataclass(frozen=True, slots=True)
class EADValidationPolicy:
    policy_version: str
    effective_from: date
    evidence_status: str
    minimum_amortized_observations: int
    maximum_amortized_mae: Decimal
    minimum_ccf_validation_observations: int
    maximum_ccf_mae: Decimal
    maximum_ccf_rmse: Decimal
    minimum_segment_observations: int
    minimum_ccf_validation_years: int
    minimum_sensitivity_delta: Decimal
    require_limit_change_validation: bool
    require_institutional_evidence: bool
    sha256: str


@dataclass(frozen=True, slots=True)
class EADErrorMetrics:
    observations: int
    mean_actual: float
    mean_prediction: float
    mean_absolute_error: float
    root_mean_squared_error: float


@dataclass(frozen=True, slots=True)
class EADSegmentError:
    component: str
    segment: str
    observations: int
    mean_actual: float
    mean_prediction: float
    mean_absolute_error: float


@dataclass(frozen=True, slots=True)
class EADTemporalStability:
    component: str
    year: int
    observations: int
    mean_actual: float
    mean_prediction: float
    mean_absolute_error: float


@dataclass(frozen=True, slots=True)
class EADSensitivityCheck:
    name: str
    lower_input_prediction: float
    base_input_prediction: float
    higher_input_prediction: float
    responsive: bool
    expected_order_passed: bool | None
    status: str


@dataclass(frozen=True, slots=True)
class EADValidationReport:
    amortized_metrics: EADErrorMetrics
    ccf_metrics: EADErrorMetrics
    segment_errors: tuple[EADSegmentError, ...]
    temporal_stability: tuple[EADTemporalStability, ...]
    sensitivity_checks: tuple[EADSensitivityCheck, ...]
    approval_status: str
    blockers: tuple[str, ...]
    policy_version: str
    policy_sha256: str


def load_ead_validation_policy(path: Path) -> EADValidationPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document["schema_version"] != "1.0.0":
        raise DomainValidationError("unsupported EAD validation policy schema")
    policy = EADValidationPolicy(
        document["policy_version"],
        date.fromisoformat(document["effective_from"]),
        document["evidence_status"],
        int(document["minimum_amortized_observations"]),
        Decimal(document["maximum_amortized_mae"]),
        int(document["minimum_ccf_validation_observations"]),
        Decimal(document["maximum_ccf_mae"]),
        Decimal(document["maximum_ccf_rmse"]),
        int(document["minimum_segment_observations"]),
        int(document["minimum_ccf_validation_years"]),
        Decimal(document["minimum_sensitivity_delta"]),
        bool(document["require_limit_change_validation"]),
        bool(document["require_institutional_evidence"]),
        sha256(raw).hexdigest(),
    )
    if (
        policy.minimum_amortized_observations <= 0
        or policy.maximum_amortized_mae <= 0
        or policy.minimum_ccf_validation_observations <= 0
        or policy.maximum_ccf_mae <= 0
        or policy.maximum_ccf_rmse <= 0
        or policy.minimum_segment_observations <= 0
        or policy.minimum_sensitivity_delta <= 0
    ):
        raise DomainValidationError("EAD validation thresholds are invalid")
    return policy


def _metrics(actual: np.ndarray, prediction: np.ndarray) -> EADErrorMetrics:
    if not len(actual) or len(actual) != len(prediction):
        raise DomainValidationError("EAD validation vectors are empty or misaligned")
    errors = prediction - actual
    return EADErrorMetrics(
        len(actual),
        float(actual.mean()),
        float(prediction.mean()),
        float(np.abs(errors).mean()),
        sqrt(float(np.square(errors).mean())),
    )


def _segment(
    component: str,
    labels: list[str],
    actual: np.ndarray,
    prediction: np.ndarray,
) -> tuple[EADSegmentError, ...]:
    result: list[EADSegmentError] = []
    for label in sorted(set(labels)):
        indices = np.asarray([index for index, item in enumerate(labels) if item == label])
        metrics = _metrics(actual[indices], prediction[indices])
        result.append(
            EADSegmentError(
                component,
                label,
                metrics.observations,
                metrics.mean_actual,
                metrics.mean_prediction,
                metrics.mean_absolute_error,
            )
        )
    return tuple(result)


def _temporal(
    component: str,
    years: list[int],
    actual: np.ndarray,
    prediction: np.ndarray,
) -> tuple[EADTemporalStability, ...]:
    result: list[EADTemporalStability] = []
    for year in sorted(set(years)):
        indices = np.asarray([index for index, item in enumerate(years) if item == year])
        metrics = _metrics(actual[indices], prediction[indices])
        result.append(
            EADTemporalStability(
                component,
                year,
                metrics.observations,
                metrics.mean_actual,
                metrics.mean_prediction,
                metrics.mean_absolute_error,
            )
        )
    return tuple(result)


def _ccf_sensitivity(
    model: RevolvingCCFModel,
    template: RevolvingCCFRow,
    minimum_delta: Decimal,
) -> tuple[EADSensitivityCheck, EADSensitivityCheck]:
    utilization_rows = tuple(
        replace(
            template,
            utilization=value,
            horizon_months=6,
            product_code="credit_card",
        )
        for value in (Decimal("0.20"), Decimal("0.50"), Decimal("0.80"))
    )
    utilization_predictions = predict_revolving_ccf(model, utilization_rows)
    horizon_rows = tuple(
        replace(template, utilization=Decimal("0.50"), horizon_months=horizon)
        for horizon in (3, 6, 12)
    )
    horizon_predictions = predict_revolving_ccf(model, horizon_rows)
    threshold = float(minimum_delta)
    utilization_range = max(utilization_predictions) - min(utilization_predictions)
    horizon_range = max(horizon_predictions) - min(horizon_predictions)
    return (
        EADSensitivityCheck(
            "ccf_utilization",
            utilization_predictions[0],
            utilization_predictions[1],
            utilization_predictions[2],
            utilization_range >= threshold,
            None,
            "direction_diagnostic_only",
        ),
        EADSensitivityCheck(
            "ccf_horizon",
            horizon_predictions[0],
            horizon_predictions[1],
            horizon_predictions[2],
            horizon_range >= threshold,
            None,
            "direction_diagnostic_only",
        ),
    )


def _limit_sensitivity(policy: OffBalanceEADPolicy, minimum_delta: Decimal) -> EADSensitivityCheck:
    predictions = tuple(
        project_off_balance_ead(
            facility_type="commitment",
            horizon_months=12,
            original_limit=Decimal("100"),
            current_limit=limit,
            current_drawn=Decimal("0"),
            risk_multiplier=Decimal("1"),
            policy=policy,
        ).projected_ead
        for limit in (Decimal("50"), Decimal("75"), Decimal("100"))
    )
    return EADSensitivityCheck(
        "off_balance_current_limit",
        float(predictions[0]),
        float(predictions[1]),
        float(predictions[2]),
        predictions[-1] - predictions[0] >= minimum_delta,
        predictions[0] < predictions[1] < predictions[2],
        "parameterized_monotonicity_only",
    )


def validate_ead_models(
    amortized: AmortizedDefaultEADDataset,
    ccf_dataset: RevolvingCCFDataset,
    ccf_model: RevolvingCCFModel,
    off_balance_policy: OffBalanceEADPolicy,
    validation_policy: EADValidationPolicy,
) -> EADValidationReport:
    amortized_actual = np.asarray([float(item.observed_ead) for item in amortized.records])
    amortized_prediction = np.asarray([float(item.projected_ead) for item in amortized.records])
    amortized_metrics = _metrics(amortized_actual, amortized_prediction)
    validation_rows = tuple(
        item
        for item in ccf_dataset.rows
        if item.split == "validation" and item.target_ccf is not None
    )
    if not validation_rows:
        raise DomainValidationError("CCF temporal validation sample is empty")
    ccf_actual = np.asarray([float(cast(Decimal, item.target_ccf)) for item in validation_rows])
    ccf_prediction = np.asarray(predict_revolving_ccf(ccf_model, validation_rows))
    ccf_metrics = _metrics(ccf_actual, ccf_prediction)
    segments = _segment(
        "amortized_ead",
        [item.product_code for item in amortized.records],
        amortized_actual,
        amortized_prediction,
    ) + _segment(
        "revolving_ccf",
        [f"{item.product_code}:{item.horizon_months}m" for item in validation_rows],
        ccf_actual,
        ccf_prediction,
    )
    temporal = _temporal(
        "amortized_ead",
        [item.default_date.year for item in amortized.records],
        amortized_actual,
        amortized_prediction,
    ) + _temporal(
        "revolving_ccf",
        [item.default_date.year for item in validation_rows],
        ccf_actual,
        ccf_prediction,
    )
    sensitivities = (
        *_ccf_sensitivity(
            ccf_model, validation_rows[0], validation_policy.minimum_sensitivity_delta
        ),
        _limit_sensitivity(off_balance_policy, validation_policy.minimum_sensitivity_delta),
    )
    blockers: list[str] = []
    if amortized_metrics.observations < validation_policy.minimum_amortized_observations:
        blockers.append("amortized_sample_below_minimum")
    if (
        Decimal(str(amortized_metrics.mean_absolute_error))
        > validation_policy.maximum_amortized_mae
    ):
        blockers.append("amortized_mae_above_limit")
    if ccf_metrics.observations < validation_policy.minimum_ccf_validation_observations:
        blockers.append("ccf_validation_sample_below_minimum")
    if Decimal(str(ccf_metrics.mean_absolute_error)) > validation_policy.maximum_ccf_mae:
        blockers.append("ccf_mae_above_limit")
    if Decimal(str(ccf_metrics.root_mean_squared_error)) > validation_policy.maximum_ccf_rmse:
        blockers.append("ccf_rmse_above_limit")
    if any(item.observations < validation_policy.minimum_segment_observations for item in segments):
        blockers.append("segment_sample_below_minimum")
    ccf_years = {item.default_date.year for item in validation_rows}
    if len(ccf_years) < validation_policy.minimum_ccf_validation_years:
        blockers.append("ccf_temporal_coverage_below_minimum")
    if validation_policy.require_limit_change_validation and not any(
        item.limit_status in {"reduced", "cancelled"} for item in validation_rows
    ):
        blockers.append("no_limit_change_in_validation")
    if any(not item.responsive for item in sensitivities):
        blockers.append("sensitivity_not_responsive")
    if ccf_model.status != "approved":
        blockers.append("ccf_model_not_approved")
    if off_balance_policy.evidence_status != "institutionally_validated":
        blockers.append("off_balance_parameters_not_estimated")
    if (
        validation_policy.require_institutional_evidence
        and validation_policy.evidence_status != "institutionally_validated"
    ):
        blockers.append("validation_evidence_not_institutionally_validated")
    return EADValidationReport(
        amortized_metrics,
        ccf_metrics,
        segments,
        temporal,
        sensitivities,
        "not_approved" if blockers else "approved",
        tuple(blockers),
        validation_policy.policy_version,
        validation_policy.sha256,
    )
