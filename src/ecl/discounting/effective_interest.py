"""Original effective-interest-rate discount factors."""

from decimal import ROUND_HALF_EVEN, Decimal

from ...domain.conventions import DecimalInput, decimal_from, rate
from ...domain.exceptions import DomainValidationError

QUANTUM = Decimal("0.00000001")


def effective_interest_discount_factor(
    original_annual_eir: DecimalInput, months_from_reporting_date: int
) -> Decimal:
    annual_eir = rate(original_annual_eir, field="original_annual_eir")
    if months_from_reporting_date <= 0:
        raise DomainValidationError("months_from_reporting_date must be positive")
    exponent = Decimal(months_from_reporting_date) / Decimal("12")
    factor = Decimal("1") / ((Decimal("1") + annual_eir) ** exponent)
    return factor.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def present_value(amount: DecimalInput, discount_factor: DecimalInput) -> Decimal:
    value = decimal_from(amount, field="amount")
    factor = rate(discount_factor, field="discount_factor")
    return (value * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
