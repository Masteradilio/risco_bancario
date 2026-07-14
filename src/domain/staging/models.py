"""Point-in-time observations used by the future SICR service."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import IntEnum

from ..conventions import DecimalInput, aware_utc, non_empty, rate
from ..exceptions import DomainValidationError, TemporalConsistencyError


class Stage(IntEnum):
    STAGE_1 = 1
    STAGE_2 = 2
    STAGE_3 = 3


@dataclass(frozen=True, slots=True)
class RiskSnapshot:
    snapshot_id: str
    contract_id: str
    reference_date: date
    observed_at: datetime
    stage: Stage
    days_past_due: int
    pd_12m: DecimalInput
    pd_lifetime: DecimalInput
    policy_version: str
    rating: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", non_empty(self.snapshot_id, field="snapshot_id"))
        object.__setattr__(self, "contract_id", non_empty(self.contract_id, field="contract_id"))
        object.__setattr__(
            self, "policy_version", non_empty(self.policy_version, field="policy_version")
        )
        if self.days_past_due < 0:
            raise DomainValidationError("days_past_due must be non-negative")
        observed_at = aware_utc(self.observed_at, field="observed_at")
        if observed_at.date() < self.reference_date:
            raise TemporalConsistencyError("observed_at cannot precede reference_date")
        object.__setattr__(self, "observed_at", observed_at)
        pd_12m = rate(self.pd_12m, field="pd_12m")
        pd_lifetime = rate(self.pd_lifetime, field="pd_lifetime")
        if pd_lifetime < pd_12m:
            raise DomainValidationError("pd_lifetime cannot be lower than pd_12m")
        object.__setattr__(self, "pd_12m", pd_12m)
        object.__setattr__(self, "pd_lifetime", pd_lifetime)
        if self.rating is not None:
            object.__setattr__(self, "rating", non_empty(self.rating, field="rating"))
