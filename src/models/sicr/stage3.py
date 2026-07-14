"""Unified operational default and accounting Stage 3 decision."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ...domain.conventions import non_empty
from ...domain.exceptions import DomainValidationError
from ..pd.default_definition import (
    DefaultAssessmentInput,
    DefaultDecision,
    LoadedDefaultPolicy,
    assess_default,
)


@dataclass(frozen=True, slots=True)
class CounterpartyDefaultEvidence:
    contract_id: str
    is_default: bool
    exception_reason: str | None = None


@dataclass(frozen=True, slots=True)
class Stage3AssessmentInput:
    default_input: DefaultAssessmentInput
    concession_or_forbearance: bool = False
    financial_difficulty: bool = False
    counterparty_defaults: tuple[CounterpartyDefaultEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class Stage3Decision:
    contract_id: str
    counterparty_id: str
    is_stage3: bool
    operational_default: bool
    accounting_credit_impaired: bool
    assessment_level: str
    reasons: tuple[str, ...]
    contagion_contracts: tuple[str, ...]
    contagion_exceptions: tuple[str, ...]
    default_decision: DefaultDecision
    policy_version: str
    policy_sha256: str
    evidence_status: str


def _with_distressed_restructuring(value: Stage3AssessmentInput) -> DefaultAssessmentInput:
    item = value.default_input
    if not (value.concession_or_forbearance and value.financial_difficulty):
        return item
    indicators = tuple(dict.fromkeys((*item.qualitative_indicators, "distressed_restructuring")))
    return replace(item, qualitative_indicators=indicators)


def assess_stage3(value: Stage3AssessmentInput, loaded: LoadedDefaultPolicy) -> Stage3Decision:
    policy = loaded.policy
    own = assess_default(_with_distressed_restructuring(value), policy)
    contagion_contracts: list[str] = []
    exceptions: list[str] = []
    seen_contracts: set[str] = set()
    for evidence in value.counterparty_defaults:
        contract_id = non_empty(evidence.contract_id, field="counterparty_default_contract_id")
        if contract_id == value.default_input.contract_id or contract_id in seen_contracts:
            raise DomainValidationError("counterparty default evidence must be unique and external")
        seen_contracts.add(contract_id)
        if not evidence.is_default:
            continue
        if evidence.exception_reason is not None:
            reason = non_empty(evidence.exception_reason, field="contagion_exception_reason")
            if reason not in policy.counterparty_contagion.exception_reasons:
                raise DomainValidationError("unknown counterparty contagion exception")
            exceptions.append(f"{contract_id}:{reason}")
            continue
        if policy.counterparty_contagion.enabled and own.assessment_level == "counterparty":
            contagion_contracts.append(contract_id)

    reasons = list(own.reasons)
    reasons.extend(f"counterparty_contagion:{item}" for item in contagion_contracts)
    is_default = own.is_default or bool(contagion_contracts)
    return Stage3Decision(
        value.default_input.contract_id,
        value.default_input.counterparty_id,
        is_default,
        is_default,
        is_default,
        own.assessment_level,
        tuple(reasons),
        tuple(contagion_contracts),
        tuple(exceptions),
        own,
        policy.metadata.version,
        loaded.configuration_hash,
        policy.metadata.status,
    )
