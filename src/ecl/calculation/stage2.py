"""Stage 2 lifetime ECL with behavioral term adjustments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum

from ...domain.conventions import DecimalInput, decimal_from, money, non_empty, rate
from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import ScenarioSet
from ...models.forward_looking import MacroRiskPolicy
from ..discounting import effective_interest_discount_factor
from .scenario_engine import (
    BaselineRiskPeriod,
    ProbabilityWeightedScenarioECL,
    calculate_probability_weighted_scenario_ecl,
)

RATE_QUANTUM = Decimal("0.00000001")


class Stage2CalculationMode(StrEnum):
    INDIVIDUAL = "individual"
    COLLECTIVE = "collective"


@dataclass(frozen=True, slots=True)
class Stage2RiskPeriod:
    reference_date: date
    conditional_hazard: DecimalInput
    lifetime_lgd: DecimalInput
    scheduled_drawn_ead: DecimalInput
    undrawn_amount: DecimalInput = Decimal("0")
    ccf: DecimalInput = Decimal("0")
    expected_prepayment_rate: DecimalInput = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "conditional_hazard", rate(self.conditional_hazard, field="conditional_hazard")
        )
        object.__setattr__(self, "lifetime_lgd", rate(self.lifetime_lgd, field="lifetime_lgd"))
        object.__setattr__(
            self, "scheduled_drawn_ead", money(self.scheduled_drawn_ead, field="drawn_ead")
        )
        object.__setattr__(
            self, "undrawn_amount", money(self.undrawn_amount, field="undrawn_amount")
        )
        object.__setattr__(self, "ccf", rate(self.ccf, field="ccf"))
        object.__setattr__(
            self,
            "expected_prepayment_rate",
            rate(self.expected_prepayment_rate, field="expected_prepayment_rate"),
        )


@dataclass(frozen=True, slots=True)
class Stage2ContractInput:
    contract_id: str
    reporting_date: date
    original_effective_interest_rate: DecimalInput
    contractual_months: int
    expected_extension_months: int
    expected_extension_probability: DecimalInput
    periods: tuple[Stage2RiskPeriod, ...]
    calculation_mode: Stage2CalculationMode = Stage2CalculationMode.INDIVIDUAL
    homogeneous_group_id: str | None = None
    segment: str = "portfolio"

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", non_empty(self.contract_id, field="contract_id"))
        object.__setattr__(self, "segment", non_empty(self.segment, field="segment"))
        object.__setattr__(
            self,
            "original_effective_interest_rate",
            rate(self.original_effective_interest_rate, field="original_effective_interest_rate"),
        )
        object.__setattr__(
            self,
            "expected_extension_probability",
            rate(self.expected_extension_probability, field="expected_extension_probability"),
        )
        if self.contractual_months <= 0 or self.expected_extension_months < 0:
            raise DomainValidationError("Stage 2 term months are invalid")
        if len(self.periods) != self.contractual_months + self.expected_extension_months:
            raise DomainValidationError("Stage 2 periods must cover contractual and extension term")
        if self.expected_extension_months == 0 and self.expected_extension_probability != 0:
            raise DomainValidationError("extension probability requires extension months")
        if not self.periods or self.periods[0].reference_date <= self.reporting_date:
            raise DomainValidationError("Stage 2 periods must follow reporting date")
        if self.calculation_mode == Stage2CalculationMode.COLLECTIVE:
            if self.homogeneous_group_id is None:
                raise DomainValidationError("collective Stage 2 requires homogeneous_group_id")
            object.__setattr__(
                self,
                "homogeneous_group_id",
                non_empty(self.homogeneous_group_id, field="homogeneous_group_id"),
            )
        elif self.homogeneous_group_id is not None:
            raise DomainValidationError("individual Stage 2 cannot use homogeneous_group_id")


@dataclass(frozen=True, slots=True)
class Stage2ECLResult:
    contract_id: str
    reporting_date: date
    contractual_months: int
    behavioral_horizon_months: int
    calculation_mode: Stage2CalculationMode
    homogeneous_group_id: str | None
    scenario_ecl: ProbabilityWeightedScenarioECL
    measurement_basis: str = "lifetime_ecl_behavioral_term"


def calculate_stage2_ecl(
    contract: Stage2ContractInput,
    scenario_set: ScenarioSet,
    macro_policy: MacroRiskPolicy,
) -> Stage2ECLResult:
    behavioral_survival = Decimal("1")
    baseline: list[BaselineRiskPeriod] = []
    for month, period in enumerate(contract.periods, start=1):
        extension_weight = (
            decimal_from(
                contract.expected_extension_probability, field="expected_extension_probability"
            )
            if month > contract.contractual_months
            else Decimal("1")
        )
        exposure_weight = (behavioral_survival * extension_weight).quantize(
            RATE_QUANTUM, rounding=ROUND_HALF_EVEN
        )
        baseline.append(
            BaselineRiskPeriod(
                period.reference_date,
                period.conditional_hazard,
                period.lifetime_lgd,
                decimal_from(period.scheduled_drawn_ead, field="scheduled_drawn_ead")
                * exposure_weight,
                decimal_from(period.undrawn_amount, field="undrawn_amount") * exposure_weight,
                period.ccf,
                effective_interest_discount_factor(
                    contract.original_effective_interest_rate, month
                ),
            )
        )
        behavioral_survival *= Decimal("1") - decimal_from(
            period.expected_prepayment_rate, field="expected_prepayment_rate"
        )
    scenario_ecl = calculate_probability_weighted_scenario_ecl(
        tuple(baseline), scenario_set, contract.segment, macro_policy
    )
    return Stage2ECLResult(
        contract.contract_id,
        contract.reporting_date,
        contract.contractual_months,
        len(contract.periods),
        contract.calculation_mode,
        contract.homogeneous_group_id,
        scenario_ecl,
    )
