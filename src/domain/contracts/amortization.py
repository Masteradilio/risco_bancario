"""Canonical amortized-contract schedules and effective interest rate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from typing import cast

from ..conventions import DecimalInput, decimal_from, money
from ..exceptions import DomainValidationError

CENT = Decimal("0.01")
RATE_QUANTUM = Decimal("0.00000001")


class AmortizationMethod(StrEnum):
    PRICE = "price"
    SAC = "sac"
    BULLET = "bullet"


class RateType(StrEnum):
    FIXED = "fixed"
    VARIABLE = "variable"


class DayCountConvention(StrEnum):
    ACT_365 = "act_365"
    ACT_360 = "act_360"
    THIRTY_360 = "30_360"


class BusinessDayConvention(StrEnum):
    UNADJUSTED = "unadjusted"
    FOLLOWING = "following"
    MODIFIED_FOLLOWING = "modified_following"
    PRECEDING = "preceding"


@dataclass(frozen=True, slots=True)
class RateReset:
    effective_date: date
    annual_rate: DecimalInput

    def __post_init__(self) -> None:
        value = decimal_from(self.annual_rate, field="annual_rate")
        if value < 0:
            raise DomainValidationError("annual_rate must be non-negative")
        object.__setattr__(self, "annual_rate", value.quantize(RATE_QUANTUM))


@dataclass(frozen=True, slots=True)
class AmortizationTerms:
    contract_id: str
    origination_date: date
    principal: DecimalInput
    term_months: int
    annual_rate: DecimalInput
    method: AmortizationMethod
    rate_type: RateType = RateType.FIXED
    rate_resets: tuple[RateReset, ...] = ()
    upfront_fee: DecimalInput = Decimal("0")
    periodic_fee: DecimalInput = Decimal("0")
    day_count: DayCountConvention = DayCountConvention.THIRTY_360
    business_day_convention: BusinessDayConvention = BusinessDayConvention.FOLLOWING
    holidays: tuple[date, ...] = ()

    def __post_init__(self) -> None:
        if not self.contract_id.strip():
            raise DomainValidationError("contract_id must not be empty")
        if self.term_months <= 0:
            raise DomainValidationError("term_months must be positive")
        principal = money(self.principal, field="principal")
        if principal == 0:
            raise DomainValidationError("principal must be greater than zero")
        annual_rate = decimal_from(self.annual_rate, field="annual_rate")
        if annual_rate < 0:
            raise DomainValidationError("annual_rate must be non-negative")
        upfront_fee = money(self.upfront_fee, field="upfront_fee")
        if upfront_fee >= principal:
            raise DomainValidationError("upfront_fee must be lower than principal")
        periodic_fee = money(self.periodic_fee, field="periodic_fee")
        resets = tuple(sorted(self.rate_resets, key=lambda item: item.effective_date))
        if len({item.effective_date for item in resets}) != len(resets):
            raise DomainValidationError("rate reset dates must be unique")
        if self.rate_type is RateType.FIXED and resets:
            raise DomainValidationError("fixed-rate terms cannot contain rate resets")
        if self.rate_type is RateType.VARIABLE and not resets:
            raise DomainValidationError("variable-rate terms require at least one rate reset")
        object.__setattr__(self, "contract_id", self.contract_id.strip())
        object.__setattr__(self, "principal", principal)
        object.__setattr__(self, "annual_rate", annual_rate.quantize(RATE_QUANTUM))
        object.__setattr__(self, "upfront_fee", upfront_fee)
        object.__setattr__(self, "periodic_fee", periodic_fee)
        object.__setattr__(self, "rate_resets", resets)
        object.__setattr__(self, "holidays", tuple(sorted(set(self.holidays))))


@dataclass(frozen=True, slots=True)
class AmortizationPeriod:
    period_number: int
    accrual_start: date
    accrual_end: date
    due_date: date
    opening_balance: Decimal
    annual_rate: Decimal
    year_fraction: Decimal
    principal: Decimal
    interest: Decimal
    fee: Decimal
    total_payment: Decimal
    closing_balance: Decimal


@dataclass(frozen=True, slots=True)
class AmortizationSchedule:
    contract_id: str
    periods: tuple[AmortizationPeriod, ...]
    effective_interest_rate: Decimal
    initial_carrying_amount: Decimal


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    month_lengths = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    return date(year, month, min(value.day, month_lengths[month - 1]))


def year_fraction(start: date, end: date, convention: DayCountConvention) -> Decimal:
    if end < start:
        raise DomainValidationError("end date cannot precede start date")
    if convention is DayCountConvention.ACT_365:
        return Decimal((end - start).days) / Decimal("365")
    if convention is DayCountConvention.ACT_360:
        return Decimal((end - start).days) / Decimal("360")
    start_day = min(start.day, 30)
    end_day = 30 if start_day == 30 and end.day == 31 else min(end.day, 30)
    days = (end.year - start.year) * 360 + (end.month - start.month) * 30 + end_day - start_day
    return Decimal(days) / Decimal("360")


def _is_business_day(value: date, holidays: frozenset[date]) -> bool:
    return value.weekday() < 5 and value not in holidays


def adjust_business_day(
    value: date,
    convention: BusinessDayConvention,
    holidays: tuple[date, ...] = (),
) -> date:
    if convention is BusinessDayConvention.UNADJUSTED:
        return value
    holiday_set = frozenset(holidays)
    if _is_business_day(value, holiday_set):
        return value
    step = -1 if convention is BusinessDayConvention.PRECEDING else 1
    adjusted = value
    while not _is_business_day(adjusted, holiday_set):
        adjusted += timedelta(days=step)
    if convention is BusinessDayConvention.MODIFIED_FOLLOWING and adjusted.month != value.month:
        return adjust_business_day(value, BusinessDayConvention.PRECEDING, holidays)
    return adjusted


def _rate_for(terms: AmortizationTerms, accrual_start: date) -> Decimal:
    result = cast(Decimal, terms.annual_rate)
    for reset in terms.rate_resets:
        if reset.effective_date > accrual_start:
            break
        result = cast(Decimal, reset.annual_rate)
    return result


def _annuity_payment(balance: Decimal, monthly_rate: Decimal, periods: int) -> Decimal:
    if monthly_rate == 0:
        return balance / Decimal(periods)
    factor = (Decimal("1") + monthly_rate) ** Decimal(-periods)
    return balance * monthly_rate / (Decimal("1") - factor)


def calculate_effective_interest_rate(
    initial_carrying_amount: Decimal,
    origination_date: date,
    periods: tuple[AmortizationPeriod, ...],
    day_count: DayCountConvention,
) -> Decimal:
    def npv(annual_rate: Decimal) -> Decimal:
        return -initial_carrying_amount + sum(
            (
                item.total_payment
                / (Decimal("1") + annual_rate)
                ** year_fraction(origination_date, item.due_date, day_count)
                for item in periods
            ),
            Decimal("0"),
        )

    low = Decimal("0")
    high = Decimal("1")
    while npv(high) > 0 and high < Decimal("1024"):
        high *= 2
    if npv(high) > 0:
        raise DomainValidationError("effective interest rate could not be bracketed")
    for _ in range(120):
        midpoint = (low + high) / 2
        if npv(midpoint) > 0:
            low = midpoint
        else:
            high = midpoint
    return ((low + high) / 2).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN)


def project_amortized_schedule(terms: AmortizationTerms) -> AmortizationSchedule:
    contract_principal = cast(Decimal, terms.principal)
    contract_rate = cast(Decimal, terms.annual_rate)
    upfront_fee = cast(Decimal, terms.upfront_fee)
    periodic_fee = cast(Decimal, terms.periodic_fee)
    balance = contract_principal
    periods: list[AmortizationPeriod] = []
    fixed_price_payment = _annuity_payment(
        balance, contract_rate / Decimal("12"), terms.term_months
    )
    for number in range(1, terms.term_months + 1):
        accrual_start = _add_months(terms.origination_date, number - 1)
        accrual_end = _add_months(terms.origination_date, number)
        due_date = adjust_business_day(accrual_end, terms.business_day_convention, terms.holidays)
        annual_rate = _rate_for(terms, accrual_start)
        fraction = year_fraction(accrual_start, accrual_end, terms.day_count)
        interest = (balance * annual_rate * fraction).quantize(CENT, rounding=ROUND_HALF_EVEN)
        remaining = terms.term_months - number + 1
        if terms.method is AmortizationMethod.SAC:
            principal = (contract_principal / Decimal(terms.term_months)).quantize(
                CENT, rounding=ROUND_HALF_EVEN
            )
        elif terms.method is AmortizationMethod.BULLET:
            principal = balance if number == terms.term_months else Decimal("0")
        else:
            payment = fixed_price_payment
            if terms.rate_type is RateType.VARIABLE:
                payment = _annuity_payment(balance, annual_rate / Decimal("12"), remaining)
            principal = (payment - interest).quantize(CENT, rounding=ROUND_HALF_EVEN)
        principal = min(balance, max(Decimal("0"), principal))
        if number == terms.term_months:
            principal = balance
        closing = (balance - principal).quantize(CENT, rounding=ROUND_HALF_EVEN)
        total = (principal + interest + periodic_fee).quantize(CENT, rounding=ROUND_HALF_EVEN)
        periods.append(
            AmortizationPeriod(
                number,
                accrual_start,
                accrual_end,
                due_date,
                balance,
                annual_rate,
                fraction,
                principal,
                interest,
                periodic_fee,
                total,
                closing,
            )
        )
        balance = closing
    initial_carrying = contract_principal - upfront_fee
    period_tuple = tuple(periods)
    effective_rate = calculate_effective_interest_rate(
        initial_carrying, terms.origination_date, period_tuple, terms.day_count
    )
    return AmortizationSchedule(terms.contract_id, period_tuple, effective_rate, initial_carrying)
