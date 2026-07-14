"""Typed credit contracts and guarantees."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from ..conventions import DecimalInput, money, non_empty, rate
from ..exceptions import DomainValidationError, TemporalConsistencyError, UnsupportedCurrencyError


class ContractStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    DEFAULTED = "defaulted"
    WRITTEN_OFF = "written_off"


class GuaranteeType(StrEnum):
    FINANCIAL = "financial"
    REAL_ESTATE = "real_estate"
    VEHICLE = "vehicle"
    RECEIVABLE = "receivable"
    PERSONAL = "personal"
    OTHER = "other"


def _require_brl(currency: str) -> str:
    normalized = currency.strip().upper()
    if normalized != "BRL":
        raise UnsupportedCurrencyError("only BRL is supported in the current scope")
    return normalized


@dataclass(frozen=True, slots=True)
class Contract:
    contract_id: str
    client_id: str
    counterparty_id: str
    product_code: str
    origination_date: date
    maturity_date: date
    original_amount: DecimalInput
    currency: str = "BRL"
    effective_interest_rate: DecimalInput = Decimal("0")
    status: ContractStatus = ContractStatus.ACTIVE

    def __post_init__(self) -> None:
        for field in ("contract_id", "client_id", "counterparty_id", "product_code"):
            object.__setattr__(self, field, non_empty(getattr(self, field), field=field))
        if self.maturity_date < self.origination_date:
            raise TemporalConsistencyError("maturity_date cannot precede origination_date")
        object.__setattr__(self, "currency", _require_brl(self.currency))
        amount = money(self.original_amount, field="original_amount")
        if amount == 0:
            raise DomainValidationError("original_amount must be greater than zero")
        object.__setattr__(self, "original_amount", amount)
        object.__setattr__(
            self,
            "effective_interest_rate",
            rate(self.effective_interest_rate, field="effective_interest_rate"),
        )


@dataclass(frozen=True, slots=True)
class Guarantee:
    guarantee_id: str
    contract_id: str
    guarantee_type: GuaranteeType
    valuation_date: date
    value: DecimalInput
    enforceable_share: DecimalInput = Decimal("1")
    currency: str = "BRL"

    def __post_init__(self) -> None:
        object.__setattr__(self, "guarantee_id", non_empty(self.guarantee_id, field="guarantee_id"))
        object.__setattr__(self, "contract_id", non_empty(self.contract_id, field="contract_id"))
        object.__setattr__(self, "currency", _require_brl(self.currency))
        object.__setattr__(self, "value", money(self.value, field="value"))
        object.__setattr__(
            self,
            "enforceable_share",
            rate(self.enforceable_share, field="enforceable_share"),
        )
