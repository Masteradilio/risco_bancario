"""Monthly hazard, survival and PD term structures bounded by contractual maturity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import expm1, log1p

from ...domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class PDTermPoint:
    month: int
    period_end: date
    hazard: float
    survival: float
    marginal_pd: float
    cumulative_pd: float


@dataclass(frozen=True, slots=True)
class PDTermStructure:
    contract_id: str
    observation_date: date
    maturity_date: date
    horizon_pd_input: float
    calibration_horizon_months: int
    remaining_months: int
    pd_12m: float
    lifetime_pd: float
    points: tuple[PDTermPoint, ...]
    status: str


def _add_months(value: date, months: int) -> date:
    index = value.month - 1 + months
    year = value.year + index // 12
    month = index % 12 + 1
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_day = (next_month - date.resolution).day
    return date(year, month, min(value.day, last_day))


def remaining_contract_months(observation_date: date, maturity_date: date) -> int:
    if maturity_date <= observation_date:
        raise DomainValidationError("maturity_date must be after observation_date")
    months = (maturity_date.year - observation_date.year) * 12
    months += maturity_date.month - observation_date.month
    if maturity_date.day > observation_date.day:
        months += 1
    return max(1, months)


def monthly_hazards_from_horizon_pd(
    horizon_pd: float,
    remaining_months: int,
    term_multipliers: tuple[float, ...] | None = None,
) -> tuple[float, ...]:
    """Allocate cumulative hazard so PD reconciles over min(12, remaining term)."""
    if not 0 <= horizon_pd < 1:
        raise DomainValidationError("horizon_pd must be in [0, 1)")
    if remaining_months <= 0:
        raise DomainValidationError("remaining_months must be positive")
    multipliers = term_multipliers or (1.0,) * remaining_months
    if len(multipliers) != remaining_months:
        raise DomainValidationError("term_multipliers must cover every remaining month")
    if any(not 0 < value < float("inf") for value in multipliers):
        raise DomainValidationError("term_multipliers must be positive and finite")
    calibration_horizon = min(12, remaining_months)
    denominator = sum(multipliers[:calibration_horizon])
    cumulative_intensity = -log1p(-horizon_pd)
    return tuple(
        -expm1(-cumulative_intensity * multiplier / denominator) for multiplier in multipliers
    )


def project_pd_term_structure(
    contract_id: str,
    observation_date: date,
    maturity_date: date,
    horizon_pd: float,
    *,
    term_multipliers: tuple[float, ...] | None = None,
) -> PDTermStructure:
    """Project a coherent conditional-hazard curve through actual maturity."""
    if not contract_id.strip():
        raise DomainValidationError("contract_id is required")
    remaining = remaining_contract_months(observation_date, maturity_date)
    hazards = monthly_hazards_from_horizon_pd(horizon_pd, remaining, term_multipliers)
    survival = 1.0
    points: list[PDTermPoint] = []
    for month, hazard in enumerate(hazards, start=1):
        marginal = survival * hazard
        survival = max(0.0, survival - marginal)
        cumulative = min(1.0, 1.0 - survival)
        points.append(
            PDTermPoint(
                month,
                min(_add_months(observation_date, month), maturity_date),
                hazard,
                survival,
                marginal,
                cumulative,
            )
        )
    calibration_horizon = min(12, remaining)
    pd_12m = points[calibration_horizon - 1].cumulative_pd
    return PDTermStructure(
        contract_id,
        observation_date,
        maturity_date,
        horizon_pd,
        calibration_horizon,
        remaining,
        pd_12m,
        points[-1].cumulative_pd,
        tuple(points),
        "synthetic_unapproved_input",
    )
