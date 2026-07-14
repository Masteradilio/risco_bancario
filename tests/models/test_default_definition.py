from datetime import date
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError
from src.models.pd import (
    CureEvidence,
    DefaultAssessmentInput,
    assess_cure,
    assess_default,
    build_default_target,
    load_default_policy,
)


@pytest.fixture(scope="module")
def policy():
    return load_default_policy().policy


def assessment(policy, **overrides):
    values = {
        "contract_id": "C-1",
        "counterparty_id": "CP-1",
        "product_code": "personal_loan",
        "assessment_date": date(2026, 7, 14),
        "days_past_due": 0,
        "past_due_amount": Decimal("0"),
        "exposure": Decimal("1000"),
    }
    values.update(overrides)
    return assess_default(DefaultAssessmentInput(**values), policy)


def test_policy_is_versioned_and_uses_greater_than_90_days_backstop(policy) -> None:
    loaded = load_default_policy()
    assert policy.metadata.version == "2026.07.1"
    assert policy.backstop_days_past_due == 91
    assert len(loaded.configuration_hash) == 64


def test_dpd_backstop_requires_positive_past_due_amount(policy) -> None:
    assert not assessment(policy, days_past_due=90).is_default
    assert assessment(policy, days_past_due=91, past_due_amount=Decimal("0.01")).is_default
    assert not assessment(policy, days_past_due=91).is_default


def test_qualitative_indicator_can_trigger_before_backstop(policy) -> None:
    decision = assessment(policy, qualitative_indicators=("financial_incapacity",))
    assert decision.is_default
    assert decision.reasons == ("financial_incapacity",)


def test_product_populations_have_explicit_assessment_levels(policy) -> None:
    assert assessment(policy, product_code="credit_card").assessment_level == "facility"
    assert assessment(policy, product_code="financial_guarantee").assessment_level == "counterparty"
    assert (
        assessment(policy, product_code="acquired_distressed").assessment_level == "poci_separate"
    )


def test_unknown_product_or_indicator_is_rejected(policy) -> None:
    with pytest.raises(DomainValidationError, match="no default assessment"):
        assessment(policy, product_code="unknown")
    with pytest.raises(DomainValidationError, match="unknown qualitative"):
        assessment(policy, qualitative_indicators=("invented",))


def test_cure_requires_all_evidence_and_operational_payment_period(policy) -> None:
    eligible = assess_cure(CureEvidence(True, 3, True, True), policy)
    assert eligible.eligible
    assert eligible.redefault_monitor_months == 12
    failed = assess_cure(CureEvidence(False, 2, False, False), policy)
    assert not failed.eligible
    assert len(failed.failed_conditions) == 4


def test_low_frequency_cure_exception_requires_90_days_evidence(policy) -> None:
    eligible = assess_cure(CureEvidence(True, 0, True, True, 3, 90), policy)
    assert eligible.eligible
    assert not assess_cure(CureEvidence(True, 0, True, True, 3, 89), policy).eligible


def test_default_target_exclusions_and_complete_horizon(policy) -> None:
    observation = date(2023, 1, 1)
    assert (
        build_default_target(
            observation,
            date(2024, 1, 1),
            date(2023, 8, 1),
            acquired_credit_impaired=False,
            already_defaulted=False,
            policy=policy,
        ).value
        == 1
    )
    assert (
        build_default_target(
            observation,
            date(2024, 1, 1),
            None,
            acquired_credit_impaired=True,
            already_defaulted=False,
            policy=policy,
        ).exclusion_reason
        == "poci_separate_population"
    )
    assert (
        build_default_target(
            observation,
            date(2023, 12, 1),
            None,
            acquired_credit_impaired=False,
            already_defaulted=False,
            policy=policy,
        ).exclusion_reason
        == "incomplete_outcome_horizon"
    )
