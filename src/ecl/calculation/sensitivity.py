"""Versioned weight, trajectory and stress sensitivities over scenario ECL."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_EVEN, Decimal
from hashlib import sha256
from pathlib import Path

from ...domain.conventions import decimal_from, non_empty, rate
from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import MacroTrajectoryPoint, MacroVariable, ScenarioKind, ScenarioSet
from ...models.forward_looking import MacroRiskPolicy
from .scenario_engine import (
    BaselineRiskPeriod,
    calculate_probability_weighted_scenario_ecl,
)

POLICY_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "scenario_sensitivity" / "2026.07.1.json"
)
MONEY_QUANTUM = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class WeightSensitivityCase:
    case_id: str
    weights: tuple[tuple[str, Decimal], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", non_empty(self.case_id, field="case_id"))
        normalized = tuple(
            (name, rate(value, field=f"weight:{name}")) for name, value in self.weights
        )
        if {name for name, _ in normalized} != {"upside", "base", "downside"}:
            raise DomainValidationError("weight sensitivity requires upside, base and downside")
        if sum((value for _, value in normalized), Decimal("0")) != Decimal("1"):
            raise DomainValidationError("sensitivity weights must sum to one")
        object.__setattr__(self, "weights", normalized)


@dataclass(frozen=True, slots=True)
class TrajectoryShock:
    case_id: str
    variable: str
    additive: Decimal
    scenario_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "case_id", non_empty(self.case_id, field="case_id"))
        object.__setattr__(self, "variable", non_empty(self.variable, field="variable"))
        object.__setattr__(self, "additive", decimal_from(self.additive, field="additive"))
        if not self.scenario_ids or len(self.scenario_ids) != len(set(self.scenario_ids)):
            raise DomainValidationError("trajectory shock requires unique scenario ids")


@dataclass(frozen=True, slots=True)
class ScenarioSensitivityPolicy:
    policy_version: str
    evidence_status: str
    weight_cases: tuple[WeightSensitivityCase, ...]
    trajectory_shocks: tuple[TrajectoryShock, ...]
    sha256: str


@dataclass(frozen=True, slots=True)
class SensitivityResult:
    case_id: str
    kind: str
    probability_weighted_ecl: Decimal
    delta_from_base: Decimal


@dataclass(frozen=True, slots=True)
class ScenarioSensitivityReport:
    base_ecl: Decimal
    stress_ecl: Decimal
    stress_delta: Decimal
    results: tuple[SensitivityResult, ...]
    policy_version: str
    policy_hash: str


def load_scenario_sensitivity_policy(path: Path = POLICY_PATH) -> ScenarioSensitivityPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    metadata = document["metadata"]
    weight_cases = tuple(
        WeightSensitivityCase(
            item["case_id"],
            tuple((name, Decimal(item[name])) for name in ("upside", "base", "downside")),
        )
        for item in document["weight_cases"]
    )
    shocks = tuple(
        TrajectoryShock(
            item["case_id"],
            item["variable"],
            Decimal(item["additive"]),
            tuple(item["scenario_ids"]),
        )
        for item in document["trajectory_shocks"]
    )
    return ScenarioSensitivityPolicy(
        metadata["policy_version"],
        metadata["evidence_status"],
        weight_cases,
        shocks,
        sha256(raw).hexdigest(),
    )


def _derived_hash(source_hash: str, payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(source_hash.encode() + encoded).hexdigest()


def _apply_weights(scenario_set: ScenarioSet, case: WeightSensitivityCase) -> ScenarioSet:
    weights = dict(case.weights)
    trajectories = tuple(
        replace(
            trajectory,
            weight=(
                Decimal("0")
                if trajectory.kind == ScenarioKind.STRESS
                else weights[trajectory.scenario_id]
            ),
        )
        for trajectory in scenario_set.trajectories
    )
    return replace(
        scenario_set,
        version=f"{scenario_set.version}:weight:{case.case_id}",
        source_snapshot_hash=_derived_hash(scenario_set.source_snapshot_hash, case.weights),
        trajectories=trajectories,
    )


def _shock_point(point: MacroTrajectoryPoint, shock: TrajectoryShock) -> MacroTrajectoryPoint:
    found = False
    variables: list[MacroVariable] = []
    for variable in point.variables:
        value = decimal_from(variable.value, field=variable.name)
        if variable.name == shock.variable:
            value += shock.additive
            found = True
        variables.append(MacroVariable(variable.name, value))
    if not found:
        raise DomainValidationError(f"trajectory shock variable not found: {shock.variable}")
    return replace(point, variables=tuple(variables))


def _apply_shock(scenario_set: ScenarioSet, shock: TrajectoryShock) -> ScenarioSet:
    available = {trajectory.scenario_id for trajectory in scenario_set.trajectories}
    if not set(shock.scenario_ids) <= available:
        raise DomainValidationError("trajectory shock references unknown scenario")
    trajectories = tuple(
        (
            replace(
                trajectory,
                periods=tuple(_shock_point(point, shock) for point in trajectory.periods),
            )
            if trajectory.scenario_id in shock.scenario_ids
            else trajectory
        )
        for trajectory in scenario_set.trajectories
    )
    payload = (shock.case_id, shock.variable, str(shock.additive), shock.scenario_ids)
    return replace(
        scenario_set,
        version=f"{scenario_set.version}:shock:{shock.case_id}",
        source_snapshot_hash=_derived_hash(scenario_set.source_snapshot_hash, payload),
        trajectories=trajectories,
    )


def run_scenario_sensitivities(
    baseline: tuple[BaselineRiskPeriod, ...],
    scenario_set: ScenarioSet,
    segment: str,
    macro_policy: MacroRiskPolicy,
    sensitivity_policy: ScenarioSensitivityPolicy,
) -> ScenarioSensitivityReport:
    base = calculate_probability_weighted_scenario_ecl(
        baseline, scenario_set, segment, macro_policy
    )
    results: list[SensitivityResult] = []
    cases: tuple[tuple[str, str, ScenarioSet], ...] = tuple(
        (case.case_id, "weight", _apply_weights(scenario_set, case))
        for case in sensitivity_policy.weight_cases
    ) + tuple(
        (shock.case_id, "trajectory", _apply_shock(scenario_set, shock))
        for shock in sensitivity_policy.trajectory_shocks
    )
    for case_id, kind, derived_set in cases:
        result = calculate_probability_weighted_scenario_ecl(
            baseline, derived_set, segment, macro_policy
        )
        results.append(
            SensitivityResult(
                case_id,
                kind,
                result.probability_weighted_ecl,
                (result.probability_weighted_ecl - base.probability_weighted_ecl).quantize(
                    MONEY_QUANTUM, rounding=ROUND_HALF_EVEN
                ),
            )
        )
    return ScenarioSensitivityReport(
        base.probability_weighted_ecl,
        base.stress_ecl,
        (base.stress_ecl - base.probability_weighted_ecl).quantize(
            MONEY_QUANTUM, rounding=ROUND_HALF_EVEN
        ),
        tuple(results),
        sensitivity_policy.policy_version,
        sensitivity_policy.sha256,
    )
