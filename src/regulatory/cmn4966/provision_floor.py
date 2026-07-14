"""Date-versioned local provision floor applied after accounting ECL."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from ...domain.conventions import DecimalInput, money, rate
from ...domain.exceptions import DomainValidationError, TemporalConsistencyError

POLICY_DIRECTORY = (
    Path(__file__).resolve().parents[3] / "config" / "regulatory" / "cmn4966_provision_floor"
)


class ProvisionPortfolio(StrEnum):
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"
    C5 = "C5"


@dataclass(frozen=True, slots=True)
class ProvisionFloorPolicy:
    policy_version: str
    effective_from: date
    effective_to: date | None
    source_id: str
    source_locator: str
    evidence_status: str
    delinquency_threshold_days: int
    floor_rates: tuple[tuple[ProvisionPortfolio, tuple[Decimal, ...]], ...]
    sha256: str

    def rate_for(self, portfolio: ProvisionPortfolio, months_since_default: int) -> Decimal:
        if months_since_default < 0:
            raise DomainValidationError("months_since_default must be non-negative")
        rates = dict(self.floor_rates)[portfolio]
        return rates[min(months_since_default, len(rates) - 1)]


@dataclass(frozen=True, slots=True)
class ProvisionFloorResult:
    reference_date: date
    portfolio: ProvisionPortfolio
    gross_carrying_amount: Decimal
    calculated_ecl: Decimal
    floor_rate: Decimal
    regulatory_floor: Decimal
    final_provision: Decimal
    floor_applied: bool
    months_since_default: int | None
    policy_version: str
    policy_hash: str
    source_id: str
    source_locator: str


def _load_policy_file(path: Path) -> ProvisionFloorPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    metadata = document["metadata"]
    effective_to = metadata["effective_to"]
    rates = document["floor_rates_by_month_since_default"]
    expected = {item.value for item in ProvisionPortfolio}
    if set(rates) != expected:
        raise DomainValidationError("provision floor policy must define C1 through C5")
    parsed_rates: list[tuple[ProvisionPortfolio, tuple[Decimal, ...]]] = []
    for portfolio in ProvisionPortfolio:
        values = tuple(
            rate(value, field=f"floor_rates.{portfolio.value}") for value in rates[portfolio]
        )
        if len(values) != 22:
            raise DomainValidationError("provision floor policy must define 22 month bands")
        if any(current > following for current, following in zip(values, values[1:], strict=False)):
            raise DomainValidationError("provision floor rates must be non-decreasing")
        if values[-1] != Decimal("1.00000000"):
            raise DomainValidationError("last provision floor band must equal 100%")
        parsed_rates.append((portfolio, values))
    threshold = int(document["delinquency_threshold_days"])
    if threshold != 90:
        raise DomainValidationError("official policy requires a 90-day delinquency threshold")
    return ProvisionFloorPolicy(
        metadata["policy_version"],
        date.fromisoformat(metadata["effective_from"]),
        date.fromisoformat(effective_to) if effective_to else None,
        metadata["source_id"],
        metadata["source_locator"],
        metadata["evidence_status"],
        threshold,
        tuple(parsed_rates),
        sha256(raw).hexdigest(),
    )


def load_provision_floor_policy(
    reference_date: date, directory: Path = POLICY_DIRECTORY
) -> ProvisionFloorPolicy:
    candidates = tuple(_load_policy_file(path) for path in sorted(directory.glob("*.json")))
    matches = tuple(
        policy
        for policy in candidates
        if policy.effective_from <= reference_date
        and (policy.effective_to is None or reference_date <= policy.effective_to)
    )
    if len(matches) != 1:
        raise DomainValidationError(
            f"unsupported or ambiguous provision floor policy for {reference_date.isoformat()}"
        )
    return matches[0]


def _months_since_default(default_date: date, reference_date: date) -> int:
    if default_date > reference_date:
        raise TemporalConsistencyError("default_date cannot be after reference_date")
    year_months = (reference_date.year - default_date.year) * 12
    return year_months + reference_date.month - default_date.month


def apply_provision_floor(
    *,
    reference_date: date,
    portfolio: ProvisionPortfolio,
    gross_carrying_amount: DecimalInput,
    calculated_ecl: DecimalInput,
    days_past_due: int,
    default_date: date | None,
    policy: ProvisionFloorPolicy | None = None,
) -> ProvisionFloorResult:
    """Return accounting ECL, regulatory floor and final provision without mixing layers."""
    active_policy = policy or load_provision_floor_policy(reference_date)
    gross = money(gross_carrying_amount, field="gross_carrying_amount")
    ecl = money(calculated_ecl, field="calculated_ecl")
    if ecl > gross:
        raise DomainValidationError("calculated_ecl cannot exceed gross_carrying_amount")
    if days_past_due < 0:
        raise DomainValidationError("days_past_due must be non-negative")
    delinquent = days_past_due > active_policy.delinquency_threshold_days
    if delinquent and default_date is None:
        raise DomainValidationError("default_date is required for a delinquent asset")
    if not delinquent and default_date is not None:
        raise DomainValidationError("default_date is only allowed for a delinquent asset")
    months = _months_since_default(default_date, reference_date) if default_date else None
    floor_rate = active_policy.rate_for(portfolio, months) if months is not None else Decimal("0")
    floor = money(gross * floor_rate, field="regulatory_floor")
    final = max(ecl, floor)
    return ProvisionFloorResult(
        reference_date,
        portfolio,
        gross,
        ecl,
        floor_rate,
        floor,
        final,
        floor > ecl,
        months,
        active_policy.policy_version,
        active_policy.sha256,
        active_policy.source_id,
        active_policy.source_locator,
    )
