"""Independent ECL outcome backtesting and sequential attribution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any

from ...domain.exceptions import DomainValidationError

DEFAULT_ECL_BACKTEST_POLICY = Path("config/validation/backtesting/ecl-2026.07.1.json")


class ECLBacktestDecision(StrEnum):
    PASSED = "passed"
    PASSED_WITH_RESERVATIONS = "passed_with_reservations"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ECLAttributionPath:
    opening_ecl: Decimal
    steps: tuple[tuple[str, Decimal], ...]

    def __post_init__(self) -> None:
        if self.opening_ecl < 0 or not self.steps:
            raise DomainValidationError("ECL attribution requires non-negative opening and steps")
        if any(not component or value < 0 for component, value in self.steps):
            raise DomainValidationError("ECL attribution components and values are invalid")
        components = [component for component, _ in self.steps]
        if len(components) != len(set(components)):
            raise DomainValidationError("ECL attribution components must be unique")


@dataclass(frozen=True, slots=True)
class ECLBacktestObservation:
    observation_id: str
    initial_ecl: Decimal
    realized_loss: Decimal | None
    vintage: str
    economic_cycle: str
    attribution_path: ECLAttributionPath | None = None

    def __post_init__(self) -> None:
        if not all((self.observation_id, self.vintage, self.economic_cycle)):
            raise DomainValidationError("ECL backtest identifiers must be non-empty")
        if self.initial_ecl < 0 or (self.realized_loss is not None and self.realized_loss < 0):
            raise DomainValidationError("ECL and realized loss cannot be negative")
        if (
            self.attribution_path is not None
            and self.attribution_path.opening_ecl != self.initial_ecl
        ):
            raise DomainValidationError("ECL attribution opening must equal initial ECL")


@dataclass(frozen=True, slots=True)
class ECLBacktestPolicy:
    version: str
    minimum_mature_observations: int
    maximum_absolute_relative_bias: Decimal
    required_attribution_components: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class ECLOutcomeMetric:
    dimension: str
    value: str
    observations: int
    initial_ecl: Decimal
    realized_loss: Decimal
    bias: Decimal
    absolute_relative_bias: Decimal | None


@dataclass(frozen=True, slots=True)
class ECLAttribution:
    observation_id: str
    component: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class ECLBacktestReport:
    methodology_id: str
    methodology_version: str
    policy_version: str
    policy_hash: str
    evidence_hash: str
    total_observations: int
    mature_observations: int
    attribution_observations: int
    outcome_metrics: tuple[ECLOutcomeMetric, ...]
    attributions: tuple[ECLAttribution, ...]
    decision: ECLBacktestDecision
    decision_reasons: tuple[str, ...]
    report_hash: str
    evidence_scope: str = "synthetic_independent_backtest"


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def load_ecl_backtest_policy(path: Path = DEFAULT_ECL_BACKTEST_POLICY) -> ECLBacktestPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "version",
        "minimum_mature_observations",
        "maximum_absolute_relative_bias",
        "required_attribution_components",
    }
    if set(payload) != expected:
        raise DomainValidationError("ECL backtest policy has missing or unknown fields")
    if not isinstance(payload["version"], str) or not payload["version"]:
        raise DomainValidationError("ECL backtest policy requires a version")
    minimum = payload["minimum_mature_observations"]
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        raise DomainValidationError("ECL mature observation minimum must be a positive integer")
    bias_limit = Decimal(str(payload["maximum_absolute_relative_bias"]))
    if bias_limit <= 0:
        raise DomainValidationError("ECL bias limit must be positive")
    components = payload["required_attribution_components"]
    if (
        not isinstance(components, list)
        or not components
        or any(not isinstance(item, str) or not item for item in components)
        or len(components) != len(set(components))
    ):
        raise DomainValidationError("ECL attribution components must be unique strings")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return ECLBacktestPolicy(payload["version"], minimum, bias_limit, tuple(components), digest)


def _metric(
    rows: tuple[ECLBacktestObservation, ...], dimension: str, value: str
) -> ECLOutcomeMetric:
    initial = sum((item.initial_ecl for item in rows), Decimal("0"))
    realized = sum(
        (item.realized_loss for item in rows if item.realized_loss is not None), Decimal("0")
    )
    bias = initial - realized
    relative = abs(bias) / realized if realized else None
    return ECLOutcomeMetric(dimension, value, len(rows), initial, realized, bias, relative)


def _outcome_metrics(
    mature: tuple[ECLBacktestObservation, ...],
) -> tuple[ECLOutcomeMetric, ...]:
    if not mature:
        return ()
    result = [_metric(mature, "aggregate", "all")]
    for dimension in ("vintage", "economic_cycle"):
        for value in sorted({str(getattr(item, dimension)) for item in mature}):
            group = tuple(item for item in mature if str(getattr(item, dimension)) == value)
            result.append(_metric(group, dimension, value))
    return tuple(result)


def _attributions(
    observations: tuple[ECLBacktestObservation, ...], policy: ECLBacktestPolicy
) -> tuple[ECLAttribution, ...]:
    result = []
    for observation in observations:
        path = observation.attribution_path
        if path is None:
            continue
        components = tuple(component for component, _ in path.steps)
        if components != policy.required_attribution_components:
            raise DomainValidationError("ECL attribution order or components differ from policy")
        previous = path.opening_ecl
        contributions = []
        for component, resulting_ecl in path.steps:
            amount = resulting_ecl - previous
            contributions.append(ECLAttribution(observation.observation_id, component, amount))
            previous = resulting_ecl
        if (
            path.opening_ecl + sum((item.amount for item in contributions), Decimal("0"))
            != path.steps[-1][1]
        ):
            raise DomainValidationError("ECL attribution does not reconcile")
        result.extend(contributions)
    return tuple(result)


def backtest_ecl(
    methodology_id: str,
    methodology_version: str,
    observations: tuple[ECLBacktestObservation, ...],
    policy: ECLBacktestPolicy | None = None,
) -> ECLBacktestReport:
    """Compare initial ECL with mature losses and reconcile an ordered waterfall."""
    if not methodology_id or not methodology_version or not observations:
        raise DomainValidationError("ECL backtest requires methodology identity and evidence")
    identifiers = [item.observation_id for item in observations]
    if len(identifiers) != len(set(identifiers)):
        raise DomainValidationError("ECL backtest evidence must be unique")
    observations = tuple(sorted(observations, key=lambda item: item.observation_id))
    selected = policy or load_ecl_backtest_policy()
    mature = tuple(item for item in observations if item.realized_loss is not None)
    attribution_count = sum(item.attribution_path is not None for item in observations)
    metrics = _outcome_metrics(mature)
    attributions = _attributions(observations, selected)
    reasons = []
    if len(mature) < selected.minimum_mature_observations:
        reasons.append("mature ECL outcome sample below objective minimum")
    if not mature:
        reasons.append("initial ECL cannot be compared with realized losses")
    if attribution_count != len(observations):
        reasons.append("comparable snapshots are missing for complete attribution")
    aggregate = metrics[0] if metrics else None
    if aggregate is not None and (
        aggregate.absolute_relative_bias is None
        or aggregate.absolute_relative_bias > selected.maximum_absolute_relative_bias
    ):
        reasons.append("aggregate ECL bias exceeds objective limit")
    if reasons:
        decision = ECLBacktestDecision.REJECTED
    else:
        segment_bias = [
            item
            for item in metrics[1:]
            if item.absolute_relative_bias is None
            or item.absolute_relative_bias > selected.maximum_absolute_relative_bias
        ]
        if segment_bias:
            decision = ECLBacktestDecision.PASSED_WITH_RESERVATIONS
            reasons.append(f"vintage/cycle cells above bias limit: {len(segment_bias)}")
        else:
            decision = ECLBacktestDecision.PASSED
            reasons.append("outcome, attribution, vintage and cycle criteria passed")
    evidence_hash = hashlib.sha256(_canonical([asdict(item) for item in observations])).hexdigest()
    payload = {
        "methodology_id": methodology_id,
        "methodology_version": methodology_version,
        "policy_version": selected.version,
        "policy_hash": selected.policy_hash,
        "evidence_hash": evidence_hash,
        "total_observations": len(observations),
        "mature_observations": len(mature),
        "attribution_observations": attribution_count,
        "outcome_metrics": [asdict(item) for item in metrics],
        "attributions": [asdict(item) for item in attributions],
        "decision": decision,
        "decision_reasons": reasons,
        "evidence_scope": "synthetic_independent_backtest",
    }
    report_hash = hashlib.sha256(_canonical(payload)).hexdigest()
    return ECLBacktestReport(
        methodology_id,
        methodology_version,
        selected.version,
        selected.policy_hash,
        evidence_hash,
        len(observations),
        len(mature),
        attribution_count,
        metrics,
        attributions,
        decision,
        tuple(reasons),
        report_hash,
    )


def render_ecl_backtest_report(report: ECLBacktestReport) -> str:
    lines = [
        f"# Independent ECL backtest — {report.methodology_id}",
        "",
        f"- Methodology version: `{report.methodology_version}`",
        f"- Policy: `{report.policy_version}` (`{report.policy_hash}`)",
        f"- Evidence hash: `{report.evidence_hash}`",
        f"- Decision: **{report.decision.value}**",
        f"- Report hash: `{report.report_hash}`",
        f"- Total/mature/attributed observations: `{report.total_observations}` / "
        f"`{report.mature_observations}` / `{report.attribution_observations}`",
        "",
        "## Initial ECL versus realized loss",
        "",
    ]
    if not report.outcome_metrics:
        lines.append("No mature realized-loss linkage is available; performance was not computed.")
    for item in report.outcome_metrics:
        lines.append(
            f"- {item.dimension}/{item.value}: N `{item.observations}`, initial ECL "
            f"`{item.initial_ecl}`, realized loss `{item.realized_loss}`, bias `{item.bias}`."
        )
    lines.extend(["", "## Attribution", ""])
    if not report.attributions:
        lines.append("No comparable snapshots are available for the ordered waterfall.")
    else:
        for component in sorted({item.component for item in report.attributions}):
            amount = sum(
                (item.amount for item in report.attributions if item.component == component),
                Decimal("0"),
            )
            lines.append(f"- {component}: `{amount}`")
    lines.extend(["", "## Decision reasons", ""])
    lines.extend(f"- {reason}" for reason in report.decision_reasons)
    lines.extend(
        [
            "",
            "> Synthetic evidence inventory; missing history is not replaced by fabricated losses.",
            "",
        ]
    )
    return "\n".join(lines)
