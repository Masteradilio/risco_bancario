from datetime import date
from decimal import Decimal

import pytest

from src.domain.contracts import (
    AmortizationMethod,
    AmortizationTerms,
    BusinessDayConvention,
    DayCountConvention,
    RateReset,
    RateType,
    adjust_business_day,
    project_amortized_schedule,
    year_fraction,
)
from src.domain.exceptions import DomainValidationError


def terms(method: AmortizationMethod, **overrides: object) -> AmortizationTerms:
    values: dict[str, object] = {
        "contract_id": "C-1",
        "origination_date": date(2026, 1, 15),
        "principal": "12000",
        "term_months": 12,
        "annual_rate": "0.12",
        "method": method,
    }
    values.update(overrides)
    return AmortizationTerms(**values)  # type: ignore[arg-type]


def test_price_projects_level_payments_and_reconciles_balance() -> None:
    schedule = project_amortized_schedule(terms(AmortizationMethod.PRICE))
    payments = {item.total_payment for item in schedule.periods[:-1]}
    assert len(payments) == 1
    assert sum(item.principal for item in schedule.periods) == Decimal("12000.00")
    assert schedule.periods[-1].closing_balance == Decimal("0.00")


def test_sac_has_constant_principal_and_declining_interest() -> None:
    schedule = project_amortized_schedule(terms(AmortizationMethod.SAC))
    assert {item.principal for item in schedule.periods} == {Decimal("1000.00")}
    assert all(
        left.interest > right.interest
        for left, right in zip(schedule.periods[:-1], schedule.periods[1:], strict=True)
    )


def test_bullet_repay_principal_only_at_maturity() -> None:
    schedule = project_amortized_schedule(terms(AmortizationMethod.BULLET))
    assert all(item.principal == 0 for item in schedule.periods[:-1])
    assert schedule.periods[-1].principal == Decimal("12000.00")


def test_variable_rate_reset_changes_interest_and_recalculates_price() -> None:
    schedule = project_amortized_schedule(
        terms(
            AmortizationMethod.PRICE,
            rate_type=RateType.VARIABLE,
            rate_resets=(RateReset(date(2026, 7, 15), "0.24"),),
        )
    )
    assert schedule.periods[5].annual_rate == Decimal("0.12000000")
    assert schedule.periods[6].annual_rate == Decimal("0.24000000")
    assert schedule.periods[6].total_payment > schedule.periods[5].total_payment


def test_fees_are_separate_and_increase_effective_interest_rate() -> None:
    schedule = project_amortized_schedule(
        terms(AmortizationMethod.PRICE, upfront_fee="200", periodic_fee="5")
    )
    assert schedule.initial_carrying_amount == Decimal("11800.00")
    assert all(item.fee == Decimal("5.00") for item in schedule.periods)
    assert schedule.effective_interest_rate > Decimal("0.12")


def test_business_day_conventions_respect_weekends_and_holidays() -> None:
    holiday = date(2026, 2, 16)
    assert adjust_business_day(
        date(2026, 2, 15), BusinessDayConvention.FOLLOWING, (holiday,)
    ) == date(2026, 2, 17)
    assert adjust_business_day(date(2026, 1, 31), BusinessDayConvention.MODIFIED_FOLLOWING) == date(
        2026, 1, 30
    )


def test_day_count_conventions_are_explicit() -> None:
    start, end = date(2026, 1, 15), date(2026, 2, 15)
    assert year_fraction(start, end, DayCountConvention.THIRTY_360) == Decimal("1") / 12
    assert year_fraction(start, end, DayCountConvention.ACT_365) == Decimal("31") / 365
    assert year_fraction(start, end, DayCountConvention.ACT_360) == Decimal("31") / 360


def test_variable_rate_requires_a_curve_and_fixed_rate_rejects_one() -> None:
    with pytest.raises(DomainValidationError, match="require at least one"):
        terms(AmortizationMethod.PRICE, rate_type=RateType.VARIABLE)
    with pytest.raises(DomainValidationError, match="cannot contain"):
        terms(
            AmortizationMethod.PRICE,
            rate_resets=(RateReset(date(2026, 2, 15), "0.13"),),
        )
