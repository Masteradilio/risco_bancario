"""Transparent, governed macroeconomic relations for scenario risk curves."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...domain.conventions import decimal_from
from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import MacroTrajectoryPoint, ScenarioSet

POLICY_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "macro_risk_relations" / "2026.07.1.json"
)
QUANTUM = Decimal("0.00000001")
COMPONENTS = ("pd", "lgd", "ead", "ccf")


@dataclass(frozen=True, slots=True)
class ComponentRelation:
    linear: tuple[tuple[str, Decimal], ...]
    quadratic: tuple[tuple[str, Decimal], ...]
    minimum: Decimal
    maximum: Decimal


@dataclass(frozen=True, slots=True)
class MacroRiskPolicy:
    policy_version: str
    evidence_status: str
    anchors: tuple[tuple[str, Decimal], ...]
    components: tuple[tuple[str, ComponentRelation], ...]
    segment_scalars: tuple[tuple[str, tuple[tuple[str, Decimal], ...]], ...]
    sha256: str


@dataclass(frozen=True, slots=True)
class MacroRiskMultipliers:
    scenario_id: str
    reference_date: date
    segment: str
    pd: Decimal
    lgd: Decimal
    ead: Decimal
    ccf: Decimal
    policy_version: str
    policy_hash: str


def _decimal_pairs(values: dict[str, Any]) -> tuple[tuple[str, Decimal], ...]:
    return tuple((name, Decimal(str(value))) for name, value in values.items())


def load_macro_risk_policy(path: Path = POLICY_PATH) -> MacroRiskPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    metadata = document["metadata"]
    components = tuple(
        (
            name,
            ComponentRelation(
                _decimal_pairs(values["linear"]),
                _decimal_pairs(values["quadratic"]),
                Decimal(values["minimum"]),
                Decimal(values["maximum"]),
            ),
        )
        for name, values in document["components"].items()
    )
    if tuple(name for name, _ in components) != COMPONENTS:
        raise DomainValidationError("macro risk policy requires pd, lgd, ead and ccf")
    if any(
        relation.minimum <= 0 or relation.maximum < relation.minimum for _, relation in components
    ):
        raise DomainValidationError("macro risk relation bounds are invalid")
    segment_scalars = tuple(
        (segment, _decimal_pairs(values)) for segment, values in document["segment_scalars"].items()
    )
    if any(tuple(name for name, _ in values) != COMPONENTS for _, values in segment_scalars):
        raise DomainValidationError("every macro segment requires pd, lgd, ead and ccf scalars")
    return MacroRiskPolicy(
        metadata["policy_version"],
        metadata["evidence_status"],
        _decimal_pairs(document["anchors"]),
        components,
        segment_scalars,
        sha256(raw).hexdigest(),
    )


def _component_multiplier(
    *,
    variables: dict[str, Decimal],
    anchors: dict[str, Decimal],
    relation: ComponentRelation,
    segment_scalar: Decimal,
) -> Decimal:
    deltas = {name: variables[name] - anchor for name, anchor in anchors.items()}
    score = sum((coefficient * deltas[name] for name, coefficient in relation.linear), Decimal("0"))
    score += sum(
        (
            coefficient * deltas[name] * abs(deltas[name])
            for name, coefficient in relation.quadratic
        ),
        Decimal("0"),
    )
    raw = (score * segment_scalar).exp()
    return min(relation.maximum, max(relation.minimum, raw)).quantize(
        QUANTUM, rounding=ROUND_HALF_EVEN
    )


@lru_cache(maxsize=256)
def calculate_macro_risk_multipliers(
    scenario_id: str,
    point: MacroTrajectoryPoint,
    segment: str,
    policy: MacroRiskPolicy,
) -> MacroRiskMultipliers:
    variables = {
        variable.name: decimal_from(variable.value, field=variable.name)
        for variable in point.variables
    }
    anchors = dict(policy.anchors)
    missing = set(anchors) - set(variables)
    if missing:
        raise DomainValidationError(f"macro trajectory missing variables: {sorted(missing)}")
    try:
        scalars = dict(dict(policy.segment_scalars)[segment])
    except KeyError as exc:
        raise DomainValidationError(f"unknown macro risk segment: {segment}") from exc
    multipliers = {
        name: _component_multiplier(
            variables=variables,
            anchors=anchors,
            relation=relation,
            segment_scalar=scalars[name],
        )
        for name, relation in policy.components
    }
    return MacroRiskMultipliers(
        scenario_id,
        point.reference_date,
        segment,
        multipliers["pd"],
        multipliers["lgd"],
        multipliers["ead"],
        multipliers["ccf"],
        policy.policy_version,
        policy.sha256,
    )


def build_macro_risk_paths(
    scenario_set: ScenarioSet,
    segment: str,
    policy: MacroRiskPolicy,
) -> tuple[MacroRiskMultipliers, ...]:
    return tuple(
        calculate_macro_risk_multipliers(trajectory.scenario_id, point, segment, policy)
        for trajectory in scenario_set.trajectories
        for point in trajectory.periods
    )
