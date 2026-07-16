from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from src.domain.contracts import (
    AmortizationMethod,
    AmortizationTerms,
    ModificationRequest,
    RateReset,
    RateType,
    apply_prepayment,
    modify_contract,
    project_amortized_schedule,
)
from src.domain.exceptions import DomainValidationError


def original_terms() -> AmortizationTerms:
    return AmortizationTerms(
        "M-1", date(2026, 1, 15), "12000", 12, "0.12", AmortizationMethod.PRICE
    )


def test_partial_prepayment_reduces_balance_and_reprojects_remaining_term() -> None:
    result = apply_prepayment(original_terms(), 3, "2000")
    assert result.applied_amount == Decimal("2000.00")
    assert result.balance_after == result.balance_before - Decimal("2000.00")
    assert not result.total_prepayment
    assert result.revised_schedule is not None
    assert len(result.revised_schedule.periods) == 9
    assert result.revised_schedule.periods[-1].closing_balance == Decimal("0.00")


def test_total_prepayment_caps_amount_and_closes_contract() -> None:
    result = apply_prepayment(original_terms(), 3, "99999")
    assert result.applied_amount == result.balance_before
    assert result.total_prepayment
    assert result.revised_schedule is None


def test_non_derecognized_modification_preserves_original_eir() -> None:
    schedule = project_amortized_schedule(original_terms())
    carrying = schedule.periods[2].closing_balance
    revised = AmortizationTerms(
        "M-1", date(2026, 4, 15), carrying, 15, "0.08", AmortizationMethod.PRICE
    )
    result = modify_contract(schedule, ModificationRequest(3, revised, False))
    assert not result.derecognized
    assert result.applied_effective_interest_rate == schedule.effective_interest_rate
    assert (
        result.modification_gain_loss
        == result.carrying_amount_before - result.carrying_amount_after
    )


def test_derecognized_modification_uses_fair_value_and_new_eir() -> None:
    schedule = project_amortized_schedule(original_terms())
    carrying = schedule.periods[2].closing_balance
    revised = AmortizationTerms(
        "M-1", date(2026, 4, 15), carrying, 18, "0.09", AmortizationMethod.PRICE
    )
    fair_value = carrying - Decimal("100")
    result = modify_contract(schedule, ModificationRequest(3, revised, True, fair_value))
    assert result.derecognized
    assert result.carrying_amount_after == fair_value
    assert result.modification_gain_loss == Decimal("-100.00")
    assert result.applied_effective_interest_rate != result.original_effective_interest_rate


def test_modification_requires_matching_principal_and_fair_value_rules() -> None:
    schedule = project_amortized_schedule(original_terms())
    revised = replace(original_terms(), origination_date=date(2026, 4, 15), term_months=9)
    with pytest.raises(DomainValidationError, match="must equal"):
        modify_contract(schedule, ModificationRequest(3, revised, False))
    with pytest.raises(DomainValidationError, match="requires"):
        ModificationRequest(3, revised, True)
    with pytest.raises(DomainValidationError, match="cannot set"):
        ModificationRequest(3, revised, False, "100")


def test_modification_and_prepayment_boundaries_fail_closed() -> None:
    schedule = project_amortized_schedule(original_terms())
    revised = replace(original_terms(), origination_date=date(2026, 4, 15), term_months=9)
    with pytest.raises(DomainValidationError, match="after_period must be positive"):
        ModificationRequest(0, revised, False)
    with pytest.raises(DomainValidationError, match="outside the schedule"):
        apply_prepayment(original_terms(), 99, "1")
    with pytest.raises(DomainValidationError, match="greater than zero"):
        apply_prepayment(original_terms(), 1, "0")
    with pytest.raises(DomainValidationError, match="outside the schedule"):
        modify_contract(schedule, ModificationRequest(99, revised, False))


def test_variable_rate_prepayment_carries_latest_reset_into_revised_curve() -> None:
    variable = replace(
        original_terms(),
        rate_type=RateType.VARIABLE,
        rate_resets=(RateReset(date(2026, 2, 15), "0.15"),),
    )
    result = apply_prepayment(variable, 3, "100")
    assert result.revised_schedule is not None
    assert result.revised_schedule.periods[0].annual_rate == Decimal("0.15000000")
