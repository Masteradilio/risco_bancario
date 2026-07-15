"""Management overlays kept separate from modeled economic ECL."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal

from ...domain.conventions import DecimalInput, aware_utc, money, non_empty
from ...domain.exceptions import DomainValidationError, TemporalConsistencyError


@dataclass(frozen=True, slots=True)
class ManagementOverlay:
    overlay_id: str
    amount: DecimalInput
    reason: str
    approved_by: str
    approved_at: datetime
    effective_from: date
    effective_to: date
    version: str
    reversed_at: datetime | None = None
    reversed_by: str | None = None
    reversal_reason: str | None = None

    def __post_init__(self) -> None:
        for field in ("overlay_id", "reason", "approved_by", "version"):
            object.__setattr__(self, field, non_empty(getattr(self, field), field=field))
        object.__setattr__(self, "amount", money(self.amount, field="amount", allow_negative=True))
        object.__setattr__(self, "approved_at", aware_utc(self.approved_at, field="approved_at"))
        if self.effective_to < self.effective_from:
            raise TemporalConsistencyError("overlay effective_to cannot precede effective_from")
        reversal_fields = (self.reversed_at, self.reversed_by, self.reversal_reason)
        if any(value is not None for value in reversal_fields):
            if not all(value is not None for value in reversal_fields):
                raise DomainValidationError("overlay reversal requires date, approver and reason")
            reversed_at = self.reversed_at
            reversed_by = self.reversed_by
            reversal_reason = self.reversal_reason
            if reversed_at is None or reversed_by is None or reversal_reason is None:
                raise DomainValidationError("overlay reversal requires date, approver and reason")
            normalized = aware_utc(reversed_at, field="reversed_at")
            if normalized < self.approved_at or normalized.date() < self.effective_from:
                raise TemporalConsistencyError("overlay reversal cannot precede approval or effect")
            object.__setattr__(self, "reversed_at", normalized)
            object.__setattr__(self, "reversed_by", non_empty(reversed_by, field="reversed_by"))
            object.__setattr__(
                self, "reversal_reason", non_empty(reversal_reason, field="reversal_reason")
            )

    def is_active(self, as_of: date) -> bool:
        if not self.effective_from <= as_of <= self.effective_to:
            return False
        return self.reversed_at is None or self.reversed_at.date() > as_of


@dataclass(frozen=True, slots=True)
class OverlayApplication:
    as_of: date
    economic_ecl: Decimal
    overlay_amount: Decimal
    final_ecl: Decimal
    applied_overlay_ids: tuple[str, ...]


def reverse_overlay(
    overlay: ManagementOverlay,
    *,
    reversed_at: datetime,
    reversed_by: str,
    reason: str,
) -> ManagementOverlay:
    if overlay.reversed_at is not None:
        raise DomainValidationError("overlay is already reversed")
    return replace(
        overlay,
        reversed_at=reversed_at,
        reversed_by=reversed_by,
        reversal_reason=reason,
    )


def apply_management_overlays(
    economic_ecl: DecimalInput,
    overlays: tuple[ManagementOverlay, ...],
    as_of: date,
) -> OverlayApplication:
    ids = [overlay.overlay_id for overlay in overlays]
    if len(ids) != len(set(ids)):
        raise DomainValidationError("overlay ids must be unique")
    active = tuple(overlay for overlay in overlays if overlay.is_active(as_of))
    modeled = money(economic_ecl, field="economic_ecl")
    amount = money(
        sum((overlay.amount for overlay in active), Decimal("0")),
        field="overlay_amount",
        allow_negative=True,
    )
    final = money(max(Decimal("0"), modeled + amount), field="final_ecl")
    return OverlayApplication(
        as_of, modeled, amount, final, tuple(item.overlay_id for item in active)
    )
