"""Stage 3 scenario cash-shortfall measurement."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from ...domain.conventions import DecimalInput, decimal_from, money, non_empty, rate
from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import ScenarioKind, ScenarioSet
from ..discounting import effective_interest_discount_factor

MONEY_QUANTUM = Decimal("0.01")
CONTRIBUTION_QUANTUM = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class Stage3CashFlowPeriod:
    reference_date: date
    contractual_cash_flow: DecimalInput
    expected_borrower_receipt: DecimalInput = Decimal("0")
    unsecured_recovery: DecimalInput = Decimal("0")
    collateral_recovery: DecimalInput = Decimal("0")
    guarantee_recovery: DecimalInput = Decimal("0")
    post_writeoff_recovery: DecimalInput = Decimal("0")
    collection_costs: DecimalInput = Decimal("0")
    writeoff_amount: DecimalInput = Decimal("0")
    cure_event: bool = False

    def __post_init__(self) -> None:
        for field in (
            "contractual_cash_flow",
            "expected_borrower_receipt",
            "unsecured_recovery",
            "collateral_recovery",
            "guarantee_recovery",
            "post_writeoff_recovery",
            "collection_costs",
            "writeoff_amount",
        ):
            object.__setattr__(self, field, money(getattr(self, field), field=field))


@dataclass(frozen=True, slots=True)
class Stage3ScenarioProjection:
    scenario_id: str
    periods: tuple[Stage3CashFlowPeriod, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", non_empty(self.scenario_id, field="scenario_id"))
        if not self.periods:
            raise DomainValidationError("Stage 3 scenario projection requires periods")
        dates = tuple(period.reference_date for period in self.periods)
        if dates != tuple(sorted(dates)) or len(dates) != len(set(dates)):
            raise DomainValidationError("Stage 3 cash-flow dates must be unique and ordered")
        writeoff_seen = False
        cure_count = 0
        for period in self.periods:
            if decimal_from(period.writeoff_amount, field="writeoff_amount") > 0:
                writeoff_seen = True
            if decimal_from(period.post_writeoff_recovery, field="post_writeoff_recovery") > 0:
                if not writeoff_seen:
                    raise DomainValidationError("post-writeoff recovery requires prior write-off")
            cure_count += int(period.cure_event)
        if cure_count > 1:
            raise DomainValidationError("Stage 3 scenario permits at most one cure event")


@dataclass(frozen=True, slots=True)
class Stage3ContractInput:
    contract_id: str
    reporting_date: date
    gross_carrying_amount: DecimalInput
    opening_loss_allowance: DecimalInput
    original_effective_interest_rate: DecimalInput
    scenario_projections: tuple[Stage3ScenarioProjection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", non_empty(self.contract_id, field="contract_id"))
        gross = money(self.gross_carrying_amount, field="gross_carrying_amount")
        allowance = money(self.opening_loss_allowance, field="opening_loss_allowance")
        if allowance > gross:
            raise DomainValidationError(
                "opening loss allowance cannot exceed gross carrying amount"
            )
        object.__setattr__(self, "gross_carrying_amount", gross)
        object.__setattr__(self, "opening_loss_allowance", allowance)
        object.__setattr__(
            self,
            "original_effective_interest_rate",
            rate(self.original_effective_interest_rate, field="original_effective_interest_rate"),
        )
        if not self.scenario_projections:
            raise DomainValidationError("Stage 3 requires scenario projections")


@dataclass(frozen=True, slots=True)
class Stage3MeasuredPeriod:
    reference_date: date
    contractual_cash_flow: Decimal
    expected_cash_inflows: Decimal
    collection_costs: Decimal
    cash_shortfall: Decimal
    discount_factor: Decimal
    discounted_cash_shortfall: Decimal
    writeoff_amount: Decimal
    cure_event: bool


@dataclass(frozen=True, slots=True)
class Stage3ScenarioResult:
    scenario_id: str
    kind: ScenarioKind
    weight: Decimal
    periods: tuple[Stage3MeasuredPeriod, ...]
    ecl: Decimal
    weighted_contribution: Decimal
    total_writeoff: Decimal
    cured: bool


@dataclass(frozen=True, slots=True)
class Stage3ECLResult:
    contract_id: str
    reporting_date: date
    scenario_results: tuple[Stage3ScenarioResult, ...]
    probability_weighted_ecl: Decimal
    stress_ecl: Decimal
    net_carrying_amount: Decimal
    monthly_interest_revenue: Decimal
    interest_basis: str
    scenario_version: str
    scenario_source_hash: str


def _validate_scenarios(contract: Stage3ContractInput, scenario_set: ScenarioSet) -> None:
    expected_ids = {trajectory.scenario_id for trajectory in scenario_set.trajectories}
    actual_ids = [projection.scenario_id for projection in contract.scenario_projections]
    if set(actual_ids) != expected_ids or len(actual_ids) != len(set(actual_ids)):
        raise DomainValidationError("Stage 3 projections must cover each scenario exactly once")
    date_sets = {
        tuple(period.reference_date for period in projection.periods)
        for projection in contract.scenario_projections
    }
    if len(date_sets) != 1:
        raise DomainValidationError("Stage 3 scenario projections must share cash-flow dates")
    dates = next(iter(date_sets))
    if dates[0] <= contract.reporting_date:
        raise DomainValidationError("Stage 3 cash flows must follow reporting date")


def calculate_stage3_ecl(
    contract: Stage3ContractInput, scenario_set: ScenarioSet
) -> Stage3ECLResult:
    _validate_scenarios(contract, scenario_set)
    trajectories = {item.scenario_id: item for item in scenario_set.trajectories}
    results: list[Stage3ScenarioResult] = []
    for projection in contract.scenario_projections:
        trajectory = trajectories[projection.scenario_id]
        periods: list[Stage3MeasuredPeriod] = []
        for month, period in enumerate(projection.periods, start=1):
            expected_inflows = sum(
                (
                    decimal_from(period.expected_borrower_receipt, field="borrower_receipt"),
                    decimal_from(period.unsecured_recovery, field="unsecured_recovery"),
                    decimal_from(period.collateral_recovery, field="collateral_recovery"),
                    decimal_from(period.guarantee_recovery, field="guarantee_recovery"),
                    decimal_from(period.post_writeoff_recovery, field="post_writeoff_recovery"),
                ),
                Decimal("0"),
            )
            costs = decimal_from(period.collection_costs, field="collection_costs")
            shortfall = (
                decimal_from(period.contractual_cash_flow, field="contractual_cash_flow")
                - expected_inflows
                + costs
            ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
            discount = effective_interest_discount_factor(
                contract.original_effective_interest_rate, month
            )
            discounted = (shortfall * discount).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
            periods.append(
                Stage3MeasuredPeriod(
                    period.reference_date,
                    decimal_from(period.contractual_cash_flow, field="contractual_cash_flow"),
                    expected_inflows,
                    costs,
                    shortfall,
                    discount,
                    discounted,
                    decimal_from(period.writeoff_amount, field="writeoff_amount"),
                    period.cure_event,
                )
            )
        ecl = max(
            Decimal("0"),
            sum((period.discounted_cash_shortfall for period in periods), Decimal("0")),
        ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
        weight = decimal_from(trajectory.weight, field="scenario_weight")
        contribution = (ecl * weight).quantize(CONTRIBUTION_QUANTUM, rounding=ROUND_HALF_EVEN)
        total_writeoff = sum((period.writeoff_amount for period in periods), Decimal("0")).quantize(
            MONEY_QUANTUM, rounding=ROUND_HALF_EVEN
        )
        results.append(
            Stage3ScenarioResult(
                projection.scenario_id,
                trajectory.kind,
                weight,
                tuple(periods),
                ecl,
                contribution,
                total_writeoff,
                any(period.cure_event for period in periods),
            )
        )
    weighted = sum(
        (result.weighted_contribution for result in results if result.kind != ScenarioKind.STRESS),
        Decimal("0"),
    ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
    stress = next(result.ecl for result in results if result.kind == ScenarioKind.STRESS)
    net_carrying = (
        decimal_from(contract.gross_carrying_amount, field="gross_carrying_amount")
        - decimal_from(contract.opening_loss_allowance, field="opening_loss_allowance")
    ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
    monthly_interest = (
        net_carrying
        * decimal_from(contract.original_effective_interest_rate, field="original_eir")
        / Decimal("12")
    ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
    return Stage3ECLResult(
        contract.contract_id,
        contract.reporting_date,
        tuple(results),
        weighted,
        stress,
        net_carrying,
        monthly_interest,
        "net_carrying_amount_for_credit_impaired_asset",
        scenario_set.version,
        scenario_set.source_snapshot_hash,
    )
