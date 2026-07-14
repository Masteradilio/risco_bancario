"""Single explainable SICR assessment engine with versioned policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from ...domain.conventions import DecimalInput, non_empty, rate
from ...domain.exceptions import DomainValidationError
from .origination import OriginationRiskBaseline


@dataclass(frozen=True, slots=True)
class LowCreditRiskPolicy:
    enabled: bool
    eligible_ratings: tuple[str, ...]
    maximum_current_lifetime_pd: Decimal


@dataclass(frozen=True, slots=True)
class SICRPolicy:
    schema_version: str
    policy_version: str
    effective_from: date
    evidence_status: str
    justification: str
    absolute_lifetime_pd_increase: Decimal
    relative_lifetime_pd_ratio: Decimal
    downgrade_notches: int
    days_past_due_backstop: int
    rating_order: tuple[str, ...]
    low_credit_risk: LowCreditRiskPolicy
    sha256: str


@dataclass(frozen=True, slots=True)
class SICRAssessmentInput:
    baseline: OriginationRiskBaseline
    reference_date: date
    current_lifetime_pd: DecimalInput
    current_rating: str
    days_past_due: int = 0
    watchlist: bool = False
    concession_or_forbearance: bool = False
    qualitative_events: tuple[str, ...] = ()
    apply_low_credit_risk_exemption: bool = True


@dataclass(frozen=True, slots=True)
class SICRDecision:
    contract_id: str
    reference_date: date
    is_sicr: bool
    origination_lifetime_pd: Decimal
    current_lifetime_pd: Decimal
    absolute_change: Decimal
    relative_ratio: Decimal | None
    rating_downgrade_notches: int
    low_credit_risk_exemption_applied: bool
    active_triggers: tuple[str, ...]
    suppressed_triggers: tuple[str, ...]
    reasons: tuple[str, ...]
    policy_version: str
    policy_sha256: str
    evidence_status: str


def load_sicr_policy(path: Path) -> SICRPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document["schema_version"] != "1.0.0":
        raise DomainValidationError("unsupported SICR policy schema")
    rating_order = tuple(document["rating_order"])
    if not rating_order or len(rating_order) != len(set(rating_order)):
        raise DomainValidationError("SICR rating_order must be unique and non-empty")
    low = document["low_credit_risk"]
    eligible = tuple(low["eligible_ratings"])
    if not set(eligible).issubset(rating_order):
        raise DomainValidationError("low-credit-risk ratings must exist in rating_order")
    absolute = rate(document["absolute_lifetime_pd_increase"], field="absolute_threshold")
    maximum = rate(low["maximum_current_lifetime_pd"], field="low_credit_risk_maximum")
    ratio = Decimal(str(document["relative_lifetime_pd_ratio"]))
    downgrade = int(document["downgrade_notches"])
    backstop = int(document["days_past_due_backstop"])
    if ratio <= 1 or downgrade <= 0 or backstop <= 0:
        raise DomainValidationError("SICR thresholds must be positive and ratio greater than one")
    return SICRPolicy(
        document["schema_version"],
        non_empty(document["policy_version"], field="policy_version"),
        date.fromisoformat(document["effective_from"]),
        non_empty(document["evidence_status"], field="evidence_status"),
        non_empty(document["justification"], field="justification"),
        absolute,
        ratio,
        downgrade,
        backstop,
        rating_order,
        LowCreditRiskPolicy(bool(low["enabled"]), eligible, maximum),
        sha256(raw).hexdigest(),
    )


def assess_sicr(value: SICRAssessmentInput, policy: SICRPolicy) -> SICRDecision:
    current_pd = rate(value.current_lifetime_pd, field="current_lifetime_pd")
    current_rating = non_empty(value.current_rating, field="current_rating")
    if value.reference_date < value.baseline.recognition_date:
        raise DomainValidationError("SICR reference_date cannot precede recognition")
    if value.days_past_due < 0:
        raise DomainValidationError("days_past_due must be non-negative")
    if (
        current_rating not in policy.rating_order
        or value.baseline.rating not in policy.rating_order
    ):
        raise DomainValidationError("rating is not present in SICR policy")
    origination_pd = value.baseline.lifetime_pd_original_term
    absolute_change = current_pd - origination_pd
    relative_ratio = current_pd / origination_pd if origination_pd > 0 else None
    downgrade = max(
        0,
        policy.rating_order.index(current_rating)
        - policy.rating_order.index(value.baseline.rating),
    )

    quantitative: list[str] = []
    if absolute_change >= policy.absolute_lifetime_pd_increase:
        quantitative.append("absolute_lifetime_pd_increase")
    if (relative_ratio is None and current_pd > 0) or (
        relative_ratio is not None and relative_ratio >= policy.relative_lifetime_pd_ratio
    ):
        quantitative.append("relative_lifetime_pd_increase")

    direct: list[str] = []
    if downgrade >= policy.downgrade_notches:
        direct.append("rating_downgrade")
    if value.days_past_due >= policy.days_past_due_backstop:
        direct.append("days_past_due_backstop")
    if value.watchlist:
        direct.append("watchlist")
    if value.concession_or_forbearance:
        direct.append("concession_or_forbearance")
    direct.extend(
        f"qualitative:{non_empty(item, field='qualitative_event')}"
        for item in value.qualitative_events
    )

    exemption = (
        policy.low_credit_risk.enabled
        and value.apply_low_credit_risk_exemption
        and current_rating in policy.low_credit_risk.eligible_ratings
        and current_pd <= policy.low_credit_risk.maximum_current_lifetime_pd
        and not direct
    )
    active = direct + ([] if exemption else quantitative)
    suppressed = quantitative if exemption else []
    reasons = [f"active:{item}" for item in active]
    reasons.extend(f"suppressed_by_low_credit_risk:{item}" for item in suppressed)
    if not reasons:
        reasons.append("no_sicr_trigger")
    return SICRDecision(
        value.baseline.contract_id,
        value.reference_date,
        bool(active),
        origination_pd,
        current_pd,
        absolute_change,
        relative_ratio,
        downgrade,
        exemption,
        tuple(active),
        tuple(suppressed),
        tuple(reasons),
        policy.policy_version,
        policy.sha256,
        policy.evidence_status,
    )
