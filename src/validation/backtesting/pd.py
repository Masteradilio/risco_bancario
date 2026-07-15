"""Independent PD backtesting over frozen predictions and mature outcomes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any

from scipy.stats import binomtest  # type: ignore[import-untyped]

from ...domain.exceptions import DomainValidationError

DEFAULT_PD_BACKTEST_POLICY = Path("config/validation/backtesting/pd-2026.07.1.json")


class PDBacktestDecision(StrEnum):
    PASSED = "passed"
    PASSED_WITH_RESERVATIONS = "passed_with_reservations"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class PDBacktestObservation:
    observation_id: str
    observation_date: date
    horizon_months: int
    predicted_pd: Decimal
    observed_default: int
    rating: str
    product: str
    vintage: str
    split: str

    def __post_init__(self) -> None:
        if not all((self.observation_id, self.rating, self.product, self.vintage, self.split)):
            raise DomainValidationError("PD backtest observation identifiers must be non-empty")
        if self.horizon_months < 1:
            raise DomainValidationError("PD backtest horizon must be positive")
        if not Decimal("0") <= self.predicted_pd <= Decimal("1"):
            raise DomainValidationError("predicted PD must be between zero and one")
        if self.observed_default not in (0, 1):
            raise DomainValidationError("observed default must be binary")


@dataclass(frozen=True, slots=True)
class PDBacktestPolicy:
    version: str
    alpha: Decimal
    minimum_aggregate_observations: int
    minimum_segment_observations: int
    maximum_absolute_calibration_error: Decimal
    maximum_calibration_drift: Decimal
    required_horizons_months: tuple[int, ...]
    required_dimensions: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class PDCoverageMetric:
    horizon_months: int
    dimension: str
    value: str
    row_count: int
    event_count: int
    mean_prediction: Decimal
    observed_rate: Decimal
    observed_to_expected: Decimal | None
    absolute_calibration_error: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal
    exact_p_value: Decimal
    minimum_observations_met: bool
    prediction_inside_interval: bool
    calibration_limit_met: bool
    coverage_passed: bool


@dataclass(frozen=True, slots=True)
class PDCalibrationDrift:
    horizon_months: int
    reference_absolute_error: Decimal
    evaluation_absolute_error: Decimal
    error_change: Decimal
    limit: Decimal
    passed: bool


@dataclass(frozen=True, slots=True)
class PDBacktestReport:
    model_id: str
    model_version: str
    reference_split: str
    evaluation_split: str
    policy_version: str
    policy_hash: str
    evidence_hash: str
    metrics: tuple[PDCoverageMetric, ...]
    calibration_drift: tuple[PDCalibrationDrift, ...]
    unlabeled_future_observations: int
    decision: PDBacktestDecision
    decision_reasons: tuple[str, ...]
    report_hash: str
    evidence_scope: str = "synthetic_independent_backtest"


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def load_pd_backtest_policy(path: Path = DEFAULT_PD_BACKTEST_POLICY) -> PDBacktestPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "version",
        "alpha",
        "minimum_aggregate_observations",
        "minimum_segment_observations",
        "maximum_absolute_calibration_error",
        "maximum_calibration_drift",
        "required_horizons_months",
        "required_dimensions",
    }
    if set(payload) != expected:
        raise DomainValidationError("PD backtest policy has missing or unknown fields")
    if not isinstance(payload["version"], str) or not payload["version"]:
        raise DomainValidationError("PD backtest policy requires a version")
    integer_fields = ("minimum_aggregate_observations", "minimum_segment_observations")
    if any(
        isinstance(payload[name], bool) or not isinstance(payload[name], int) or payload[name] < 1
        for name in integer_fields
    ):
        raise DomainValidationError("PD backtest observation minima must be positive integers")
    alpha = Decimal(str(payload["alpha"]))
    calibration_limit = Decimal(str(payload["maximum_absolute_calibration_error"]))
    drift_limit = Decimal(str(payload["maximum_calibration_drift"]))
    if not Decimal("0") < alpha < Decimal("1"):
        raise DomainValidationError("PD backtest alpha must be between zero and one")
    if calibration_limit < 0 or drift_limit < 0:
        raise DomainValidationError("PD backtest limits cannot be negative")
    horizons = payload["required_horizons_months"]
    dimensions = payload["required_dimensions"]
    if (
        not isinstance(horizons, list)
        or not horizons
        or any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in horizons)
        or len(horizons) != len(set(horizons))
    ):
        raise DomainValidationError("required PD horizons must be unique positive integers")
    if (
        not isinstance(dimensions, list)
        or not dimensions
        or any(not isinstance(item, str) or not item for item in dimensions)
        or len(dimensions) != len(set(dimensions))
    ):
        raise DomainValidationError("required PD dimensions must be unique strings")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return PDBacktestPolicy(
        payload["version"],
        alpha,
        payload["minimum_aggregate_observations"],
        payload["minimum_segment_observations"],
        calibration_limit,
        drift_limit,
        tuple(horizons),
        tuple(dimensions),
        digest,
    )


def _metric(
    rows: tuple[PDBacktestObservation, ...],
    horizon: int,
    dimension: str,
    value: str,
    minimum_observations: int,
    policy: PDBacktestPolicy,
) -> PDCoverageMetric:
    count = len(rows)
    events = sum(item.observed_default for item in rows)
    prediction = sum((item.predicted_pd for item in rows), Decimal("0")) / count
    observed = Decimal(events) / count
    test = binomtest(events, count, float(prediction))
    interval = test.proportion_ci(confidence_level=1 - float(policy.alpha), method="exact")
    lower = Decimal(str(interval.low))
    upper = Decimal(str(interval.high))
    error = abs(observed - prediction)
    enough = count >= minimum_observations
    inside = lower <= prediction <= upper
    calibration_ok = error <= policy.maximum_absolute_calibration_error
    return PDCoverageMetric(
        horizon,
        dimension,
        value,
        count,
        events,
        prediction,
        observed,
        observed / prediction if prediction else None,
        error,
        lower,
        upper,
        Decimal(str(test.pvalue)),
        enough,
        inside,
        calibration_ok,
        enough and inside and calibration_ok,
    )


def _group_metrics(
    rows: tuple[PDBacktestObservation, ...], policy: PDBacktestPolicy
) -> tuple[PDCoverageMetric, ...]:
    accessors: dict[str, Callable[[PDBacktestObservation], str]] = {
        "rating": lambda row: row.rating,
        "product": lambda row: row.product,
        "vintage": lambda row: row.vintage,
    }
    unknown = set(policy.required_dimensions) - set(accessors)
    if unknown:
        raise DomainValidationError(f"unsupported PD dimensions: {sorted(unknown)}")
    metrics: list[PDCoverageMetric] = []
    for horizon in policy.required_horizons_months:
        horizon_rows = tuple(item for item in rows if item.horizon_months == horizon)
        if not horizon_rows:
            raise DomainValidationError(f"required PD horizon is absent: {horizon}")
        metrics.append(
            _metric(
                horizon_rows,
                horizon,
                "aggregate",
                "all",
                policy.minimum_aggregate_observations,
                policy,
            )
        )
        for dimension in policy.required_dimensions:
            accessor = accessors[dimension]
            for value in sorted({accessor(item) for item in horizon_rows}):
                group = tuple(item for item in horizon_rows if accessor(item) == value)
                metrics.append(
                    _metric(
                        group,
                        horizon,
                        dimension,
                        value,
                        policy.minimum_segment_observations,
                        policy,
                    )
                )
    return tuple(metrics)


def backtest_pd(
    model_id: str,
    model_version: str,
    reference: tuple[PDBacktestObservation, ...],
    evaluation: tuple[PDBacktestObservation, ...],
    *,
    unlabeled_future_observations: int = 0,
    policy: PDBacktestPolicy | None = None,
) -> PDBacktestReport:
    """Calculate PD performance without fitting or modifying the submitted model."""
    if not model_id or not model_version:
        raise DomainValidationError("PD backtest requires model identity and version")
    if not reference or not evaluation:
        raise DomainValidationError("PD backtest requires reference and evaluation evidence")
    if unlabeled_future_observations < 0:
        raise DomainValidationError("unlabeled observation count cannot be negative")
    selected = policy or load_pd_backtest_policy()
    reference_splits = {item.split for item in reference}
    evaluation_splits = {item.split for item in evaluation}
    if len(reference_splits) != 1 or len(evaluation_splits) != 1:
        raise DomainValidationError("reference and evaluation must each contain one split")
    if reference_splits == evaluation_splits:
        raise DomainValidationError("reference and evaluation splits must differ")
    evidence_keys = [
        (item.observation_id, item.horizon_months, item.split) for item in (*reference, *evaluation)
    ]
    if len(evidence_keys) != len(set(evidence_keys)):
        raise DomainValidationError("PD backtest evidence contains duplicate observations")
    reference_metrics = _group_metrics(reference, selected)
    metrics = _group_metrics(evaluation, selected)
    evidence_payload = {
        "reference": [
            asdict(item)
            for item in sorted(reference, key=lambda row: (row.horizon_months, row.observation_id))
        ],
        "evaluation": [
            asdict(item)
            for item in sorted(evaluation, key=lambda row: (row.horizon_months, row.observation_id))
        ],
    }
    evidence_hash = hashlib.sha256(_canonical(evidence_payload)).hexdigest()
    reference_aggregate = {
        item.horizon_months: item for item in reference_metrics if item.dimension == "aggregate"
    }
    aggregate = {item.horizon_months: item for item in metrics if item.dimension == "aggregate"}
    drift = tuple(
        PDCalibrationDrift(
            horizon,
            reference_aggregate[horizon].absolute_calibration_error,
            aggregate[horizon].absolute_calibration_error,
            aggregate[horizon].absolute_calibration_error
            - reference_aggregate[horizon].absolute_calibration_error,
            selected.maximum_calibration_drift,
            aggregate[horizon].absolute_calibration_error
            - reference_aggregate[horizon].absolute_calibration_error
            <= selected.maximum_calibration_drift,
        )
        for horizon in selected.required_horizons_months
    )
    reasons: list[str] = []
    failed_aggregate = [
        str(item.horizon_months) for item in aggregate.values() if not item.coverage_passed
    ]
    failed_drift = [str(item.horizon_months) for item in drift if not item.passed]
    if failed_aggregate:
        reasons.append(f"aggregate coverage failed at horizons: {','.join(failed_aggregate)}")
    if failed_drift:
        reasons.append(f"calibration drift exceeded at horizons: {','.join(failed_drift)}")
    if reasons:
        decision = PDBacktestDecision.REJECTED
    else:
        segment_failures = sum(
            not item.coverage_passed for item in metrics if item.dimension != "aggregate"
        )
        if segment_failures or unlabeled_future_observations:
            decision = PDBacktestDecision.PASSED_WITH_RESERVATIONS
            reasons.append(f"segment cells requiring attention: {segment_failures}")
            if unlabeled_future_observations:
                reasons.append(
                    "future observations awaiting target maturation: "
                    f"{unlabeled_future_observations}"
                )
        else:
            decision = PDBacktestDecision.PASSED
            reasons.append("aggregate, segment and drift criteria passed")
    payload = {
        "model_id": model_id,
        "model_version": model_version,
        "reference_split": next(iter(reference_splits)),
        "evaluation_split": next(iter(evaluation_splits)),
        "policy_version": selected.version,
        "policy_hash": selected.policy_hash,
        "evidence_hash": evidence_hash,
        "metrics": [asdict(item) for item in metrics],
        "calibration_drift": [asdict(item) for item in drift],
        "unlabeled_future_observations": unlabeled_future_observations,
        "decision": decision,
        "decision_reasons": reasons,
        "evidence_scope": "synthetic_independent_backtest",
    }
    report_hash = hashlib.sha256(_canonical(payload)).hexdigest()
    return PDBacktestReport(
        model_id,
        model_version,
        next(iter(reference_splits)),
        next(iter(evaluation_splits)),
        selected.version,
        selected.policy_hash,
        evidence_hash,
        metrics,
        drift,
        unlabeled_future_observations,
        decision,
        tuple(reasons),
        report_hash,
    )


def render_pd_backtest_report(report: PDBacktestReport) -> str:
    lines = [
        f"# Independent PD backtest — {report.model_id}",
        "",
        f"- Model version: `{report.model_version}`",
        f"- Reference/evaluation: `{report.reference_split}` / `{report.evaluation_split}`",
        f"- Policy: `{report.policy_version}` (`{report.policy_hash}`)",
        f"- Evidence hash: `{report.evidence_hash}`",
        f"- Decision: **{report.decision.value}**",
        f"- Report hash: `{report.report_hash}`",
        f"- Evidence scope: `{report.evidence_scope}`",
        f"- Future observations without mature targets: `{report.unlabeled_future_observations}`",
        "",
        "## Predicted versus observed and coverage",
        "",
        "| Horizon | Dimension | Value | N | Events | Predicted | Observed | O/E | "
        "Confidence interval | p-value | Pass |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for item in report.metrics:
        ratio = "NA" if item.observed_to_expected is None else str(item.observed_to_expected)
        lines.append(
            f"| {item.horizon_months} | {item.dimension} | {item.value} | {item.row_count} | "
            f"{item.event_count} | {item.mean_prediction} | {item.observed_rate} | {ratio} | "
            f"[{item.confidence_lower}, {item.confidence_upper}] | {item.exact_p_value} | "
            f"{str(item.coverage_passed).lower()} |"
        )
    lines.extend(["", "## Calibration drift", ""])
    for drift_item in report.calibration_drift:
        lines.append(
            f"- {drift_item.horizon_months}m: reference error "
            f"`{drift_item.reference_absolute_error}`, evaluation error "
            f"`{drift_item.evaluation_absolute_error}`, change `{drift_item.error_change}`, "
            f"passed `{str(drift_item.passed).lower()}`."
        )
    lines.extend(["", "## Decision reasons", ""])
    lines.extend(f"- {reason}" for reason in report.decision_reasons)
    lines.extend(
        [
            "",
            "> Synthetic retrospective validation evidence; not institutional model approval.",
            "",
        ]
    )
    return "\n".join(lines)
