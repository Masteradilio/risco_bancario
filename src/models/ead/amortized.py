"""Schedule-based EAD for amortized facilities with contract adjustments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from ...data.synthetic.events import CreditEventHistory
from ...data.synthetic.longitudinal import LongitudinalPortfolio
from ...data.synthetic.population import SyntheticPortfolio
from ...domain.contracts import (
    AmortizationMethod,
    AmortizationSchedule,
    AmortizationTerms,
    ModificationResult,
    PrepaymentResult,
    project_amortized_schedule,
)
from ...domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class AmortizedEADPolicy:
    policy_version: str
    effective_from: date
    evidence_status: str
    amortized_balance_basis: str
    default_timing: str
    include_accrued_interest: bool
    include_undrawn_amount_for_amortized: bool
    prepayment_treatment: str
    modification_treatment: str
    sha256: str


@dataclass(frozen=True, slots=True)
class AmortizedEADResult:
    contract_id: str
    default_date: date
    schedule_source: str
    default_period_number: int | None
    period_opening_balance: Decimal
    scheduled_principal: Decimal
    total_prepayment_applied: Decimal
    modification_gain_loss: Decimal
    ead_at_default: Decimal
    adjustments_applied: tuple[str, ...]
    policy_version: str
    policy_sha256: str


@dataclass(frozen=True, slots=True)
class AmortizedDefaultEADRecord:
    default_id: str
    contract_id: str
    product_code: str
    default_date: date
    projected_ead: Decimal
    observed_ead: Decimal
    absolute_error: Decimal
    predefault_term_extension_observed: bool
    policy_version: str
    policy_sha256: str


@dataclass(frozen=True, slots=True)
class AmortizedDefaultEADDataset:
    records: tuple[AmortizedDefaultEADRecord, ...]
    version: str
    policy_version: str
    policy_sha256: str


def load_amortized_ead_policy(path: Path) -> AmortizedEADPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document["schema_version"] != "1.0.0":
        raise DomainValidationError("unsupported amortized EAD policy schema")
    expected_basis = "last_observable_period_opening_before_default"
    expected_timing = "before_scheduled_payment_on_default_date"
    if (
        document["amortized_balance_basis"] != expected_basis
        or document["default_timing"] != expected_timing
        or document["include_accrued_interest"] is not False
        or document["include_undrawn_amount_for_amortized"] is not False
    ):
        raise DomainValidationError("unsupported amortized EAD measurement convention")
    return AmortizedEADPolicy(
        document["policy_version"],
        date.fromisoformat(document["effective_from"]),
        document["evidence_status"],
        document["amortized_balance_basis"],
        document["default_timing"],
        document["include_accrued_interest"],
        document["include_undrawn_amount_for_amortized"],
        document["prepayment_treatment"],
        document["modification_treatment"],
        sha256(raw).hexdigest(),
    )


def _prepayment_date(original_schedule: AmortizationSchedule, result: PrepaymentResult) -> date:
    if result.contract_id != original_schedule.contract_id:
        raise DomainValidationError("prepayment contract differs from EAD schedule")
    if not 1 <= result.after_period <= len(original_schedule.periods):
        raise DomainValidationError("prepayment period is outside the EAD schedule")
    return original_schedule.periods[result.after_period - 1].accrual_end


def _modification_date(result: ModificationResult) -> date:
    if not result.revised_schedule.periods:
        raise DomainValidationError("modified EAD schedule must contain periods")
    return result.revised_schedule.periods[0].accrual_start


def calculate_amortized_ead(
    original_schedule: AmortizationSchedule,
    default_date: date,
    policy: AmortizedEADPolicy,
    *,
    prepayments: tuple[PrepaymentResult, ...] = (),
    modifications: tuple[ModificationResult, ...] = (),
) -> AmortizedEADResult:
    if not original_schedule.periods:
        raise DomainValidationError("amortized EAD schedule must contain periods")
    if default_date < original_schedule.periods[0].accrual_start:
        raise DomainValidationError("default date precedes contract origination")
    events: list[tuple[date, int, str, PrepaymentResult | ModificationResult]] = []
    for prepayment in prepayments:
        events.append(
            (
                _prepayment_date(original_schedule, prepayment),
                0,
                "prepayment",
                prepayment,
            )
        )
    for modification in modifications:
        if modification.contract_id != original_schedule.contract_id:
            raise DomainValidationError("modification contract differs from EAD schedule")
        events.append(
            (
                _modification_date(modification),
                1,
                "modification",
                modification,
            )
        )
    active_schedule = original_schedule
    source = "original_schedule"
    fully_prepaid = False
    total_prepayment = Decimal("0")
    modification_gain_loss = Decimal("0")
    applied: list[str] = []
    for event_date, _, event_type, event in sorted(events, key=lambda item: item[:2]):
        if event_date > default_date:
            continue
        if event_type == "prepayment":
            if not isinstance(event, PrepaymentResult):
                raise DomainValidationError("invalid prepayment EAD event")
            total_prepayment += event.applied_amount
            applied.append(f"prepayment_after_period_{event.after_period}")
            if event.total_prepayment:
                fully_prepaid = True
                source = "fully_prepaid"
            elif event.revised_schedule is not None:
                active_schedule = event.revised_schedule
                source = "prepayment_revised_schedule"
        else:
            if not isinstance(event, ModificationResult):
                raise DomainValidationError("invalid modification EAD event")
            if fully_prepaid:
                raise DomainValidationError("modification cannot follow a full prepayment")
            active_schedule = event.revised_schedule
            source = "modification_revised_schedule"
            modification_gain_loss += event.modification_gain_loss
            applied.append("modification_derecognized" if event.derecognized else "modification")
    if fully_prepaid:
        return AmortizedEADResult(
            original_schedule.contract_id,
            default_date,
            source,
            None,
            Decimal("0"),
            Decimal("0"),
            total_prepayment,
            modification_gain_loss,
            Decimal("0"),
            tuple(applied),
            policy.policy_version,
            policy.sha256,
        )
    if default_date > active_schedule.periods[-1].accrual_end:
        return AmortizedEADResult(
            original_schedule.contract_id,
            default_date,
            "matured_schedule",
            None,
            Decimal("0"),
            Decimal("0"),
            total_prepayment,
            modification_gain_loss,
            Decimal("0"),
            tuple(applied),
            policy.policy_version,
            policy.sha256,
        )
    observable = [item for item in active_schedule.periods if item.accrual_end < default_date]
    period = observable[-1] if observable else active_schedule.periods[0]
    return AmortizedEADResult(
        original_schedule.contract_id,
        default_date,
        source,
        period.period_number,
        period.opening_balance,
        period.principal,
        total_prepayment,
        modification_gain_loss,
        period.opening_balance,
        tuple(applied),
        policy.policy_version,
        policy.sha256,
    )


def _term_months(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + end.month - start.month


def build_amortized_default_ead_dataset(
    population: SyntheticPortfolio,
    history: LongitudinalPortfolio,
    events: CreditEventHistory,
    policy: AmortizedEADPolicy,
) -> AmortizedDefaultEADDataset:
    contracts = {item.contract_id: item for item in population.contracts}
    modifications = {item.contract_id: item for item in history.modifications}
    records: list[AmortizedDefaultEADRecord] = []
    for default in events.defaults:
        contract = contracts[default.contract_id]
        if default.is_redefault or contract.facility_type != "amortized":
            continue
        schedule = project_amortized_schedule(
            AmortizationTerms(
                contract.contract_id,
                contract.origination_date,
                contract.original_amount,
                _term_months(contract.origination_date, contract.maturity_date),
                contract.effective_interest_rate,
                AmortizationMethod.PRICE,
            )
        )
        result = calculate_amortized_ead(schedule, default.default_date, policy)
        modification = modifications.get(contract.contract_id)
        has_prior_extension = bool(
            modification is not None and modification.modification_date <= default.default_date
        )
        records.append(
            AmortizedDefaultEADRecord(
                default.default_id,
                default.contract_id,
                contract.product_code,
                default.default_date,
                result.ead_at_default,
                default.exposure_at_default,
                abs(result.ead_at_default - default.exposure_at_default),
                has_prior_extension,
                policy.policy_version,
                policy.sha256,
            )
        )
    return AmortizedDefaultEADDataset(tuple(records), "0.1.0", policy.policy_version, policy.sha256)
