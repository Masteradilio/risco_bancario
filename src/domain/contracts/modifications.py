"""Prepayment and contract-modification accounting mechanics."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import ROUND_HALF_EVEN, Decimal
from typing import cast

from ..conventions import DecimalInput, money
from ..exceptions import DomainValidationError
from .amortization import (
    RATE_QUANTUM,
    AmortizationPeriod,
    AmortizationSchedule,
    AmortizationTerms,
    RateReset,
    RateType,
    calculate_effective_interest_rate,
    project_amortized_schedule,
    year_fraction,
)


@dataclass(frozen=True, slots=True)
class PrepaymentResult:
    contract_id: str
    after_period: int
    requested_amount: Decimal
    applied_amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    total_prepayment: bool
    revised_schedule: AmortizationSchedule | None


@dataclass(frozen=True, slots=True)
class ModificationRequest:
    after_period: int
    revised_terms: AmortizationTerms
    derecognize: bool
    replacement_fair_value: DecimalInput | None = None

    def __post_init__(self) -> None:
        if self.after_period <= 0:
            raise DomainValidationError("after_period must be positive")
        if self.derecognize and self.replacement_fair_value is None:
            raise DomainValidationError("derecognition requires replacement_fair_value")
        if not self.derecognize and self.replacement_fair_value is not None:
            raise DomainValidationError("non-derecognition cannot set replacement_fair_value")
        if self.replacement_fair_value is not None:
            object.__setattr__(
                self,
                "replacement_fair_value",
                money(self.replacement_fair_value, field="replacement_fair_value"),
            )


@dataclass(frozen=True, slots=True)
class ModificationResult:
    contract_id: str
    derecognized: bool
    carrying_amount_before: Decimal
    carrying_amount_after: Decimal
    modification_gain_loss: Decimal
    applied_effective_interest_rate: Decimal
    original_effective_interest_rate: Decimal
    revised_schedule: AmortizationSchedule


def _period(schedule: AmortizationSchedule, after_period: int) -> AmortizationPeriod:
    if not 1 <= after_period <= len(schedule.periods):
        raise DomainValidationError("after_period is outside the schedule")
    return schedule.periods[after_period - 1]


def apply_prepayment(
    terms: AmortizationTerms, after_period: int, amount: DecimalInput
) -> PrepaymentResult:
    schedule = project_amortized_schedule(terms)
    event_period = _period(schedule, after_period)
    requested = money(amount, field="prepayment_amount")
    if requested == 0:
        raise DomainValidationError("prepayment_amount must be greater than zero")
    applied = min(requested, event_period.closing_balance)
    balance_after = event_period.closing_balance - applied
    remaining_months = terms.term_months - after_period
    revised_schedule = None
    if balance_after > 0 and remaining_months > 0:
        new_date = event_period.accrual_end
        resets = tuple(item for item in terms.rate_resets if item.effective_date >= new_date)
        annual_rate = cast(Decimal, terms.annual_rate)
        if terms.rate_type is RateType.VARIABLE:
            for reset in terms.rate_resets:
                if reset.effective_date <= new_date:
                    annual_rate = cast(Decimal, reset.annual_rate)
            if not resets:
                resets = (RateReset(new_date, annual_rate),)
        revised_terms = replace(
            terms,
            origination_date=new_date,
            principal=balance_after,
            term_months=remaining_months,
            annual_rate=annual_rate,
            rate_resets=resets,
            upfront_fee=Decimal("0"),
        )
        revised_schedule = project_amortized_schedule(revised_terms)
    return PrepaymentResult(
        terms.contract_id,
        after_period,
        requested,
        applied,
        event_period.closing_balance,
        balance_after,
        balance_after == 0,
        revised_schedule,
    )


def _present_value(
    schedule: AmortizationSchedule, annual_rate: Decimal, terms: AmortizationTerms
) -> Decimal:
    value = sum(
        (
            item.total_payment
            / (Decimal("1") + annual_rate)
            ** year_fraction(terms.origination_date, item.due_date, terms.day_count)
            for item in schedule.periods
        ),
        Decimal("0"),
    )
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def modify_contract(
    original_schedule: AmortizationSchedule, request: ModificationRequest
) -> ModificationResult:
    event_period = _period(original_schedule, request.after_period)
    carrying_before = event_period.closing_balance
    revised_principal = cast(Decimal, request.revised_terms.principal)
    if revised_principal != carrying_before:
        raise DomainValidationError(
            "revised principal must equal carrying amount before modification"
        )
    revised_schedule = project_amortized_schedule(request.revised_terms)
    original_eir = original_schedule.effective_interest_rate
    if request.derecognize:
        fair_value = cast(Decimal, request.replacement_fair_value)
        applied_eir = calculate_effective_interest_rate(
            fair_value,
            request.revised_terms.origination_date,
            revised_schedule.periods,
            request.revised_terms.day_count,
        )
        carrying_after = fair_value
        gain_loss = fair_value - carrying_before
    else:
        carrying_after = _present_value(revised_schedule, original_eir, request.revised_terms)
        applied_eir = original_eir
        gain_loss = carrying_before - carrying_after
    return ModificationResult(
        original_schedule.contract_id,
        request.derecognize,
        carrying_before,
        carrying_after,
        gain_loss.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN),
        applied_eir.quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN),
        original_eir,
        revised_schedule,
    )
