"""Entities that identify obligors without persistence concerns."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from ..conventions import non_empty
from ..exceptions import TemporalConsistencyError


class PartyType(StrEnum):
    INDIVIDUAL = "individual"
    LEGAL_ENTITY = "legal_entity"


@dataclass(frozen=True, slots=True)
class Counterparty:
    counterparty_id: str
    party_type: PartyType
    inception_date: date
    economic_group_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "counterparty_id", non_empty(self.counterparty_id, field="counterparty_id")
        )
        if self.economic_group_id is not None:
            object.__setattr__(
                self,
                "economic_group_id",
                non_empty(self.economic_group_id, field="economic_group_id"),
            )


@dataclass(frozen=True, slots=True)
class Client:
    client_id: str
    counterparty_id: str
    relationship_start_date: date
    reference_date: date

    def __post_init__(self) -> None:
        object.__setattr__(self, "client_id", non_empty(self.client_id, field="client_id"))
        object.__setattr__(
            self, "counterparty_id", non_empty(self.counterparty_id, field="counterparty_id")
        )
        if self.reference_date < self.relationship_start_date:
            raise TemporalConsistencyError("reference_date cannot precede relationship_start_date")
