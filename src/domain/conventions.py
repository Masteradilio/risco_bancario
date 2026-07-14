"""Numeric and temporal conventions shared by domain entities.

Percentages are decimal fractions in the closed interval [0, 1]. Monetary
values use ``Decimal`` and are rounded to cents with ``ROUND_HALF_EVEN``.
Business dates are ``date`` objects; event timestamps must be timezone-aware.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

from .exceptions import DomainValidationError, TemporalConsistencyError

type DecimalInput = Decimal | int | str
MONEY_QUANTUM = Decimal("0.01")
RATE_QUANTUM = Decimal("0.00000001")
ZERO = Decimal("0")
ONE = Decimal("1")


def decimal_from(value: DecimalInput, *, field: str) -> Decimal:
    """Convert an exact input to ``Decimal`` and reject binary floats."""
    if isinstance(value, bool) or isinstance(value, float):
        raise DomainValidationError(
            f"{field} must be Decimal, int or string; binary floats are not accepted"
        )
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise DomainValidationError(f"{field} is not a valid decimal") from exc
    if not result.is_finite():
        raise DomainValidationError(f"{field} must be finite")
    return result


def money(value: DecimalInput, *, field: str, allow_negative: bool = False) -> Decimal:
    """Normalize a BRL amount according to the explicit rounding policy."""
    result = decimal_from(value, field=field)
    if not allow_negative and result < ZERO:
        raise DomainValidationError(f"{field} must be non-negative")
    return result.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)


def rate(value: DecimalInput, *, field: str) -> Decimal:
    """Normalize a decimal percentage constrained to [0, 1]."""
    result = decimal_from(value, field=field)
    if not ZERO <= result <= ONE:
        raise DomainValidationError(f"{field} must be between 0 and 1")
    return result.quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN)


def non_empty(value: str, *, field: str) -> str:
    """Strip and validate a required identifier or label."""
    normalized = value.strip()
    if not normalized:
        raise DomainValidationError(f"{field} must not be empty")
    return normalized


def aware_utc(value: datetime, *, field: str) -> datetime:
    """Require an aware timestamp and normalize it to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise TemporalConsistencyError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)
