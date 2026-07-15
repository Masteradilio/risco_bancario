"""Independent simulated model-risk validation and reproducible decisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from ...domain.exceptions import DomainValidationError, TemporalConsistencyError

DEFAULT_POLICY_PATH = Path("config/validation/model_risk/2026.07.1.json")


def _is_lower_hex(value: str, length: int) -> bool:
    return len(value) == length and all(char in "0123456789abcdef" for char in value)


class CriterionResult(StrEnum):
    PASS = "pass"  # noqa: S105 - validation result label, not a password
    WARNING = "warning"
    FAIL = "fail"


class FindingSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_RESERVATIONS = "approved_with_reservations"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ModelSubmission:
    submission_id: str
    model_id: str
    model_version: str
    model_type: str
    development_owner: str
    development_unit: str
    submitted_at: datetime
    code_commit: str
    dataset_hash: str
    artifact_hashes: Mapping[str, str]
    approval_status: str = "not_approved"

    def __post_init__(self) -> None:
        for name in (
            "submission_id",
            "model_id",
            "model_version",
            "model_type",
            "development_owner",
            "development_unit",
            "code_commit",
            "dataset_hash",
        ):
            if not getattr(self, name).strip():
                raise DomainValidationError(f"submission {name} must be non-empty")
        if self.submitted_at.tzinfo is None or self.submitted_at.utcoffset() is None:
            raise DomainValidationError("submitted_at must be timezone-aware")
        if self.approval_status != "not_approved":
            raise DomainValidationError("development submissions cannot carry an approval decision")
        if not _is_lower_hex(self.code_commit, 40):
            raise DomainValidationError("code_commit must be a lowercase 40-character Git SHA")
        if not _is_lower_hex(self.dataset_hash, 64):
            raise DomainValidationError("dataset_hash must be a lowercase SHA-256 value")
        if not self.artifact_hashes:
            raise DomainValidationError("submission requires hashed model artifacts")
        for name, digest in self.artifact_hashes.items():
            if not name or not _is_lower_hex(digest, 64):
                raise DomainValidationError(
                    "artifact hashes must be named lowercase SHA-256 values"
                )


@dataclass(frozen=True, slots=True)
class ValidatorIdentity:
    validator_id: str
    validation_unit: str
    role: str
    independence_attested: bool

    def __post_init__(self) -> None:
        if not self.validator_id or not self.validation_unit:
            raise DomainValidationError("validator identity and unit are required")
        if self.role != "independent_model_validation":
            raise DomainValidationError("validator role lacks independent decision authority")
        if not self.independence_attested:
            raise DomainValidationError("validator must attest independence")


@dataclass(frozen=True, slots=True)
class ValidationCriterion:
    criterion_id: str
    category: str
    description: str
    result: CriterionResult
    mandatory: bool
    observed_value: str
    threshold: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.criterion_id or not self.category or not self.description:
            raise DomainValidationError("criterion identity, category and description are required")
        if not self.observed_value or not self.threshold or not self.evidence_refs:
            raise DomainValidationError("criterion requires observed value, threshold and evidence")


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    finding_id: str
    severity: FindingSeverity
    title: str
    details: str
    remediation: str
    due_date: date | None

    def __post_init__(self) -> None:
        if not all((self.finding_id, self.title, self.details, self.remediation)):
            raise DomainValidationError("finding requires identity, detail and remediation")


@dataclass(frozen=True, slots=True)
class ValidationPolicy:
    version: str
    minimum_criteria: int
    reject_on_mandatory_failure: bool
    reject_on_critical_finding: bool
    reject_on_high_finding: bool
    reservation_on_non_mandatory_failure: bool
    reservation_on_warning: bool
    reservation_on_medium_or_low_finding: bool
    required_categories: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    submission: ModelSubmission
    validator: ValidatorIdentity
    validation_date: date
    policy_version: str
    policy_hash: str
    criteria: tuple[ValidationCriterion, ...]
    findings: tuple[ValidationFinding, ...]
    decision: ValidationDecision
    decision_reasons: tuple[str, ...]
    report_hash: str
    evidence_status: str = "synthetic_independent_validation"


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def load_validation_policy(path: Path = DEFAULT_POLICY_PATH) -> ValidationPolicy:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "version",
        "minimum_criteria",
        "reject_on_mandatory_failure",
        "reject_on_critical_finding",
        "reject_on_high_finding",
        "reservation_on_non_mandatory_failure",
        "reservation_on_warning",
        "reservation_on_medium_or_low_finding",
        "required_categories",
    }
    if set(payload) != required:
        raise DomainValidationError("validation policy has missing or unknown fields")
    if not isinstance(payload["minimum_criteria"], int) or payload["minimum_criteria"] < 1:
        raise DomainValidationError("minimum_criteria must be positive")
    if not isinstance(payload["version"], str) or not payload["version"]:
        raise DomainValidationError("validation policy version must be a non-empty string")
    boolean_fields = required - {"version", "minimum_criteria", "required_categories"}
    if any(not isinstance(payload[field], bool) for field in boolean_fields):
        raise DomainValidationError("validation policy switches must be boolean")
    categories = payload["required_categories"]
    if (
        not isinstance(categories, list)
        or not categories
        or not all(isinstance(x, str) and x for x in categories)
        or len(categories) != len(set(categories))
    ):
        raise DomainValidationError("required_categories must be a non-empty string list")
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return ValidationPolicy(
        payload["version"],
        payload["minimum_criteria"],
        payload["reject_on_mandatory_failure"],
        payload["reject_on_critical_finding"],
        payload["reject_on_high_finding"],
        payload["reservation_on_non_mandatory_failure"],
        payload["reservation_on_warning"],
        payload["reservation_on_medium_or_low_finding"],
        tuple(categories),
        digest,
    )


def _assert_independence(submission: ModelSubmission, validator: ValidatorIdentity) -> None:
    if validator.validator_id == submission.development_owner:
        raise DomainValidationError("developer cannot validate their own model")
    if validator.validation_unit == submission.development_unit:
        raise DomainValidationError("validation unit must differ from development unit")


def _decision(
    criteria: tuple[ValidationCriterion, ...],
    findings: tuple[ValidationFinding, ...],
    policy: ValidationPolicy,
) -> tuple[ValidationDecision, tuple[str, ...]]:
    reasons: list[str] = []
    mandatory_failures = [
        item.criterion_id
        for item in criteria
        if item.mandatory and item.result == CriterionResult.FAIL
    ]
    critical = [item.finding_id for item in findings if item.severity == FindingSeverity.CRITICAL]
    high = [item.finding_id for item in findings if item.severity == FindingSeverity.HIGH]
    if policy.reject_on_mandatory_failure and mandatory_failures:
        reasons.append(f"mandatory criteria failed: {','.join(mandatory_failures)}")
    if policy.reject_on_critical_finding and critical:
        reasons.append(f"critical findings open: {','.join(critical)}")
    if policy.reject_on_high_finding and high:
        reasons.append(f"high findings open: {','.join(high)}")
    if reasons:
        return ValidationDecision.REJECTED, tuple(reasons)
    reservations: list[str] = []
    if policy.reservation_on_non_mandatory_failure:
        failed = [
            item.criterion_id
            for item in criteria
            if not item.mandatory and item.result == CriterionResult.FAIL
        ]
        if failed:
            reservations.append(f"non-mandatory criteria failed: {','.join(failed)}")
    if policy.reservation_on_warning:
        warned = [item.criterion_id for item in criteria if item.result == CriterionResult.WARNING]
        if warned:
            reservations.append(f"criteria warnings: {','.join(warned)}")
    if policy.reservation_on_medium_or_low_finding:
        open_findings = [item.finding_id for item in findings]
        if open_findings:
            reservations.append(f"open findings: {','.join(open_findings)}")
    if reservations:
        return ValidationDecision.APPROVED_WITH_RESERVATIONS, tuple(reservations)
    return ValidationDecision.APPROVED, ("all objective criteria passed with no open findings",)


def validate_model_submission(
    submission: ModelSubmission,
    validator: ValidatorIdentity,
    validation_date: date,
    criteria: tuple[ValidationCriterion, ...],
    findings: tuple[ValidationFinding, ...],
    policy: ValidationPolicy | None = None,
) -> ValidationReport:
    selected = policy or load_validation_policy()
    _assert_independence(submission, validator)
    if validation_date < submission.submitted_at.date():
        raise TemporalConsistencyError("validation_date cannot precede submission")
    if len(criteria) < selected.minimum_criteria:
        raise DomainValidationError("insufficient criteria for an independent decision")
    criteria = tuple(sorted(criteria, key=lambda item: item.criterion_id))
    findings = tuple(sorted(findings, key=lambda item: item.finding_id))
    criterion_ids = [item.criterion_id for item in criteria]
    finding_ids = [item.finding_id for item in findings]
    if len(criterion_ids) != len(set(criterion_ids)) or len(finding_ids) != len(set(finding_ids)):
        raise DomainValidationError("criterion and finding IDs must be unique")
    categories = {item.category for item in criteria}
    missing = set(selected.required_categories) - categories
    if missing:
        raise DomainValidationError(f"required validation categories absent: {sorted(missing)}")
    decision, reasons = _decision(criteria, findings, selected)
    payload = {
        "submission": asdict(submission),
        "validator": asdict(validator),
        "validation_date": validation_date,
        "policy_version": selected.version,
        "policy_hash": selected.policy_hash,
        "criteria": [asdict(item) for item in criteria],
        "findings": [asdict(item) for item in findings],
        "decision": decision,
        "decision_reasons": reasons,
        "evidence_status": "synthetic_independent_validation",
    }
    report_hash = hashlib.sha256(_canonical(payload)).hexdigest()
    return ValidationReport(
        submission,
        validator,
        validation_date,
        selected.version,
        selected.policy_hash,
        criteria,
        findings,
        decision,
        reasons,
        report_hash,
    )


def render_validation_report(report: ValidationReport) -> str:
    lines = [
        f"# Independent validation report — {report.submission.model_id}",
        "",
        f"- Model version: `{report.submission.model_version}`",
        f"- Validation date: `{report.validation_date.isoformat()}`",
        f"- Validator: `{report.validator.validator_id}` / `{report.validator.validation_unit}`",
        f"- Policy: `{report.policy_version}` (`{report.policy_hash}`)",
        f"- Decision: **{report.decision.value}**",
        f"- Report hash: `{report.report_hash}`",
        f"- Evidence status: `{report.evidence_status}`",
        "",
        "## Objective criteria",
        "",
        "| ID | Category | Mandatory | Result | Observed | Threshold | Evidence |",
        "|---|---|---:|---|---|---|---|",
    ]
    for item in report.criteria:
        lines.append(
            f"| {item.criterion_id} | {item.category} | {str(item.mandatory).lower()} | "
            f"{item.result.value} | {item.observed_value} | {item.threshold} | "
            f"{'; '.join(item.evidence_refs)} |"
        )
    lines.extend(("", "## Decision reasons", ""))
    lines.extend(f"- {reason}" for reason in report.decision_reasons)
    lines.extend(("", "## Findings", ""))
    if report.findings:
        lines.extend(
            f"- `{item.finding_id}` [{item.severity.value}] {item.title}: {item.remediation}"
            for item in report.findings
        )
    else:
        lines.append("- No open findings.")
    lines.extend(("", "> Synthetic simulated independence; not institutional model approval.", ""))
    return "\n".join(lines)
