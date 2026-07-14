"""Applicability and separate simplified expected-loss strategy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from ...domain.conventions import DecimalInput, money, rate
from ...domain.exceptions import DomainValidationError
from .provision_floor import ProvisionPortfolio, apply_provision_floor

POLICY_DIRECTORY = (
    Path(__file__).resolve().parents[3] / "config" / "regulatory" / "cmn4966_simplified"
)


class PrudentialSegment(StrEnum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
    S5 = "S5"


class RegulatoryFramework(StrEnum):
    CMN4966 = "CMN4966"
    BCB352 = "BCB352"


class ProvisionMethodology(StrEnum):
    COMPLETE = "complete"
    SIMPLIFIED = "simplified"


@dataclass(frozen=True, slots=True)
class MethodologyApplicability:
    framework: RegulatoryFramework
    segment: PrudentialSegment
    methodology: ProvisionMethodology
    rationale: str
    requires_bcb_authorization: bool


@dataclass(frozen=True, slots=True)
class SimplifiedProvisionPolicy:
    policy_version: str
    effective_from: date
    effective_to: date | None
    source_ids: tuple[str, ...]
    source_locator: str
    evidence_status: str
    maximum_days: tuple[int, ...]
    non_problem_rates: tuple[tuple[ProvisionPortfolio, tuple[Decimal, ...]], ...]
    problem_non_delinquent_rates: tuple[tuple[ProvisionPortfolio, Decimal], ...]
    delinquent_rates: tuple[tuple[ProvisionPortfolio, Decimal], ...]
    sha256: str


@dataclass(frozen=True, slots=True)
class SimplifiedProvisionResult:
    methodology: ProvisionMethodology
    estimated_expected_loss: Decimal
    incurred_loss_floor: Decimal
    additional_expected_loss_floor: Decimal
    regulatory_minimum: Decimal
    excess_expected_loss: Decimal
    final_provision: Decimal
    additional_rate: Decimal
    policy_version: str
    policy_hash: str


def resolve_methodology(
    *,
    framework: RegulatoryFramework,
    segment: PrudentialSegment,
    has_complete_method_authorization: bool = False,
    is_credit_cooperative: bool = False,
    cooperative_system_segments: tuple[PrudentialSegment, ...] = (),
    cooperative_central_has_complete_authorization: bool = False,
) -> MethodologyApplicability:
    if has_complete_method_authorization and segment != PrudentialSegment.S4:
        raise DomainValidationError("individual complete-method authorization is restricted to S4")
    if not is_credit_cooperative and (
        cooperative_system_segments or cooperative_central_has_complete_authorization
    ):
        raise DomainValidationError("cooperative-system facts require a credit cooperative")
    if segment in {PrudentialSegment.S1, PrudentialSegment.S2, PrudentialSegment.S3}:
        return MethodologyApplicability(
            framework,
            segment,
            ProvisionMethodology.COMPLETE,
            "S1-S3 use the complete methodology",
            False,
        )
    if is_credit_cooperative:
        system_has_s1_s3 = any(
            item in {PrudentialSegment.S1, PrudentialSegment.S2, PrudentialSegment.S3}
            for item in cooperative_system_segments
        )
        if system_has_s1_s3 or cooperative_central_has_complete_authorization:
            return MethodologyApplicability(
                framework,
                segment,
                ProvisionMethodology.COMPLETE,
                "cooperative-system exception to the simplified methodology",
                cooperative_central_has_complete_authorization,
            )
    if segment == PrudentialSegment.S4 and has_complete_method_authorization:
        return MethodologyApplicability(
            framework,
            segment,
            ProvisionMethodology.COMPLETE,
            "S4 has prior BCB authorization for the complete methodology",
            True,
        )
    return MethodologyApplicability(
        framework,
        segment,
        ProvisionMethodology.SIMPLIFIED,
        "S4-S5 default to the simplified methodology",
        False,
    )


def _portfolio_rates(
    document: dict[str, DecimalInput],
) -> tuple[tuple[ProvisionPortfolio, Decimal], ...]:
    return tuple(
        (portfolio, rate(document[portfolio.value], field=f"rate.{portfolio.value}"))
        for portfolio in ProvisionPortfolio
    )


def _load_policy_file(path: Path) -> SimplifiedProvisionPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    metadata = document["metadata"]
    non_problem = document["additional_rates_non_problem_by_days_past_due"]
    maximum_days = tuple(int(value) for value in non_problem["maximum_days"])
    if maximum_days != (14, 30, 60, 90):
        raise DomainValidationError("simplified policy must define the four official delay bands")
    non_problem_rates = tuple(
        (
            portfolio,
            tuple(
                rate(value, field=f"non_problem.{portfolio.value}")
                for value in non_problem[portfolio.value]
            ),
        )
        for portfolio in ProvisionPortfolio
    )
    if any(len(values) != 4 for _, values in non_problem_rates):
        raise DomainValidationError("each portfolio must define four non-problem rates")
    effective_to = metadata["effective_to"]
    return SimplifiedProvisionPolicy(
        metadata["policy_version"],
        date.fromisoformat(metadata["effective_from"]),
        date.fromisoformat(effective_to) if effective_to else None,
        tuple(metadata["source_ids"]),
        metadata["source_locator"],
        metadata["evidence_status"],
        maximum_days,
        non_problem_rates,
        _portfolio_rates(document["additional_rates_problem_non_delinquent"]),
        _portfolio_rates(document["additional_rates_delinquent"]),
        sha256(raw).hexdigest(),
    )


def load_simplified_provision_policy(
    reference_date: date, directory: Path = POLICY_DIRECTORY
) -> SimplifiedProvisionPolicy:
    policies = tuple(_load_policy_file(path) for path in sorted(directory.glob("*.json")))
    matches = tuple(
        policy
        for policy in policies
        if policy.effective_from <= reference_date
        and (policy.effective_to is None or reference_date <= policy.effective_to)
    )
    if len(matches) != 1:
        raise DomainValidationError(
            f"unsupported or ambiguous simplified policy for {reference_date.isoformat()}"
        )
    return matches[0]


def _additional_rate(
    policy: SimplifiedProvisionPolicy,
    portfolio: ProvisionPortfolio,
    days_past_due: int,
    problem_asset: bool,
) -> Decimal:
    if days_past_due > 90:
        return dict(policy.delinquent_rates)[portfolio]
    if problem_asset:
        return dict(policy.problem_non_delinquent_rates)[portfolio]
    rates = dict(policy.non_problem_rates)[portfolio]
    return next(
        rate_value
        for maximum, rate_value in zip(policy.maximum_days, rates, strict=True)
        if days_past_due <= maximum
    )


def calculate_simplified_provision(
    *,
    applicability: MethodologyApplicability,
    reference_date: date,
    portfolio: ProvisionPortfolio,
    gross_carrying_amount: DecimalInput,
    estimated_expected_loss: DecimalInput,
    days_past_due: int,
    problem_asset: bool,
    default_date: date | None,
    policy: SimplifiedProvisionPolicy | None = None,
) -> SimplifiedProvisionResult:
    if applicability.methodology != ProvisionMethodology.SIMPLIFIED:
        raise DomainValidationError("simplified calculator rejects a complete-methodology route")
    if days_past_due < 0:
        raise DomainValidationError("days_past_due must be non-negative")
    if days_past_due > 90 and not problem_asset:
        raise DomainValidationError("a delinquent asset must be characterized as problem asset")
    active_policy = policy or load_simplified_provision_policy(reference_date)
    gross = money(gross_carrying_amount, field="gross_carrying_amount")
    expected = money(estimated_expected_loss, field="estimated_expected_loss")
    if expected > gross:
        raise DomainValidationError("estimated_expected_loss cannot exceed gross_carrying_amount")
    floor_result = apply_provision_floor(
        reference_date=reference_date,
        portfolio=portfolio,
        gross_carrying_amount=gross,
        calculated_ecl="0",
        days_past_due=days_past_due,
        default_date=default_date,
    )
    additional_rate = _additional_rate(active_policy, portfolio, days_past_due, problem_asset)
    additional = money(gross * additional_rate, field="additional_expected_loss_floor")
    regulatory_minimum = min(gross, floor_result.regulatory_floor + additional)
    excess = max(Decimal("0.00"), expected - regulatory_minimum)
    final = regulatory_minimum + excess
    return SimplifiedProvisionResult(
        ProvisionMethodology.SIMPLIFIED,
        expected,
        floor_result.regulatory_floor,
        additional,
        regulatory_minimum,
        excess,
        final,
        additional_rate,
        active_policy.policy_version,
        active_policy.sha256,
    )
