"""Immutable scenario inputs without data-provider dependencies."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from ..conventions import DecimalInput, decimal_from, non_empty, rate
from ..exceptions import DomainValidationError


class ScenarioKind(StrEnum):
    BASE = "base"
    UPSIDE = "upside"
    DOWNSIDE = "downside"


@dataclass(frozen=True, slots=True)
class MacroVariable:
    name: str
    value: DecimalInput

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", non_empty(self.name, field="name"))
        object.__setattr__(self, "value", decimal_from(self.value, field=f"variable:{self.name}"))


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    name: str
    kind: ScenarioKind
    reference_date: date
    horizon_months: int
    weight: DecimalInput
    version: str
    variables: tuple[MacroVariable, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", non_empty(self.scenario_id, field="scenario_id"))
        object.__setattr__(self, "name", non_empty(self.name, field="name"))
        object.__setattr__(self, "version", non_empty(self.version, field="version"))
        if self.horizon_months <= 0:
            raise DomainValidationError("horizon_months must be greater than zero")
        object.__setattr__(self, "weight", rate(self.weight, field="weight"))
        names = [variable.name for variable in self.variables]
        if len(names) != len(set(names)):
            raise DomainValidationError("scenario variable names must be unique")
