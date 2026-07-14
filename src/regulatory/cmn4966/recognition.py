"""Modification, derecognition, write-off and post-write-off recognition ledger."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import StrEnum

from ...domain.contracts.amortization import AmortizationSchedule, AmortizationTerms
from ...domain.contracts.modifications import (
    ModificationRequest,
    ModificationResult,
    modify_contract,
)
from ...domain.conventions import DecimalInput, money, non_empty
from ...domain.exceptions import DomainValidationError, TemporalConsistencyError


@dataclass(frozen=True, slots=True)
class ModificationFacts:
    contractual_rights_expired: bool = False
    legal_novation: bool = False
    counterparty_changed: bool = False
    currency_changed: bool = False
    instrument_type_changed: bool = False
    sppi_result_changed: bool = False


@dataclass(frozen=True, slots=True)
class ModificationDecision:
    derecognize: bool
    reasons: tuple[str, ...]
    requires_original_eir: bool
    source_locator: str = "Resolução CMN nº 4.966/2021, arts. 22-35"


class RecognitionEventType(StrEnum):
    PARTIAL_WRITE_OFF = "partial_write_off"
    TOTAL_WRITE_OFF = "total_write_off"
    POST_WRITE_OFF_RECOVERY = "post_write_off_recovery"


@dataclass(frozen=True, slots=True)
class RecognitionEvent:
    sequence: int
    event_date: date
    event_type: RecognitionEventType
    amount: Decimal
    allowance_released: Decimal
    direct_profit_or_loss: Decimal
    evidence_id: str


@dataclass(frozen=True, slots=True)
class WriteOffLedger:
    contract_id: str
    gross_carrying_amount: Decimal
    loss_allowance: Decimal
    cumulative_write_off: Decimal
    cumulative_post_write_off_recovery: Decimal
    events: tuple[RecognitionEvent, ...]


def assess_modification(facts: ModificationFacts) -> ModificationDecision:
    reasons = tuple(
        name
        for name in (
            "contractual_rights_expired",
            "legal_novation",
            "counterparty_changed",
            "currency_changed",
            "instrument_type_changed",
            "sppi_result_changed",
        )
        if getattr(facts, name)
    )
    derecognize = bool(reasons)
    return ModificationDecision(derecognize, reasons, not derecognize)


def account_for_modification(
    *,
    original_schedule: AmortizationSchedule,
    after_period: int,
    revised_terms: AmortizationTerms,
    decision: ModificationDecision,
    replacement_fair_value: DecimalInput | None = None,
) -> ModificationResult:
    if decision.derecognize and replacement_fair_value is None:
        raise DomainValidationError("derecognition decision requires replacement fair value")
    if not decision.derecognize and replacement_fair_value is not None:
        raise DomainValidationError("non-derecognition decision preserves the original EIR")
    return modify_contract(
        original_schedule,
        ModificationRequest(
            after_period,
            revised_terms,
            decision.derecognize,
            replacement_fair_value,
        ),
    )


def open_writeoff_ledger(
    contract_id: str,
    gross_carrying_amount: DecimalInput,
    loss_allowance: DecimalInput,
) -> WriteOffLedger:
    gross = money(gross_carrying_amount, field="gross_carrying_amount")
    allowance = money(loss_allowance, field="loss_allowance")
    if gross == 0:
        raise DomainValidationError("write-off ledger requires a positive gross carrying amount")
    if allowance > gross:
        raise DomainValidationError("loss allowance cannot exceed gross carrying amount")
    return WriteOffLedger(
        non_empty(contract_id, field="contract_id"),
        gross,
        allowance,
        Decimal("0.00"),
        Decimal("0.00"),
        (),
    )


def _validate_event_date(ledger: WriteOffLedger, event_date: date) -> None:
    if ledger.events and event_date < ledger.events[-1].event_date:
        raise TemporalConsistencyError("recognition events must be chronological")


def write_off(
    ledger: WriteOffLedger,
    *,
    event_date: date,
    amount: DecimalInput,
    recovery_not_probable: bool,
    evidence_id: str,
) -> WriteOffLedger:
    _validate_event_date(ledger, event_date)
    evidence = non_empty(evidence_id, field="evidence_id")
    writeoff = money(amount, field="writeoff_amount")
    if writeoff == 0:
        raise DomainValidationError("writeoff_amount must be positive")
    if not recovery_not_probable:
        raise DomainValidationError("write-off requires evidence that recovery is not probable")
    if writeoff > ledger.gross_carrying_amount:
        raise DomainValidationError("writeoff_amount cannot exceed gross carrying amount")
    allowance_released = min(writeoff, ledger.loss_allowance)
    direct_loss = writeoff - allowance_released
    event_type = (
        RecognitionEventType.TOTAL_WRITE_OFF
        if writeoff == ledger.gross_carrying_amount
        else RecognitionEventType.PARTIAL_WRITE_OFF
    )
    event = RecognitionEvent(
        len(ledger.events) + 1,
        event_date,
        event_type,
        writeoff,
        allowance_released,
        -direct_loss,
        evidence,
    )
    return replace(
        ledger,
        gross_carrying_amount=ledger.gross_carrying_amount - writeoff,
        loss_allowance=ledger.loss_allowance - allowance_released,
        cumulative_write_off=ledger.cumulative_write_off + writeoff,
        events=ledger.events + (event,),
    )


def recognize_post_writeoff_recovery(
    ledger: WriteOffLedger,
    *,
    event_date: date,
    amount: DecimalInput,
    evidence_id: str,
) -> WriteOffLedger:
    _validate_event_date(ledger, event_date)
    evidence = non_empty(evidence_id, field="evidence_id")
    recovery = money(amount, field="post_writeoff_recovery")
    if recovery == 0:
        raise DomainValidationError("post_writeoff_recovery must be positive")
    remaining = ledger.cumulative_write_off - ledger.cumulative_post_write_off_recovery
    if ledger.cumulative_write_off == 0:
        raise DomainValidationError("post-write-off recovery requires a prior write-off")
    if recovery > remaining:
        raise DomainValidationError("post-write-off recovery cannot exceed unrecovered write-off")
    event = RecognitionEvent(
        len(ledger.events) + 1,
        event_date,
        RecognitionEventType.POST_WRITE_OFF_RECOVERY,
        recovery,
        Decimal("0.00"),
        recovery,
        evidence,
    )
    return replace(
        ledger,
        cumulative_post_write_off_recovery=(ledger.cumulative_post_write_off_recovery + recovery),
        events=ledger.events + (event,),
    )
