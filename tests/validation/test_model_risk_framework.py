import json
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.validation.model_risk import (
    DEFAULT_POLICY_PATH,
    CriterionResult,
    FindingSeverity,
    ModelSubmission,
    ValidationCriterion,
    ValidationDecision,
    ValidationFinding,
    ValidatorIdentity,
    load_validation_policy,
    render_validation_report,
    validate_model_submission,
)


def submission(**changes) -> ModelSubmission:
    values = {
        "submission_id": "SUB-PD-1",
        "model_id": "pd_baseline",
        "model_version": "2026.07.1",
        "model_type": "PD",
        "development_owner": "developer-a",
        "development_unit": "credit-model-development",
        "submitted_at": datetime(2026, 7, 10, 12, tzinfo=UTC),
        "code_commit": "a" * 40,
        "dataset_hash": "b" * 64,
        "artifact_hashes": {"model.json": "c" * 64},
        "approval_status": "not_approved",
    }
    values.update(changes)
    return ModelSubmission(**values)


def validator(**changes) -> ValidatorIdentity:
    values = {
        "validator_id": "validator-b",
        "validation_unit": "independent-model-risk",
        "role": "independent_model_validation",
        "independence_attested": True,
    }
    values.update(changes)
    return ValidatorIdentity(**values)


def criterion(
    criterion_id: str,
    category: str,
    result: CriterionResult = CriterionResult.PASS,
    *,
    mandatory: bool = True,
) -> ValidationCriterion:
    return ValidationCriterion(
        criterion_id,
        category,
        f"Objective check for {category}",
        result,
        mandatory,
        "observed=1",
        "required=1",
        (f"evidence/{criterion_id}.json",),
    )


def passing_criteria() -> tuple[ValidationCriterion, ...]:
    return (
        criterion("C-CONCEPT", "conceptual_soundness"),
        criterion("C-DATA", "data"),
        criterion("C-PERF", "performance"),
    )


def finding(severity: FindingSeverity) -> ValidationFinding:
    return ValidationFinding(
        f"F-{severity.value}",
        severity,
        "Open issue",
        "Evidence does not meet the objective threshold.",
        "Remediate and resubmit to independent validation.",
        date(2026, 8, 31),
    )


def evaluate(
    criteria: tuple[ValidationCriterion, ...] | None = None,
    findings: tuple[ValidationFinding, ...] = (),
):
    return validate_model_submission(
        submission(),
        validator(),
        date(2026, 7, 14),
        criteria if criteria is not None else passing_criteria(),
        findings,
    )


def test_all_objective_criteria_pass_to_approved_decision() -> None:
    report = evaluate()
    assert report.decision == ValidationDecision.APPROVED
    assert report.decision_reasons == ("all objective criteria passed with no open findings",)
    assert len(report.report_hash) == 64


def test_warning_or_non_mandatory_failure_produces_reservations() -> None:
    warned = (
        *passing_criteria(),
        criterion("C-EXTRA", "stability", CriterionResult.WARNING, mandatory=False),
    )
    assert evaluate(warned).decision == ValidationDecision.APPROVED_WITH_RESERVATIONS
    failed = (
        *passing_criteria(),
        criterion("C-EXTRA", "stability", CriterionResult.FAIL, mandatory=False),
    )
    assert evaluate(failed).decision == ValidationDecision.APPROVED_WITH_RESERVATIONS


@pytest.mark.parametrize("severity", [FindingSeverity.LOW, FindingSeverity.MEDIUM])
def test_low_or_medium_finding_produces_reservations(severity: FindingSeverity) -> None:
    assert (
        evaluate(findings=(finding(severity),)).decision
        == ValidationDecision.APPROVED_WITH_RESERVATIONS
    )


def test_mandatory_failure_or_high_finding_rejects() -> None:
    failed = tuple(
        replace(item, result=CriterionResult.FAIL) if item.criterion_id == "C-PERF" else item
        for item in passing_criteria()
    )
    assert evaluate(failed).decision == ValidationDecision.REJECTED
    assert (
        evaluate(findings=(finding(FindingSeverity.HIGH),)).decision == ValidationDecision.REJECTED
    )
    assert (
        evaluate(findings=(finding(FindingSeverity.CRITICAL),)).decision
        == ValidationDecision.REJECTED
    )


def test_development_pipeline_cannot_submit_an_approval() -> None:
    with pytest.raises(DomainValidationError, match="cannot carry an approval"):
        submission(approval_status="approved")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"code_commit": "not-a-sha"}, "code_commit"),
        ({"dataset_hash": "not-a-hash"}, "dataset_hash"),
        ({"artifact_hashes": {"model.json": "not-a-hash"}}, "artifact hashes"),
    ],
)
def test_submission_requires_reproducible_hashes(change: dict, message: str) -> None:
    with pytest.raises(DomainValidationError, match=message):
        submission(**change)


def test_validator_must_be_independent_from_owner_and_unit() -> None:
    with pytest.raises(DomainValidationError, match="own model"):
        validate_model_submission(
            submission(),
            validator(validator_id="developer-a"),
            date(2026, 7, 14),
            passing_criteria(),
            (),
        )
    with pytest.raises(DomainValidationError, match="unit must differ"):
        validate_model_submission(
            submission(),
            validator(validation_unit="credit-model-development"),
            date(2026, 7, 14),
            passing_criteria(),
            (),
        )


def test_policy_requires_minimum_coverage_and_categories() -> None:
    with pytest.raises(DomainValidationError, match="insufficient criteria"):
        evaluate(passing_criteria()[:2])
    missing = (
        criterion("C-1", "conceptual_soundness"),
        criterion("C-2", "data"),
        criterion("C-3", "stability"),
    )
    with pytest.raises(DomainValidationError, match="performance"):
        evaluate(missing)


def test_validation_cannot_predate_submission() -> None:
    with pytest.raises(TemporalConsistencyError, match="cannot precede"):
        validate_model_submission(
            submission(), validator(), date(2026, 7, 9), passing_criteria(), ()
        )


def test_report_hash_and_markdown_are_reproducible_independent_of_input_order() -> None:
    first = evaluate(passing_criteria())
    second = evaluate(tuple(reversed(passing_criteria())))
    assert first.report_hash == second.report_hash
    assert render_validation_report(first) == render_validation_report(second)
    rendered = render_validation_report(first)
    assert "Decision: **approved**" in rendered
    assert "Synthetic simulated independence" in rendered


def test_policy_is_versioned_and_hashed() -> None:
    policy = load_validation_policy()
    assert policy.version == "2026.07.1"
    assert len(policy.policy_hash) == 64


def test_policy_loader_rejects_non_boolean_switches(tmp_path) -> None:
    payload = json.loads(DEFAULT_POLICY_PATH.read_text(encoding="utf-8"))
    payload["reject_on_high_finding"] = "yes"
    path = tmp_path / "invalid-policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="must be boolean"):
        load_validation_policy(path)
