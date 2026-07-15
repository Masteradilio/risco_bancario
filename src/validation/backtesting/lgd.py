"""Independent LGD backtesting over frozen predictions and workout evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext
from enum import StrEnum
from pathlib import Path
from typing import Any

from ...domain.exceptions import DomainValidationError

DEFAULT_LGD_BACKTEST_POLICY = Path("config/validation/backtesting/lgd-2026.07.1.json")


class LGDBacktestDecision(StrEnum):
    PASSED = "passed"
    PASSED_WITH_RESERVATIONS = "passed_with_reservations"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class LGDBacktestObservation:
    default_id: str
    cohort: str
    product: str
    exposure_at_default: Decimal
    predicted_lgd: Decimal | None
    actual_lgd: Decimal | None
    discounted_net_recovery: Decimal
    cohort_status: str
    cured: bool
    writeoff_amount: Decimal
    collateral_present: bool

    def __post_init__(self) -> None:
        if not all((self.default_id, self.cohort, self.product)):
            raise DomainValidationError("LGD backtest identifiers must be non-empty")
        if self.exposure_at_default <= 0:
            raise DomainValidationError("LGD backtest EAD must be positive")
        if self.writeoff_amount < 0:
            raise DomainValidationError("LGD write-off amount cannot be negative")
        if self.cohort_status not in {"closed", "open"}:
            raise DomainValidationError("LGD cohort status must be closed or open")
        for name, value in (("predicted_lgd", self.predicted_lgd), ("actual_lgd", self.actual_lgd)):
            if value is not None and not Decimal("0") <= value <= Decimal("1"):
                raise DomainValidationError(f"{name} must be between zero and one")
        if self.cohort_status == "closed" and (
            self.predicted_lgd is None or self.actual_lgd is None
        ):
            raise DomainValidationError("closed LGD observations require prediction and outcome")
        if self.cohort_status == "open" and self.actual_lgd is not None:
            raise DomainValidationError("open LGD observations cannot carry final realized LGD")


@dataclass(frozen=True, slots=True)
class LGDBacktestPolicy:
    version: str
    minimum_closed_observations: int
    minimum_segment_observations: int
    maximum_mae: Decimal
    maximum_rmse: Decimal
    required_dimensions: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class LGDClosedMetric:
    dimension: str
    value: str
    observations: int
    mean_predicted_lgd: Decimal
    mean_actual_lgd: Decimal
    mean_absolute_error: Decimal
    root_mean_squared_error: Decimal
    predicted_recovery: Decimal
    realized_recovery: Decimal
    recovery_error: Decimal
    minimum_observations_met: bool
    error_limits_met: bool
    passed: bool


@dataclass(frozen=True, slots=True)
class LGDOpenCohort:
    cohort: str
    observations: int
    exposure_at_default: Decimal
    recovery_to_date: Decimal
    cures: int
    writeoffs: int
    collateralized: int
    predictions_available: int
    performance_status: str = "not_scored_until_workout_closure"


@dataclass(frozen=True, slots=True)
class LGDBacktestReport:
    model_id: str
    model_version: str
    policy_version: str
    policy_hash: str
    evidence_hash: str
    closed_metrics: tuple[LGDClosedMetric, ...]
    open_cohorts: tuple[LGDOpenCohort, ...]
    decision: LGDBacktestDecision
    decision_reasons: tuple[str, ...]
    report_hash: str
    evidence_scope: str = "synthetic_independent_backtest"


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def load_lgd_backtest_policy(path: Path = DEFAULT_LGD_BACKTEST_POLICY) -> LGDBacktestPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "version",
        "minimum_closed_observations",
        "minimum_segment_observations",
        "maximum_mae",
        "maximum_rmse",
        "required_dimensions",
    }
    if set(payload) != expected:
        raise DomainValidationError("LGD backtest policy has missing or unknown fields")
    if not isinstance(payload["version"], str) or not payload["version"]:
        raise DomainValidationError("LGD backtest policy requires a version")
    for field in ("minimum_closed_observations", "minimum_segment_observations"):
        value = payload[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise DomainValidationError("LGD backtest sample minima must be positive integers")
    mae = Decimal(str(payload["maximum_mae"]))
    rmse = Decimal(str(payload["maximum_rmse"]))
    if mae <= 0 or rmse <= 0:
        raise DomainValidationError("LGD backtest error limits must be positive")
    dimensions = payload["required_dimensions"]
    if (
        not isinstance(dimensions, list)
        or not dimensions
        or any(not isinstance(item, str) or not item for item in dimensions)
        or len(dimensions) != len(set(dimensions))
    ):
        raise DomainValidationError("LGD backtest dimensions must be unique strings")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return LGDBacktestPolicy(
        payload["version"],
        payload["minimum_closed_observations"],
        payload["minimum_segment_observations"],
        mae,
        rmse,
        tuple(dimensions),
        digest,
    )


def _outcome(row: LGDBacktestObservation) -> str:
    if row.cured:
        return "cure"
    if row.writeoff_amount > 0:
        return "writeoff"
    return "other"


def _metric(
    rows: tuple[LGDBacktestObservation, ...],
    dimension: str,
    value: str,
    minimum: int,
    policy: LGDBacktestPolicy,
) -> LGDClosedMetric:
    predicted = tuple(item.predicted_lgd for item in rows)
    actual = tuple(item.actual_lgd for item in rows)
    if any(item is None for item in (*predicted, *actual)):
        raise DomainValidationError("closed LGD metric received incomplete outcomes")
    predicted_values = tuple(item for item in predicted if item is not None)
    actual_values = tuple(item for item in actual if item is not None)
    count = len(rows)
    errors = tuple(
        pred - observed for pred, observed in zip(predicted_values, actual_values, strict=True)
    )
    mae = sum((abs(item) for item in errors), Decimal("0")) / count
    with localcontext() as context:
        context.prec = 28
        rmse = (sum((item * item for item in errors), Decimal("0")) / count).sqrt()
    predicted_recovery = sum(
        (
            item.exposure_at_default * (Decimal("1") - prediction)
            for item, prediction in zip(rows, predicted_values, strict=True)
        ),
        Decimal("0"),
    )
    realized_recovery = sum((item.discounted_net_recovery for item in rows), Decimal("0"))
    enough = count >= minimum
    errors_ok = mae <= policy.maximum_mae and rmse <= policy.maximum_rmse
    return LGDClosedMetric(
        dimension,
        value,
        count,
        sum(predicted_values, Decimal("0")) / count,
        sum(actual_values, Decimal("0")) / count,
        mae,
        rmse,
        predicted_recovery,
        realized_recovery,
        predicted_recovery - realized_recovery,
        enough,
        errors_ok,
        enough and errors_ok,
    )


def _closed_metrics(
    rows: tuple[LGDBacktestObservation, ...], policy: LGDBacktestPolicy
) -> tuple[LGDClosedMetric, ...]:
    accessors: dict[str, Callable[[LGDBacktestObservation], str]] = {
        "cohort": lambda item: item.cohort,
        "outcome": _outcome,
        "collateral": lambda item: (
            "with_collateral" if item.collateral_present else "without_collateral"
        ),
    }
    unknown = set(policy.required_dimensions) - set(accessors)
    if unknown:
        raise DomainValidationError(f"unsupported LGD dimensions: {sorted(unknown)}")
    metrics = [_metric(rows, "aggregate", "all", policy.minimum_closed_observations, policy)]
    for dimension in policy.required_dimensions:
        accessor = accessors[dimension]
        for value in sorted({accessor(item) for item in rows}):
            group = tuple(item for item in rows if accessor(item) == value)
            metrics.append(
                _metric(group, dimension, value, policy.minimum_segment_observations, policy)
            )
    return tuple(metrics)


def _open_cohorts(rows: tuple[LGDBacktestObservation, ...]) -> tuple[LGDOpenCohort, ...]:
    result = []
    for cohort in sorted({item.cohort for item in rows}):
        group = tuple(item for item in rows if item.cohort == cohort)
        result.append(
            LGDOpenCohort(
                cohort,
                len(group),
                sum((item.exposure_at_default for item in group), Decimal("0")),
                sum((item.discounted_net_recovery for item in group), Decimal("0")),
                sum(item.cured for item in group),
                sum(item.writeoff_amount > 0 for item in group),
                sum(item.collateral_present for item in group),
                sum(item.predicted_lgd is not None for item in group),
            )
        )
    return tuple(result)


def backtest_lgd(
    model_id: str,
    model_version: str,
    observations: tuple[LGDBacktestObservation, ...],
    policy: LGDBacktestPolicy | None = None,
) -> LGDBacktestReport:
    """Backtest closed workouts and inventory open cohorts without treating them as final."""
    if not model_id or not model_version or not observations:
        raise DomainValidationError("LGD backtest requires model identity and evidence")
    identifiers = [item.default_id for item in observations]
    if len(identifiers) != len(set(identifiers)):
        raise DomainValidationError("LGD backtest default evidence must be unique")
    closed = tuple(item for item in observations if item.cohort_status == "closed")
    opened = tuple(item for item in observations if item.cohort_status == "open")
    if not closed or not opened:
        raise DomainValidationError("LGD backtest requires both closed and open cohorts")
    selected = policy or load_lgd_backtest_policy()
    metrics = _closed_metrics(closed, selected)
    open_cohorts = _open_cohorts(opened)
    aggregate = metrics[0]
    reasons: list[str] = []
    if not aggregate.minimum_observations_met:
        reasons.append("closed workout sample below objective minimum")
    if not aggregate.error_limits_met:
        reasons.append("aggregate MAE or RMSE exceeds objective limits")
    if reasons:
        decision = LGDBacktestDecision.REJECTED
    else:
        segment_failures = sum(not item.passed for item in metrics[1:])
        missing_open_predictions = sum(item.predictions_available == 0 for item in open_cohorts)
        if segment_failures or missing_open_predictions:
            decision = LGDBacktestDecision.PASSED_WITH_RESERVATIONS
            reasons.append(f"closed segment cells requiring attention: {segment_failures}")
            reasons.append(f"open cohorts without frozen predictions: {missing_open_predictions}")
        else:
            decision = LGDBacktestDecision.PASSED
            reasons.append("closed aggregate and segment criteria passed")
    ordered = tuple(sorted(observations, key=lambda item: item.default_id))
    evidence_hash = hashlib.sha256(_canonical([asdict(item) for item in ordered])).hexdigest()
    payload = {
        "model_id": model_id,
        "model_version": model_version,
        "policy_version": selected.version,
        "policy_hash": selected.policy_hash,
        "evidence_hash": evidence_hash,
        "closed_metrics": [asdict(item) for item in metrics],
        "open_cohorts": [asdict(item) for item in open_cohorts],
        "decision": decision,
        "decision_reasons": reasons,
        "evidence_scope": "synthetic_independent_backtest",
    }
    report_hash = hashlib.sha256(_canonical(payload)).hexdigest()
    return LGDBacktestReport(
        model_id,
        model_version,
        selected.version,
        selected.policy_hash,
        evidence_hash,
        metrics,
        open_cohorts,
        decision,
        tuple(reasons),
        report_hash,
    )


def render_lgd_backtest_report(report: LGDBacktestReport) -> str:
    lines = [
        f"# Independent LGD backtest — {report.model_id}",
        "",
        f"- Model version: `{report.model_version}`",
        f"- Policy: `{report.policy_version}` (`{report.policy_hash}`)",
        f"- Evidence hash: `{report.evidence_hash}`",
        f"- Decision: **{report.decision.value}**",
        f"- Report hash: `{report.report_hash}`",
        "",
        "## Closed workouts: predicted versus realized",
        "",
        "| Dimension | Value | N | Predicted LGD | Actual LGD | MAE | RMSE | "
        "Predicted recovery | Realized recovery | Pass |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in report.closed_metrics:
        lines.append(
            f"| {item.dimension} | {item.value} | {item.observations} | "
            f"{item.mean_predicted_lgd} | {item.mean_actual_lgd} | "
            f"{item.mean_absolute_error} | {item.root_mean_squared_error} | "
            f"{item.predicted_recovery} | {item.realized_recovery} | "
            f"{str(item.passed).lower()} |"
        )
    lines.extend(["", "## Open workout cohorts", ""])
    for open_item in report.open_cohorts:
        lines.append(
            f"- {open_item.cohort}: N `{open_item.observations}`, EAD "
            f"`{open_item.exposure_at_default}`, recovery to date "
            f"`{open_item.recovery_to_date}`, cures `{open_item.cures}`, "
            f"write-offs `{open_item.writeoffs}`, collateralized "
            f"`{open_item.collateralized}`, status `{open_item.performance_status}`."
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
