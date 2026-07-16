from datetime import date
from decimal import Decimal

import pytest

from src.domain.contracts import (
    RevolvingActivity,
    RevolvingProduct,
    RevolvingTerms,
    project_revolving_facility,
)
from src.domain.exceptions import DomainValidationError, TemporalConsistencyError


def terms(**overrides: object) -> RevolvingTerms:
    values: dict[str, object] = {
        "contract_id": "R-1",
        "product": RevolvingProduct.CREDIT_CARD,
        "start_date": date(2026, 1, 1),
        "term_months": 2,
        "credit_limit": "1000",
        "initial_drawn_balance": "400",
        "annual_rate": "0.12",
        "minimum_payment_rate": "0.15",
        "minimum_payment_amount": "50",
    }
    values.update(overrides)
    return RevolvingTerms(**values)  # type: ignore[arg-type]


def test_credit_card_tracks_minimum_payment_and_unused_limit() -> None:
    schedule = project_revolving_facility(
        terms(),
        (
            RevolvingActivity(date(2026, 1, 1), payment="100"),
            RevolvingActivity(date(2026, 2, 1), payment="50"),
        ),
    )
    first = schedule.periods[0]
    assert first.interest == Decimal("4.00")
    assert first.minimum_payment == Decimal("60.60")
    assert first.closing_balance == Decimal("304.00")
    assert first.unused_limit == Decimal("696.00")


def test_drawdown_is_capped_by_available_limit() -> None:
    schedule = project_revolving_facility(
        terms(term_months=1),
        (RevolvingActivity(date(2026, 1, 1), requested_drawdown="900"),),
    )
    period = schedule.periods[0]
    assert period.drawdown == Decimal("596.00")
    assert period.closing_balance == Decimal("1000.00")
    assert period.unused_limit == Decimal("0")


def test_limit_cancellation_cannot_reduce_limit_below_balance() -> None:
    schedule = project_revolving_facility(
        terms(term_months=1),
        (RevolvingActivity(date(2026, 1, 1), payment="100", requested_limit_cancellation="900"),),
    )
    period = schedule.periods[0]
    assert period.limit_cancellation == Decimal("696.00")
    assert period.closing_limit == period.closing_balance == Decimal("304.00")


def test_payment_is_allocated_to_interest_before_principal() -> None:
    schedule = project_revolving_facility(
        terms(term_months=1),
        (RevolvingActivity(date(2026, 1, 1), payment="54"),),
    )
    period = schedule.periods[0]
    assert period.principal_payment == Decimal("50.00")
    assert period.payment_shortfall == Decimal("6.60")


def test_overdraft_uses_same_limit_contract_with_distinct_product_type() -> None:
    schedule = project_revolving_facility(
        terms(
            product=RevolvingProduct.OVERDRAFT,
            term_months=1,
            minimum_payment_rate="1",
            minimum_payment_amount="0",
        ),
        (RevolvingActivity(date(2026, 1, 1), payment="404"),),
    )
    assert schedule.product is RevolvingProduct.OVERDRAFT
    assert schedule.periods[0].closing_balance == Decimal("0.00")


def test_activity_calendar_and_count_are_strict() -> None:
    with pytest.raises(DomainValidationError, match="each contract month"):
        project_revolving_facility(terms(), (RevolvingActivity(date(2026, 1, 1)),))
    with pytest.raises(TemporalConsistencyError, match="monthly"):
        project_revolving_facility(
            terms(),
            (
                RevolvingActivity(date(2026, 1, 1)),
                RevolvingActivity(date(2026, 3, 1)),
            ),
        )


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"contract_id": " "}, "contract_id"),
        ({"term_months": 0}, "term_months"),
        ({"credit_limit": "0"}, "positive credit limit"),
        ({"initial_drawn_balance": "1001"}, "positive credit limit"),
        ({"annual_rate": "-0.01"}, "annual_rate"),
    ],
)
def test_revolving_terms_fail_closed(overrides: dict[str, object], message: str) -> None:
    with pytest.raises(DomainValidationError, match=message):
        terms(**overrides)
