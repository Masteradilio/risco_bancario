"""Versioned synthetic macroeconomic history and forward scenarios."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from hashlib import sha256
from pathlib import Path
from random import Random
from typing import Any

from .population import _add_months

POLICY_PATH = (
    Path(__file__).resolve().parents[3]
    / "config"
    / "synthetic"
    / "macroeconomic_scenarios"
    / "1.0.0.json"
)
QUANTUM = Decimal("0.0001")
VARIABLES = ("gdp_growth", "inflation", "policy_rate", "unemployment", "household_debt")


@dataclass(frozen=True, slots=True)
class MacroObservation:
    reference_date: date
    scenario_id: str
    regime: str
    gdp_growth: Decimal
    inflation: Decimal
    policy_rate: Decimal
    unemployment: Decimal
    household_debt: Decimal
    risk_pressure: Decimal
    policy_version: str


@dataclass(frozen=True, slots=True)
class MacroeconomicBundle:
    observed: tuple[MacroObservation, ...]
    scenarios: tuple[MacroObservation, ...]
    scenario_weights: tuple[tuple[str, Decimal], ...]
    policy_version: str
    policy_hash: str
    seed: int

    def as_tables(self) -> dict[str, list[dict[str, object]]]:
        return {
            "macro_observed": [asdict(item) for item in self.observed],
            "macro_scenarios": [asdict(item) for item in self.scenarios],
            "scenario_weights": [
                {"scenario_id": scenario_id, "weight": weight}
                for scenario_id, weight in self.scenario_weights
            ],
        }


def _quantize(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _load_policy(path: Path = POLICY_PATH) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    policy = json.loads(raw)
    scenarios = policy["forecast"]["scenarios"]
    ids = [item["scenario_id"] for item in scenarios]
    if ids != ["upside", "base", "downside", "stress"]:
        raise ValueError("macro scenario policy requires upside, base, downside and stress")
    if sum(Decimal(str(item["weight"])) for item in scenarios) != Decimal("1"):
        raise ValueError("probability-weighted macro scenario weights must sum to one")
    if Decimal(str(scenarios[-1]["weight"])) != Decimal("0"):
        raise ValueError("stress is a sensitivity path and must have zero probability weight")
    return policy, sha256(raw).hexdigest()


def _risk_pressure(values: dict[str, float]) -> Decimal:
    pressure = (
        0.08 * max(0.0, -values["gdp_growth"]) ** 2
        + 0.02 * max(0.0, values["inflation"] - 4.5) ** 2
        + 0.01 * max(0.0, values["policy_rate"] - 10.0) ** 2
        + 0.05 * max(0.0, values["unemployment"] - 7.0) ** 2
        + 0.01 * max(0.0, values["household_debt"] - 45.0) ** 2
    )
    return _quantize(pressure)


def _record(
    reference_date: date,
    scenario_id: str,
    regime: str,
    values: dict[str, float],
    version: str,
) -> MacroObservation:
    return MacroObservation(
        reference_date,
        scenario_id,
        regime,
        _quantize(values["gdp_growth"]),
        _quantize(values["inflation"]),
        _quantize(values["policy_rate"]),
        _quantize(values["unemployment"]),
        _quantize(values["household_debt"]),
        _risk_pressure(values),
        version,
    )


def generate_macroeconomic_bundle(seed: int = 20260714) -> MacroeconomicBundle:
    policy, policy_hash = _load_policy()
    version = policy["metadata"]["version"]
    rng = Random(seed)
    current = {
        "gdp_growth": 0.5,
        "inflation": 6.5,
        "policy_rate": 14.0,
        "unemployment": 10.0,
        "household_debt": 41.0,
    }
    observed: list[MacroObservation] = []
    for regime in policy["observed"]["regimes"]:
        cursor = date.fromisoformat(regime["start"])
        end = date.fromisoformat(regime["end"])
        while cursor <= end:
            for name in VARIABLES:
                target = float(regime["targets"][name])
                noise_scale = 0.12 if name == "gdp_growth" else 0.06
                current[name] += 0.18 * (target - current[name]) + rng.gauss(0, noise_scale)
            observed.append(_record(cursor, "observed", regime["name"], current, version))
            cursor = _add_months(cursor, 1)

    anchor = {name: float(getattr(observed[-1], name)) for name in VARIABLES}
    scenarios: list[MacroObservation] = []
    horizon = int(policy["forecast"]["horizon_months"])
    start = date.fromisoformat(policy["forecast"]["start_date"])
    for scenario in policy["forecast"]["scenarios"]:
        scenario_id = scenario["scenario_id"]
        curvature = float(scenario["curvature"])
        for month in range(horizon):
            progress = (month + 1) / horizon
            shaped = 1 - math.exp(-curvature * 3 * progress)
            values = {
                name: anchor[name] + float(scenario["terminal_offsets"][name]) * shaped
                for name in VARIABLES
            }
            scenarios.append(
                _record(_add_months(start, month), scenario_id, "forecast", values, version)
            )

    weights = tuple(
        (item["scenario_id"], _quantize(item["weight"])) for item in policy["forecast"]["scenarios"]
    )
    return MacroeconomicBundle(
        tuple(observed), tuple(scenarios), weights, version, policy_hash, seed
    )
