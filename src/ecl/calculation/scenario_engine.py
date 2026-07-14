"""Period-by-period scenario ECL before stage-specific orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from ...domain.conventions import DecimalInput, decimal_from, money, rate
from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import ScenarioKind, ScenarioSet
from ...models.forward_looking import MacroRiskPolicy, calculate_macro_risk_multipliers

MONEY_QUANTUM = Decimal("0.01")
RATE_QUANTUM = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class BaselineRiskPeriod:
    reference_date: date
    conditional_hazard: DecimalInput
    lgd: DecimalInput
    drawn_ead: DecimalInput
    undrawn_amount: DecimalInput
    ccf: DecimalInput
    discount_factor: DecimalInput

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "conditional_hazard", rate(self.conditional_hazard, field="conditional_hazard")
        )
        object.__setattr__(self, "lgd", rate(self.lgd, field="lgd"))
        object.__setattr__(self, "drawn_ead", money(self.drawn_ead, field="drawn_ead"))
        object.__setattr__(
            self, "undrawn_amount", money(self.undrawn_amount, field="undrawn_amount")
        )
        object.__setattr__(self, "ccf", rate(self.ccf, field="ccf"))
        discount_factor = rate(self.discount_factor, field="discount_factor")
        if discount_factor == 0:
            raise DomainValidationError("discount_factor must be greater than zero")
        object.__setattr__(self, "discount_factor", discount_factor)


@dataclass(frozen=True, slots=True)
class ScenarioRiskPeriod:
    scenario_id: str
    reference_date: date
    survival_at_start: Decimal
    conditional_hazard: Decimal
    marginal_pd: Decimal
    lgd: Decimal
    ead: Decimal
    ccf: Decimal
    discount_factor: Decimal
    expected_loss: Decimal


@dataclass(frozen=True, slots=True)
class ScenarioIntegral:
    scenario_id: str
    kind: ScenarioKind
    weight: Decimal
    periods: tuple[ScenarioRiskPeriod, ...]
    ecl: Decimal
    weighted_contribution: Decimal


@dataclass(frozen=True, slots=True)
class ProbabilityWeightedScenarioECL:
    scenario_results: tuple[ScenarioIntegral, ...]
    probability_weighted_ecl: Decimal
    stress_ecl: Decimal
    scenario_version: str
    scenario_source_hash: str
    macro_policy_version: str
    macro_policy_hash: str


def _validate_baseline(baseline: tuple[BaselineRiskPeriod, ...], scenario_set: ScenarioSet) -> None:
    if not baseline:
        raise DomainValidationError("baseline risk curve must not be empty")
    if len(baseline) > len(scenario_set.trajectories[0].periods):
        raise DomainValidationError("baseline risk curve exceeds scenario horizon")
    expected_dates = tuple(
        point.reference_date for point in scenario_set.trajectories[0].periods[: len(baseline)]
    )
    if tuple(period.reference_date for period in baseline) != expected_dates:
        raise DomainValidationError("baseline dates must align with scenario periods")


def calculate_probability_weighted_scenario_ecl(
    baseline: tuple[BaselineRiskPeriod, ...],
    scenario_set: ScenarioSet,
    segment: str,
    macro_policy: MacroRiskPolicy,
) -> ProbabilityWeightedScenarioECL:
    _validate_baseline(baseline, scenario_set)
    results: list[ScenarioIntegral] = []
    for trajectory in scenario_set.trajectories:
        survival = Decimal("1")
        periods: list[ScenarioRiskPeriod] = []
        for base, macro_point in zip(baseline, trajectory.periods[: len(baseline)], strict=True):
            factors = calculate_macro_risk_multipliers(
                trajectory.scenario_id, macro_point, segment, macro_policy
            )
            hazard = min(
                Decimal("1"),
                decimal_from(base.conditional_hazard, field="conditional_hazard") * factors.pd,
            ).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN)
            marginal_pd = (survival * hazard).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN)
            adjusted_lgd = min(
                Decimal("1"), decimal_from(base.lgd, field="lgd") * factors.lgd
            ).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN)
            adjusted_ccf = min(
                Decimal("1"), decimal_from(base.ccf, field="ccf") * factors.ccf
            ).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN)
            adjusted_ead = (
                decimal_from(base.drawn_ead, field="drawn_ead") * factors.ead
                + decimal_from(base.undrawn_amount, field="undrawn_amount") * adjusted_ccf
            ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
            expected_loss = (
                marginal_pd
                * adjusted_lgd
                * adjusted_ead
                * decimal_from(base.discount_factor, field="discount_factor")
            ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
            periods.append(
                ScenarioRiskPeriod(
                    trajectory.scenario_id,
                    base.reference_date,
                    survival.quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN),
                    hazard,
                    marginal_pd,
                    adjusted_lgd,
                    adjusted_ead,
                    adjusted_ccf,
                    decimal_from(base.discount_factor, field="discount_factor"),
                    expected_loss,
                )
            )
            survival = max(Decimal("0"), survival - marginal_pd)
        ecl = sum((period.expected_loss for period in periods), Decimal("0")).quantize(
            MONEY_QUANTUM, rounding=ROUND_HALF_EVEN
        )
        scenario_weight = decimal_from(trajectory.weight, field="scenario_weight")
        contribution = (ecl * scenario_weight).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN)
        results.append(
            ScenarioIntegral(
                trajectory.scenario_id,
                trajectory.kind,
                scenario_weight,
                tuple(periods),
                ecl,
                contribution,
            )
        )
    weighted_ecl = sum(
        (result.weighted_contribution for result in results if result.kind != ScenarioKind.STRESS),
        Decimal("0"),
    ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
    stress_ecl = next(result.ecl for result in results if result.kind == ScenarioKind.STRESS)
    return ProbabilityWeightedScenarioECL(
        tuple(results),
        weighted_ecl,
        stress_ecl,
        scenario_set.version,
        scenario_set.source_snapshot_hash,
        macro_policy.policy_version,
        macro_policy.sha256,
    )
