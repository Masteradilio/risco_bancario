"""Cash-flow values used by period-based ECL calculations."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from ..conventions import DecimalInput, money, non_empty


class CashFlowType(str, Enum):
    PRINCIPAL = "principal"
    INTEREST = "interest"
    FEE = "fee"
    RECOVERY = "recovery"
    RECOVERY_COST = "recovery_cost"


@dataclass(frozen=True, slots=True)
class CashFlow:
    contract_id: str
    due_date: date
    amount: DecimalInput
    flow_type: CashFlowType
    currency: str = "BRL"

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", non_empty(self.contract_id, field="contract_id"))
        if self.currency.strip().upper() != "BRL":
            from ..exceptions import UnsupportedCurrencyError

            raise UnsupportedCurrencyError("only BRL is supported in the current scope")
        object.__setattr__(self, "currency", "BRL")
        object.__setattr__(
            self,
            "amount",
            money(self.amount, field="amount", allow_negative=self.flow_type is CashFlowType.RECOVERY_COST),
        )

