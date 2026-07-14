"""Stage 1 12-month ECL using lifetime loss conditional on default."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ...domain.conventions import DecimalInput, money, non_empty, rate
from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import ScenarioSet
from ...models.forward_looking import MacroRiskPolicy
from ..discounting import effective_interest_discount_factor
from .scenario_engine import (
    BaselineRiskPeriod,
    ProbabilityWeightedScenarioECL,
    calculate_probability_weighted_scenario_ecl,
)


@dataclass(frozen=True, slots=True)
class Stage1RiskPeriod:
    reference_date: date
    conditional_hazard: DecimalInput
    lifetime_lgd: DecimalInput
    drawn_ead: DecimalInput
    undrawn_amount: DecimalInput = Decimal("0")
    ccf: DecimalInput = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "conditional_hazard", rate(self.conditional_hazard, field="conditional_hazard")
        )
        object.__setattr__(self, "lifetime_lgd", rate(self.lifetime_lgd, field="lifetime_lgd"))
        object.__setattr__(self, "drawn_ead", money(self.drawn_ead, field="drawn_ead"))
        object.__setattr__(
            self, "undrawn_amount", money(self.undrawn_amount, field="undrawn_amount")
        )
        object.__setattr__(self, "ccf", rate(self.ccf, field="ccf"))


@dataclass(frozen=True, slots=True)
class Stage1ContractInput:
    contract_id: str
    reporting_date: date
    original_effective_interest_rate: DecimalInput
    periods: tuple[Stage1RiskPeriod, ...]
    segment: str = "portfolio"

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", non_empty(self.contract_id, field="contract_id"))
        object.__setattr__(self, "segment", non_empty(self.segment, field="segment"))
        object.__setattr__(
            self,
            "original_effective_interest_rate",
            rate(self.original_effective_interest_rate, field="original_effective_interest_rate"),
        )
        if not self.periods or len(self.periods) > 12:
            raise DomainValidationError("Stage 1 requires one to twelve default periods")
        if self.periods[0].reference_date <= self.reporting_date:
            raise DomainValidationError("Stage 1 periods must follow reporting date")
        if tuple(item.reference_date for item in self.periods) != tuple(
            sorted(item.reference_date for item in self.periods)
        ):
            raise DomainValidationError("Stage 1 periods must be chronologically ordered")


@dataclass(frozen=True, slots=True)
class Stage1ECLResult:
    contract_id: str
    reporting_date: date
    horizon_months: int
    original_effective_interest_rate: Decimal
    scenario_ecl: ProbabilityWeightedScenarioECL
    measurement_basis: str = "defaults_possible_next_12m_with_lifetime_losses"


def calculate_stage1_ecl(
    contract: Stage1ContractInput,
    scenario_set: ScenarioSet,
    macro_policy: MacroRiskPolicy,
) -> Stage1ECLResult:
    baseline = tuple(
        BaselineRiskPeriod(
            period.reference_date,
            period.conditional_hazard,
            period.lifetime_lgd,
            period.drawn_ead,
            period.undrawn_amount,
            period.ccf,
            effective_interest_discount_factor(contract.original_effective_interest_rate, month),
        )
        for month, period in enumerate(contract.periods, start=1)
    )
    result = calculate_probability_weighted_scenario_ecl(
        baseline, scenario_set, contract.segment, macro_policy
    )
    return Stage1ECLResult(
        contract.contract_id,
        contract.reporting_date,
        len(contract.periods),
        Decimal(str(contract.original_effective_interest_rate)),
        result,
    )
