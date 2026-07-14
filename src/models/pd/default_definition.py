"""Versioned, auditable default, cure and PD-target definitions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...domain.exceptions import DomainValidationError

POLICY_PATH = Path(__file__).resolve().parents[3] / "config" / "default_policy" / "2026.07.1.json"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DefaultPolicyMetadata(StrictModel):
    version: str = Field(min_length=1)
    effective_from: date
    status: str = Field(min_length=1)
    sources: tuple[str, ...] = Field(min_length=1)


class MaterialityPolicy(StrictModel):
    absolute_amount_brl: Decimal = Field(ge=0)
    relative_to_exposure: Decimal = Field(ge=0, le=1)
    status: str = Field(min_length=1)


class CurePolicy(StrictModel):
    minimum_timely_payment_months: int = Field(ge=1)
    minimum_low_frequency_evidence_days: int = Field(ge=1)
    redefault_monitor_months: int = Field(ge=1)
    status: str = Field(min_length=1)


class TargetPolicy(StrictModel):
    horizon_months: int = Field(ge=1)
    exclude_poci: bool
    exclude_already_defaulted: bool
    require_complete_horizon: bool


class DefaultPolicy(StrictModel):
    metadata: DefaultPolicyMetadata
    backstop_days_past_due: int = Field(ge=1)
    materiality: MaterialityPolicy
    qualitative_indicators: tuple[str, ...] = Field(min_length=1)
    product_assessment_level: dict[str, Literal["facility", "counterparty", "poci_separate"]]
    cure: CurePolicy
    target: TargetPolicy

    @model_validator(mode="after")
    def unique_and_complete(self) -> DefaultPolicy:
        if len(set(self.qualitative_indicators)) != len(self.qualitative_indicators):
            raise ValueError("qualitative indicators must be unique")
        if self.backstop_days_past_due != 91:
            raise ValueError("CMN/BCB greater-than-90-days backstop must operationalize at 91")
        return self


@dataclass(frozen=True, slots=True)
class LoadedDefaultPolicy:
    policy: DefaultPolicy
    configuration_hash: str
    source_path: Path


@dataclass(frozen=True, slots=True)
class DefaultAssessmentInput:
    contract_id: str
    counterparty_id: str
    product_code: str
    assessment_date: date
    days_past_due: int
    past_due_amount: Decimal
    exposure: Decimal
    qualitative_indicators: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DefaultDecision:
    is_default: bool
    assessment_level: str
    reasons: tuple[str, ...]
    policy_version: str


@dataclass(frozen=True, slots=True)
class CureEvidence:
    no_past_due_amounts: bool
    timely_payment_months: int
    contractual_obligations_met: bool
    full_payment_capacity_evidenced: bool
    payment_interval_months: int = 1
    capacity_evidence_days: int = 0


@dataclass(frozen=True, slots=True)
class CureDecision:
    eligible: bool
    failed_conditions: tuple[str, ...]
    redefault_monitor_months: int
    policy_version: str


@dataclass(frozen=True, slots=True)
class DefaultTarget:
    value: int | None
    exclusion_reason: str | None


def load_default_policy(path: str | Path = POLICY_PATH) -> LoadedDefaultPolicy:
    source_path = Path(path).resolve()
    raw = json.loads(source_path.read_text(encoding="utf-8"), parse_float=str)
    policy = DefaultPolicy.model_validate(raw)
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return LoadedDefaultPolicy(policy, sha256(canonical.encode()).hexdigest(), source_path)


def assess_default(item: DefaultAssessmentInput, policy: DefaultPolicy) -> DefaultDecision:
    if item.days_past_due < 0 or item.past_due_amount < 0 or item.exposure <= 0:
        raise DomainValidationError("default assessment amounts and days are invalid")
    level = policy.product_assessment_level.get(item.product_code)
    if level is None:
        raise DomainValidationError("product has no default assessment policy")
    unknown = set(item.qualitative_indicators) - set(policy.qualitative_indicators)
    if unknown:
        raise DomainValidationError(f"unknown qualitative default indicators: {sorted(unknown)}")
    material = (
        item.past_due_amount > policy.materiality.absolute_amount_brl
        and item.past_due_amount / item.exposure > policy.materiality.relative_to_exposure
    )
    reasons = list(item.qualitative_indicators)
    if item.days_past_due >= policy.backstop_days_past_due and material:
        reasons.append("days_past_due_backstop")
    return DefaultDecision(bool(reasons), level, tuple(reasons), policy.metadata.version)


def assess_cure(evidence: CureEvidence, policy: DefaultPolicy) -> CureDecision:
    failures: list[str] = []
    if not evidence.no_past_due_amounts:
        failures.append("past_due_amounts_remain")
    low_frequency_exception = (
        evidence.payment_interval_months >= 3
        and evidence.capacity_evidence_days >= policy.cure.minimum_low_frequency_evidence_days
    )
    if (
        evidence.timely_payment_months < policy.cure.minimum_timely_payment_months
        and not low_frequency_exception
    ):
        failures.append("insufficient_timely_payment_period")
    if not evidence.contractual_obligations_met:
        failures.append("contractual_obligations_not_met")
    if not evidence.full_payment_capacity_evidenced:
        failures.append("full_payment_capacity_not_evidenced")
    return CureDecision(
        not failures,
        tuple(failures),
        policy.cure.redefault_monitor_months,
        policy.metadata.version,
    )


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    return date(year, month, min(value.day, 28))


def build_default_target(
    observation_date: date,
    data_end_date: date,
    default_date: date | None,
    *,
    acquired_credit_impaired: bool,
    already_defaulted: bool,
    policy: DefaultPolicy,
) -> DefaultTarget:
    if acquired_credit_impaired and policy.target.exclude_poci:
        return DefaultTarget(None, "poci_separate_population")
    if already_defaulted and policy.target.exclude_already_defaulted:
        return DefaultTarget(None, "already_defaulted_at_observation")
    horizon_end = _add_months(observation_date, policy.target.horizon_months)
    if policy.target.require_complete_horizon and data_end_date < horizon_end:
        return DefaultTarget(None, "incomplete_outcome_horizon")
    value = int(default_date is not None and observation_date < default_date <= horizon_end)
    return DefaultTarget(value, None)
