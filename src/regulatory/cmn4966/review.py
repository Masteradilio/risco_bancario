"""Monthly provision and stage review evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256

from ...domain.conventions import DecimalInput, aware_utc, money, non_empty
from ...domain.exceptions import DomainValidationError, TemporalConsistencyError
from ...domain.staging import Stage


@dataclass(frozen=True, slots=True)
class InstrumentMonthlyReview:
    contract_id: str
    previous_reference_date: date
    reference_date: date
    previous_stage: Stage
    current_stage: Stage
    previous_allowance: DecimalInput
    current_allowance: DecimalInput
    review_reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", non_empty(self.contract_id, field="contract_id"))
        object.__setattr__(
            self, "review_reason", non_empty(self.review_reason, field="review_reason")
        )
        previous = money(self.previous_allowance, field="previous_allowance")
        current = money(self.current_allowance, field="current_allowance")
        previous_month = self.previous_reference_date.year * 12 + self.previous_reference_date.month
        current_month = self.reference_date.year * 12 + self.reference_date.month
        if current_month - previous_month != 1:
            raise TemporalConsistencyError("monthly review cannot skip or repeat a calendar month")
        object.__setattr__(self, "previous_allowance", previous)
        object.__setattr__(self, "current_allowance", current)

    @property
    def allowance_change(self) -> Decimal:
        return Decimal(self.current_allowance) - Decimal(self.previous_allowance)

    @property
    def stage_changed(self) -> bool:
        return self.current_stage != self.previous_stage


@dataclass(frozen=True, slots=True)
class MonthlyReviewManifest:
    review_id: str
    reference_date: date
    completed_at: datetime
    instruments: tuple[InstrumentMonthlyReview, ...]
    total_previous_allowance: Decimal
    total_current_allowance: Decimal
    stage_change_count: int
    source_locator: str
    manifest_hash: str


def create_monthly_review_manifest(
    *,
    review_id: str,
    reference_date: date,
    completed_at: datetime,
    instruments: tuple[InstrumentMonthlyReview, ...],
) -> MonthlyReviewManifest:
    identifier = non_empty(review_id, field="review_id")
    completed = aware_utc(completed_at, field="completed_at")
    if completed.date() < reference_date:
        raise TemporalConsistencyError("monthly review cannot complete before reference date")
    if not instruments:
        raise DomainValidationError("monthly review requires instruments")
    ids = [item.contract_id for item in instruments]
    if len(ids) != len(set(ids)):
        raise DomainValidationError("monthly review contains duplicate contracts")
    if any(item.reference_date != reference_date for item in instruments):
        raise DomainValidationError("every instrument review must use the manifest reference date")
    ordered = tuple(sorted(instruments, key=lambda item: item.contract_id))
    previous = sum((Decimal(item.previous_allowance) for item in ordered), Decimal("0"))
    current = sum((Decimal(item.current_allowance) for item in ordered), Decimal("0"))
    payload = {
        "review_id": identifier,
        "reference_date": reference_date,
        "completed_at": completed,
        "instruments": [asdict(item) for item in ordered],
    }
    digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    return MonthlyReviewManifest(
        identifier,
        reference_date,
        completed,
        ordered,
        previous.quantize(Decimal("0.01")),
        current.quantize(Decimal("0.01")),
        sum(item.stage_changed for item in ordered),
        "Resolução CMN nº 4.966/2021, art. 48; Resolução BCB nº 352/2023",
        digest,
    )
