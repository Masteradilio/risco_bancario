"""Canonical monthly engine for cards, overdrafts and revolving facilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from typing import cast

from ..conventions import DecimalInput, decimal_from, money, rate
from ..exceptions import DomainValidationError, TemporalConsistencyError
from .amortization import _add_months

CENT = Decimal("0.01")


class RevolvingProduct(StrEnum):
    CREDIT_CARD = "credit_card"
    OVERDRAFT = "overdraft"


@dataclass(frozen=True, slots=True)
class RevolvingTerms:
    contract_id: str
    product: RevolvingProduct
    start_date: date
    term_months: int
    credit_limit: DecimalInput
    initial_drawn_balance: DecimalInput
    annual_rate: DecimalInput
    minimum_payment_rate: DecimalInput
    minimum_payment_amount: DecimalInput = Decimal("0")

    def __post_init__(self) -> None:
        if not self.contract_id.strip():
            raise DomainValidationError("contract_id must not be empty")
        if self.term_months <= 0:
            raise DomainValidationError("term_months must be positive")
        limit = money(self.credit_limit, field="credit_limit")
        drawn = money(self.initial_drawn_balance, field="initial_drawn_balance")
        if limit == 0 or drawn > limit:
            raise DomainValidationError("drawn balance must be within a positive credit limit")
        annual_rate = decimal_from(self.annual_rate, field="annual_rate")
        if annual_rate < 0:
            raise DomainValidationError("annual_rate must be non-negative")
        minimum_rate = rate(self.minimum_payment_rate, field="minimum_payment_rate")
        minimum_amount = money(self.minimum_payment_amount, field="minimum_payment_amount")
        object.__setattr__(self, "contract_id", self.contract_id.strip())
        object.__setattr__(self, "credit_limit", limit)
        object.__setattr__(self, "initial_drawn_balance", drawn)
        object.__setattr__(self, "annual_rate", annual_rate)
        object.__setattr__(self, "minimum_payment_rate", minimum_rate)
        object.__setattr__(self, "minimum_payment_amount", minimum_amount)


@dataclass(frozen=True, slots=True)
class RevolvingActivity:
    reference_date: date
    requested_drawdown: DecimalInput = Decimal("0")
    payment: DecimalInput = Decimal("0")
    requested_limit_cancellation: DecimalInput = Decimal("0")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requested_drawdown",
            money(self.requested_drawdown, field="requested_drawdown"),
        )
        object.__setattr__(self, "payment", money(self.payment, field="payment"))
        object.__setattr__(
            self,
            "requested_limit_cancellation",
            money(self.requested_limit_cancellation, field="requested_limit_cancellation"),
        )


@dataclass(frozen=True, slots=True)
class RevolvingPeriod:
    period_number: int
    reference_date: date
    opening_limit: Decimal
    opening_balance: Decimal
    interest: Decimal
    drawdown: Decimal
    minimum_payment: Decimal
    actual_payment: Decimal
    payment_shortfall: Decimal
    principal_payment: Decimal
    limit_cancellation: Decimal
    closing_limit: Decimal
    closing_balance: Decimal
    unused_limit: Decimal


@dataclass(frozen=True, slots=True)
class RevolvingSchedule:
    contract_id: str
    product: RevolvingProduct
    periods: tuple[RevolvingPeriod, ...]


def project_revolving_facility(
    terms: RevolvingTerms, activities: tuple[RevolvingActivity, ...]
) -> RevolvingSchedule:
    if len(activities) != terms.term_months:
        raise DomainValidationError("one activity is required for each contract month")
    expected_dates = tuple(
        _add_months(terms.start_date, month) for month in range(terms.term_months)
    )
    actual_dates = tuple(item.reference_date for item in activities)
    if actual_dates != expected_dates:
        raise TemporalConsistencyError(
            "activities must be unique, ordered and monthly from start_date"
        )

    current_limit = cast(Decimal, terms.credit_limit)
    current_balance = cast(Decimal, terms.initial_drawn_balance)
    annual_rate = cast(Decimal, terms.annual_rate)
    minimum_rate = cast(Decimal, terms.minimum_payment_rate)
    minimum_amount = cast(Decimal, terms.minimum_payment_amount)
    periods: list[RevolvingPeriod] = []
    for number, activity in enumerate(activities, start=1):
        interest = (current_balance * annual_rate / Decimal("12")).quantize(
            CENT, rounding=ROUND_HALF_EVEN
        )
        available_before_payment = max(Decimal("0"), current_limit - current_balance - interest)
        drawdown = min(cast(Decimal, activity.requested_drawdown), available_before_payment)
        amount_due = current_balance + interest + drawdown
        minimum_payment = min(
            amount_due,
            max(minimum_amount, (amount_due * minimum_rate).quantize(CENT)),
        )
        actual_payment = min(cast(Decimal, activity.payment), amount_due)
        payment_shortfall = max(Decimal("0"), minimum_payment - actual_payment)
        principal_payment = max(Decimal("0"), actual_payment - interest)
        principal_payment = min(current_balance + drawdown, principal_payment)
        closing_balance = (amount_due - actual_payment).quantize(CENT, rounding=ROUND_HALF_EVEN)
        unused_before_cancellation = max(Decimal("0"), current_limit - closing_balance)
        cancellation = min(
            cast(Decimal, activity.requested_limit_cancellation), unused_before_cancellation
        )
        closing_limit = (current_limit - cancellation).quantize(CENT, rounding=ROUND_HALF_EVEN)
        unused_limit = max(Decimal("0"), closing_limit - closing_balance)
        periods.append(
            RevolvingPeriod(
                number,
                activity.reference_date,
                current_limit,
                current_balance,
                interest,
                drawdown,
                minimum_payment,
                actual_payment,
                payment_shortfall,
                principal_payment,
                cancellation,
                closing_limit,
                closing_balance,
                unused_limit,
            )
        )
        current_limit = closing_limit
        current_balance = closing_balance
    return RevolvingSchedule(terms.contract_id, terms.product, tuple(periods))
