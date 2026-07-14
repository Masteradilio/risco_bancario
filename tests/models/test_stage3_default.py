from datetime import date
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError
from src.models.pd import DefaultAssessmentInput, load_default_policy
from src.models.sicr import (
    CounterpartyDefaultEvidence,
    Stage3AssessmentInput,
    assess_stage3,
)


@pytest.fixture(scope="module")
def policy():
    return load_default_policy()


def default_input(**overrides):
    values = {
        "contract_id": "CT-1",
        "counterparty_id": "CP-1",
        "product_code": "personal_loan",
        "assessment_date": date(2026, 7, 14),
        "days_past_due": 0,
        "past_due_amount": Decimal("0"),
        "exposure": Decimal("1000"),
        "qualitative_indicators": (),
    }
    values.update(overrides)
    return DefaultAssessmentInput(**values)


def test_operational_default_and_accounting_stage3_are_unified(policy) -> None:
    result = assess_stage3(
        Stage3AssessmentInput(
            default_input=default_input(days_past_due=91, past_due_amount=Decimal("1"))
        ),
        policy,
    )
    assert result.is_stage3
    assert result.operational_default
    assert result.accounting_credit_impaired
    assert "days_past_due_backstop" in result.reasons


def test_unlikeliness_to_pay_event_triggers_stage3_before_backstop(policy) -> None:
    result = assess_stage3(
        Stage3AssessmentInput(
            default_input=default_input(qualitative_indicators=("financial_incapacity",))
        ),
        policy,
    )
    assert result.is_stage3
    assert result.reasons == ("financial_incapacity",)


def test_distressed_concession_maps_to_canonical_default_indicator(policy) -> None:
    result = assess_stage3(
        Stage3AssessmentInput(
            default_input=default_input(),
            concession_or_forbearance=True,
            financial_difficulty=True,
        ),
        policy,
    )
    assert result.is_stage3
    assert "distressed_restructuring" in result.reasons


def test_concession_without_financial_difficulty_is_not_automatic_stage3(policy) -> None:
    result = assess_stage3(
        Stage3AssessmentInput(default_input=default_input(), concession_or_forbearance=True),
        policy,
    )
    assert not result.is_stage3


def test_counterparty_level_product_propagates_unexcepted_default(policy) -> None:
    result = assess_stage3(
        Stage3AssessmentInput(
            default_input=default_input(product_code="credit_commitment"),
            counterparty_defaults=(CounterpartyDefaultEvidence("CT-OTHER", True),),
        ),
        policy,
    )
    assert result.is_stage3
    assert result.contagion_contracts == ("CT-OTHER",)
    assert "counterparty_contagion:CT-OTHER" in result.reasons


def test_documented_contagion_exception_blocks_propagation(policy) -> None:
    result = assess_stage3(
        Stage3AssessmentInput(
            default_input=default_input(product_code="credit_commitment"),
            counterparty_defaults=(
                CounterpartyDefaultEvidence("CT-OTHER", True, "legal_ring_fence"),
            ),
        ),
        policy,
    )
    assert not result.is_stage3
    assert result.contagion_exceptions == ("CT-OTHER:legal_ring_fence",)


def test_facility_level_product_does_not_apply_counterparty_contagion(policy) -> None:
    result = assess_stage3(
        Stage3AssessmentInput(
            default_input=default_input(product_code="personal_loan"),
            counterparty_defaults=(CounterpartyDefaultEvidence("CT-OTHER", True),),
        ),
        policy,
    )
    assert not result.is_stage3
    assert result.assessment_level == "facility"


def test_unknown_or_duplicate_contagion_evidence_fails_closed(policy) -> None:
    with pytest.raises(DomainValidationError, match="unknown"):
        assess_stage3(
            Stage3AssessmentInput(
                default_input=default_input(product_code="credit_commitment"),
                counterparty_defaults=(
                    CounterpartyDefaultEvidence("CT-OTHER", True, "unsupported"),
                ),
            ),
            policy,
        )
    with pytest.raises(DomainValidationError, match="unique"):
        assess_stage3(
            Stage3AssessmentInput(
                default_input=default_input(product_code="credit_commitment"),
                counterparty_defaults=(
                    CounterpartyDefaultEvidence("CT-OTHER", True),
                    CounterpartyDefaultEvidence("CT-OTHER", True),
                ),
            ),
            policy,
        )


def test_stage3_decision_carries_policy_hash_and_evidence_status(policy) -> None:
    result = assess_stage3(Stage3AssessmentInput(default_input=default_input()), policy)
    assert result.policy_version == "2026.07.1"
    assert result.policy_sha256 == policy.configuration_hash
    assert "pending_institutional_validation" in result.evidence_status
