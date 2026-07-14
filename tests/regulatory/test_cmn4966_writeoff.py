from datetime import date
from decimal import Decimal

import pytest

from src.domain.contracts import (
    AmortizationMethod,
    AmortizationTerms,
    project_amortized_schedule,
)
from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.regulatory.cmn4966 import (
    ModificationFacts,
    RecognitionEventType,
    account_for_modification,
    assess_modification,
    open_writeoff_ledger,
    recognize_post_writeoff_recovery,
    write_off,
)


def _terms() -> AmortizationTerms:
    return AmortizationTerms(
        "M-REG", date(2026, 1, 15), "12000", 12, "0.12", AmortizationMethod.PRICE
    )


def _revised(after_period: int, term_months: int = 15) -> tuple[object, AmortizationTerms]:
    schedule = project_amortized_schedule(_terms())
    carrying = schedule.periods[after_period - 1].closing_balance
    terms = AmortizationTerms(
        "M-REG",
        schedule.periods[after_period - 1].accrual_end,
        carrying,
        term_months,
        "0.08",
        AmortizationMethod.PRICE,
    )
    return schedule, terms


def test_non_substantial_modification_preserves_original_eir() -> None:
    schedule, revised = _revised(3)
    decision = assess_modification(ModificationFacts())
    result = account_for_modification(
        original_schedule=schedule,
        after_period=3,
        revised_terms=revised,
        decision=decision,
    )
    assert not decision.derecognize
    assert decision.requires_original_eir
    assert not result.derecognized
    assert result.applied_effective_interest_rate == result.original_effective_interest_rate


def test_substantial_modification_derecognizes_and_uses_new_eir() -> None:
    schedule, revised = _revised(3, 18)
    decision = assess_modification(ModificationFacts(legal_novation=True))
    fair_value = schedule.periods[2].closing_balance - Decimal("100")
    result = account_for_modification(
        original_schedule=schedule,
        after_period=3,
        revised_terms=revised,
        decision=decision,
        replacement_fair_value=fair_value,
    )
    assert decision.derecognize
    assert decision.reasons == ("legal_novation",)
    assert result.derecognized
    assert result.modification_gain_loss == Decimal("-100.00")
    assert result.applied_effective_interest_rate != result.original_effective_interest_rate


def test_modification_route_and_fair_value_must_be_consistent() -> None:
    schedule, revised = _revised(3)
    with pytest.raises(DomainValidationError, match="requires replacement"):
        account_for_modification(
            original_schedule=schedule,
            after_period=3,
            revised_terms=revised,
            decision=assess_modification(ModificationFacts(currency_changed=True)),
        )
    with pytest.raises(DomainValidationError, match="preserves the original EIR"):
        account_for_modification(
            original_schedule=schedule,
            after_period=3,
            revised_terms=revised,
            decision=assess_modification(ModificationFacts()),
            replacement_fair_value="100",
        )


def test_partial_and_total_writeoff_reduce_gross_and_allowance_separately() -> None:
    ledger = open_writeoff_ledger("C-1", "1000", "800")
    ledger = write_off(
        ledger,
        event_date=date(2026, 7, 1),
        amount="300",
        recovery_not_probable=True,
        evidence_id="COLLECTION-001",
    )
    assert ledger.events[-1].event_type == RecognitionEventType.PARTIAL_WRITE_OFF
    assert ledger.gross_carrying_amount == Decimal("700.00")
    assert ledger.loss_allowance == Decimal("500.00")
    ledger = write_off(
        ledger,
        event_date=date(2026, 8, 1),
        amount="700",
        recovery_not_probable=True,
        evidence_id="COLLECTION-002",
    )
    assert ledger.events[-1].event_type == RecognitionEventType.TOTAL_WRITE_OFF
    assert ledger.gross_carrying_amount == Decimal("0.00")
    assert ledger.loss_allowance == Decimal("0.00")
    assert ledger.events[-1].direct_profit_or_loss == Decimal("-200.00")


def test_post_writeoff_recovery_is_income_without_reinstating_asset() -> None:
    ledger = write_off(
        open_writeoff_ledger("C-2", "1000", "1000"),
        event_date=date(2026, 7, 1),
        amount="1000",
        recovery_not_probable=True,
        evidence_id="WO-1",
    )
    recovered = recognize_post_writeoff_recovery(
        ledger,
        event_date=date(2026, 9, 1),
        amount="120",
        evidence_id="REC-1",
    )
    event = recovered.events[-1]
    assert event.event_type == RecognitionEventType.POST_WRITE_OFF_RECOVERY
    assert event.direct_profit_or_loss == Decimal("120.00")
    assert recovered.gross_carrying_amount == Decimal("0.00")
    assert recovered.cumulative_post_write_off_recovery == Decimal("120.00")


def test_writeoff_and_recovery_controls_fail_closed() -> None:
    ledger = open_writeoff_ledger("C-3", "1000", "500")
    with pytest.raises(DomainValidationError, match="not probable"):
        write_off(
            ledger,
            event_date=date(2026, 7, 1),
            amount="10",
            recovery_not_probable=False,
            evidence_id="NO-WO",
        )
    with pytest.raises(DomainValidationError, match="prior write-off"):
        recognize_post_writeoff_recovery(
            ledger, event_date=date(2026, 7, 1), amount="10", evidence_id="REC"
        )
    written = write_off(
        ledger,
        event_date=date(2026, 8, 1),
        amount="100",
        recovery_not_probable=True,
        evidence_id="WO",
    )
    with pytest.raises(DomainValidationError, match="cannot exceed"):
        recognize_post_writeoff_recovery(
            written, event_date=date(2026, 9, 1), amount="101", evidence_id="REC"
        )
    with pytest.raises(TemporalConsistencyError, match="chronological"):
        recognize_post_writeoff_recovery(
            written, event_date=date(2026, 7, 1), amount="10", evidence_id="REC"
        )
