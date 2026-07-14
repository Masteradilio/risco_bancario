"""Explicit exceptions raised by domain invariants."""


class DomainError(Exception):
    """Base class for errors expressed in domain language."""


class DomainValidationError(DomainError, ValueError):
    """A value violates a domain invariant."""


class TemporalConsistencyError(DomainValidationError):
    """Dates or timestamps are inconsistent with their business timeline."""


class UnsupportedCurrencyError(DomainValidationError):
    """A monetary value uses a currency not supported by the current scope."""

