"""Independent EAD and CCF backtesting over frozen predictions."""

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

DEFAULT_EAD_BACKTEST_POLICY = Path("config/validation/backtesting/ead-2026.07.1.json")


class EADBacktestDecision(StrEnum):
    PASSED = "passed"
    PASSED_WITH_RESERVATIONS = "passed_with_reservations"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class EADBacktestObservation:
    observation_id: str
    component: str
    product: str
    predicted_ead: Decimal
    actual_ead: Decimal
    utilization_band: str
    predicted_ccf: Decimal | None = None
    actual_ccf: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.observation_id or not self.product or not self.utilization_band:
            raise DomainValidationError("EAD backtest identifiers must be non-empty")
        if self.component not in {"amortized", "revolving"}:
            raise DomainValidationError("EAD component must be amortized or revolving")
        if self.predicted_ead < 0 or self.actual_ead < 0:
            raise DomainValidationError("EAD values cannot be negative")
        if self.component == "revolving" and (
            self.predicted_ccf is None or self.actual_ccf is None
        ):
            raise DomainValidationError(
                "revolving EAD observations require predicted and actual CCF"
            )
        if self.component == "amortized" and (
            self.predicted_ccf is not None or self.actual_ccf is not None
        ):
            raise DomainValidationError("amortized EAD observations cannot carry CCF")
        for value in (self.predicted_ccf, self.actual_ccf):
            if value is not None and not Decimal("0") <= value <= Decimal("1"):
                raise DomainValidationError("CCF values must be between zero and one")


@dataclass(frozen=True, slots=True)
class EADBacktestPolicy:
    version: str
    minimum_amortized_observations: int
    maximum_amortized_ead_mae: Decimal
    minimum_revolving_observations: int
    minimum_segment_observations: int
    maximum_revolving_ead_relative_mae: Decimal
    maximum_ccf_mae: Decimal
    maximum_ccf_rmse: Decimal
    required_revolving_dimensions: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class EADBacktestMetric:
    component: str
    dimension: str
    value: str
    observations: int
    mean_predicted_ead: Decimal
    mean_actual_ead: Decimal
    ead_mae: Decimal
    ead_rmse: Decimal
    ead_relative_mae: Decimal | None
    mean_predicted_ccf: Decimal | None
    mean_actual_ccf: Decimal | None
    ccf_mae: Decimal | None
    ccf_rmse: Decimal | None
    minimum_observations_met: bool
    error_limits_met: bool
    passed: bool


@dataclass(frozen=True, slots=True)
class EADBacktestReport:
    model_id: str
    model_version: str
    policy_version: str
    policy_hash: str
    evidence_hash: str
    metrics: tuple[EADBacktestMetric, ...]
    decision: EADBacktestDecision
    decision_reasons: tuple[str, ...]
    report_hash: str
    excluded_components: tuple[str, ...] = ("off_balance_without_realized_history",)
    evidence_scope: str = "synthetic_independent_backtest"


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def load_ead_backtest_policy(path: Path = DEFAULT_EAD_BACKTEST_POLICY) -> EADBacktestPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "version",
        "minimum_amortized_observations",
        "maximum_amortized_ead_mae",
        "minimum_revolving_observations",
        "minimum_segment_observations",
        "maximum_revolving_ead_relative_mae",
        "maximum_ccf_mae",
        "maximum_ccf_rmse",
        "required_revolving_dimensions",
    }
    if set(payload) != expected:
        raise DomainValidationError("EAD backtest policy has missing or unknown fields")
    if not isinstance(payload["version"], str) or not payload["version"]:
        raise DomainValidationError("EAD backtest policy requires a version")
    integer_fields = (
        "minimum_amortized_observations",
        "minimum_revolving_observations",
        "minimum_segment_observations",
    )
    if any(
        isinstance(payload[name], bool) or not isinstance(payload[name], int) or payload[name] < 1
        for name in integer_fields
    ):
        raise DomainValidationError("EAD backtest sample minima must be positive integers")
    limits = tuple(
        Decimal(str(payload[name]))
        for name in (
            "maximum_amortized_ead_mae",
            "maximum_revolving_ead_relative_mae",
            "maximum_ccf_mae",
            "maximum_ccf_rmse",
        )
    )
    if any(item <= 0 for item in limits):
        raise DomainValidationError("EAD backtest error limits must be positive")
    dimensions = payload["required_revolving_dimensions"]
    if (
        not isinstance(dimensions, list)
        or not dimensions
        or any(not isinstance(item, str) or not item for item in dimensions)
        or len(dimensions) != len(set(dimensions))
    ):
        raise DomainValidationError("EAD backtest dimensions must be unique strings")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return EADBacktestPolicy(
        payload["version"],
        payload["minimum_amortized_observations"],
        limits[0],
        payload["minimum_revolving_observations"],
        payload["minimum_segment_observations"],
        limits[1],
        limits[2],
        limits[3],
        tuple(dimensions),
        digest,
    )


def _rmse(errors: tuple[Decimal, ...]) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        return (sum((item * item for item in errors), Decimal("0")) / len(errors)).sqrt()


def _metric(
    rows: tuple[EADBacktestObservation, ...],
    dimension: str,
    value: str,
    minimum: int,
    policy: EADBacktestPolicy,
) -> EADBacktestMetric:
    component = rows[0].component
    count = len(rows)
    ead_errors = tuple(item.predicted_ead - item.actual_ead for item in rows)
    ead_mae = sum((abs(item) for item in ead_errors), Decimal("0")) / count
    ead_rmse = _rmse(ead_errors)
    mean_actual_ead = sum((item.actual_ead for item in rows), Decimal("0")) / count
    ead_relative_mae = ead_mae / mean_actual_ead if mean_actual_ead else None
    predicted_ccf: Decimal | None = None
    actual_ccf: Decimal | None = None
    ccf_mae: Decimal | None = None
    ccf_rmse: Decimal | None = None
    if component == "revolving":
        predicted_values = tuple(
            item.predicted_ccf for item in rows if item.predicted_ccf is not None
        )
        actual_values = tuple(item.actual_ccf for item in rows if item.actual_ccf is not None)
        if len(predicted_values) != count or len(actual_values) != count:
            raise DomainValidationError("revolving CCF evidence is incomplete")
        ccf_errors = tuple(
            predicted - actual
            for predicted, actual in zip(predicted_values, actual_values, strict=True)
        )
        predicted_ccf = sum(predicted_values, Decimal("0")) / count
        actual_ccf = sum(actual_values, Decimal("0")) / count
        ccf_mae = sum((abs(item) for item in ccf_errors), Decimal("0")) / count
        ccf_rmse = _rmse(ccf_errors)
    enough = count >= minimum
    error_limits_met = (
        ead_mae <= policy.maximum_amortized_ead_mae
        if component == "amortized"
        else ccf_mae is not None
        and ccf_rmse is not None
        and ead_relative_mae is not None
        and ead_relative_mae <= policy.maximum_revolving_ead_relative_mae
        and ccf_mae <= policy.maximum_ccf_mae
        and ccf_rmse <= policy.maximum_ccf_rmse
    )
    return EADBacktestMetric(
        component,
        dimension,
        value,
        count,
        sum((item.predicted_ead for item in rows), Decimal("0")) / count,
        mean_actual_ead,
        ead_mae,
        ead_rmse,
        ead_relative_mae,
        predicted_ccf,
        actual_ccf,
        ccf_mae,
        ccf_rmse,
        enough,
        error_limits_met,
        enough and error_limits_met,
    )


def backtest_ead(
    model_id: str,
    model_version: str,
    observations: tuple[EADBacktestObservation, ...],
    policy: EADBacktestPolicy | None = None,
) -> EADBacktestReport:
    """Compare frozen balance/drawdown predictions with realized EAD and CCF."""
    if not model_id or not model_version or not observations:
        raise DomainValidationError("EAD backtest requires model identity and evidence")
    identifiers = [item.observation_id for item in observations]
    if len(identifiers) != len(set(identifiers)):
        raise DomainValidationError("EAD backtest evidence must be unique")
    amortized = tuple(item for item in observations if item.component == "amortized")
    revolving = tuple(item for item in observations if item.component == "revolving")
    if not amortized or not revolving:
        raise DomainValidationError("EAD backtest requires amortized and revolving evidence")
    selected = policy or load_ead_backtest_policy()
    metrics = [
        _metric(
            amortized,
            "aggregate",
            "all",
            selected.minimum_amortized_observations,
            selected,
        ),
        _metric(
            revolving,
            "aggregate",
            "all",
            selected.minimum_revolving_observations,
            selected,
        ),
    ]
    for product in sorted({item.product for item in amortized}):
        group = tuple(item for item in amortized if item.product == product)
        metrics.append(
            _metric(
                group,
                "product",
                product,
                selected.minimum_segment_observations,
                selected,
            )
        )
    accessors: dict[str, Callable[[EADBacktestObservation], str]] = {
        "product": lambda item: item.product,
        "utilization_band": lambda item: item.utilization_band,
    }
    unknown = set(selected.required_revolving_dimensions) - set(accessors)
    if unknown:
        raise DomainValidationError(f"unsupported EAD dimensions: {sorted(unknown)}")
    for dimension in selected.required_revolving_dimensions:
        accessor = accessors[dimension]
        for value in sorted({accessor(item) for item in revolving}):
            group = tuple(item for item in revolving if accessor(item) == value)
            metrics.append(
                _metric(
                    group,
                    dimension,
                    value,
                    selected.minimum_segment_observations,
                    selected,
                )
            )
    reasons = []
    for aggregate in metrics[:2]:
        if not aggregate.minimum_observations_met:
            reasons.append(f"{aggregate.component} sample below objective minimum")
        if not aggregate.error_limits_met:
            reasons.append(f"{aggregate.component} error exceeds objective limit")
    if reasons:
        decision = EADBacktestDecision.REJECTED
    elif any(not item.passed for item in metrics[2:]):
        decision = EADBacktestDecision.PASSED_WITH_RESERVATIONS
        reasons.append("one or more product/utilization cells fail volume or error criteria")
    else:
        decision = EADBacktestDecision.PASSED
        reasons.append("aggregate and segment criteria passed")
    ordered = tuple(sorted(observations, key=lambda item: item.observation_id))
    evidence_hash = hashlib.sha256(_canonical([asdict(item) for item in ordered])).hexdigest()
    payload = {
        "model_id": model_id,
        "model_version": model_version,
        "policy_version": selected.version,
        "policy_hash": selected.policy_hash,
        "evidence_hash": evidence_hash,
        "metrics": [asdict(item) for item in metrics],
        "decision": decision,
        "decision_reasons": reasons,
        "excluded_components": ["off_balance_without_realized_history"],
        "evidence_scope": "synthetic_independent_backtest",
    }
    report_hash = hashlib.sha256(_canonical(payload)).hexdigest()
    return EADBacktestReport(
        model_id,
        model_version,
        selected.version,
        selected.policy_hash,
        evidence_hash,
        tuple(metrics),
        decision,
        tuple(reasons),
        report_hash,
    )


def render_ead_backtest_report(report: EADBacktestReport) -> str:
    lines = [
        f"# Independent EAD/CCF backtest — {report.model_id}",
        "",
        f"- Model version: `{report.model_version}`",
        f"- Policy: `{report.policy_version}` (`{report.policy_hash}`)",
        f"- Evidence hash: `{report.evidence_hash}`",
        f"- Decision: **{report.decision.value}**",
        f"- Report hash: `{report.report_hash}`",
        f"- Excluded: `{', '.join(report.excluded_components)}`",
        "",
        "| Component | Dimension | Value | N | Predicted EAD | Actual EAD | EAD MAE | "
        "EAD relative MAE | Predicted CCF | Actual CCF | CCF MAE | CCF RMSE | Pass |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in report.metrics:
        ccf_values = tuple(
            "NA" if value is None else str(value)
            for value in (
                item.mean_predicted_ccf,
                item.mean_actual_ccf,
                item.ccf_mae,
                item.ccf_rmse,
            )
        )
        lines.append(
            f"| {item.component} | {item.dimension} | {item.value} | "
            f"{item.observations} | {item.mean_predicted_ead} | {item.mean_actual_ead} | "
            f"{item.ead_mae} | {item.ead_relative_mae} | {ccf_values[0]} | "
            f"{ccf_values[1]} | {ccf_values[2]} | "
            f"{ccf_values[3]} | {str(item.passed).lower()} |"
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
