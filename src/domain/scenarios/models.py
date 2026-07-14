"""Immutable scenario inputs without data-provider dependencies."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from ..conventions import DecimalInput, decimal_from, non_empty, rate
from ..exceptions import DomainValidationError


class ScenarioKind(StrEnum):
    BASE = "base"
    UPSIDE = "upside"
    DOWNSIDE = "downside"
    STRESS = "stress"


class ScenarioApprovalStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_APPROVED = "not_approved"


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


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


@dataclass(frozen=True, slots=True)
class MacroTrajectoryPoint:
    reference_date: date
    variables: tuple[MacroVariable, ...]

    def __post_init__(self) -> None:
        if self.reference_date.day != 1:
            raise DomainValidationError("trajectory reference dates must be month starts")
        if not self.variables:
            raise DomainValidationError("trajectory point requires macro variables")
        names = [variable.name for variable in self.variables]
        if len(names) != len(set(names)):
            raise DomainValidationError("trajectory variable names must be unique")


@dataclass(frozen=True, slots=True)
class ScenarioTrajectory:
    scenario_id: str
    name: str
    kind: ScenarioKind
    weight: DecimalInput
    periods: tuple[MacroTrajectoryPoint, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", non_empty(self.scenario_id, field="scenario_id"))
        object.__setattr__(self, "name", non_empty(self.name, field="name"))
        object.__setattr__(self, "weight", rate(self.weight, field="weight"))
        if not self.periods:
            raise DomainValidationError("scenario trajectory requires periods")
        expected_names = tuple(variable.name for variable in self.periods[0].variables)
        for previous, current in zip(self.periods[:-1], self.periods[1:], strict=True):
            if current.reference_date != _next_month(previous.reference_date):
                raise DomainValidationError(
                    "scenario trajectory periods must be consecutive months"
                )
        if any(
            tuple(variable.name for variable in period.variables) != expected_names
            for period in self.periods
        ):
            raise DomainValidationError("macro variable schema must be stable across periods")


@dataclass(frozen=True, slots=True)
class ScenarioSet:
    reference_date: date
    version: str
    approval_status: ScenarioApprovalStatus
    source_snapshot_hash: str
    trajectories: tuple[ScenarioTrajectory, ...]
    approved_by: str | None = None
    approval_date: date | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "version", non_empty(self.version, field="version"))
        snapshot_hash = non_empty(self.source_snapshot_hash, field="source_snapshot_hash")
        if len(snapshot_hash) != 64 or any(
            character not in "0123456789abcdef" for character in snapshot_hash
        ):
            raise DomainValidationError("source_snapshot_hash must be a lowercase SHA-256")
        object.__setattr__(self, "source_snapshot_hash", snapshot_hash)
        if not self.trajectories:
            raise DomainValidationError("scenario set requires trajectories")
        kinds = [trajectory.kind for trajectory in self.trajectories]
        if sorted(kinds) != sorted(ScenarioKind):
            raise DomainValidationError(
                "scenario set requires one base, upside, downside and stress"
            )
        ids = [trajectory.scenario_id for trajectory in self.trajectories]
        if len(ids) != len(set(ids)):
            raise DomainValidationError("scenario ids must be unique")
        probability_weight = sum(
            (
                trajectory.weight
                for trajectory in self.trajectories
                if trajectory.kind != ScenarioKind.STRESS
            ),
            Decimal("0"),
        )
        if probability_weight != Decimal("1"):
            raise DomainValidationError("probability scenario weights must sum to one")
        stress = next(item for item in self.trajectories if item.kind == ScenarioKind.STRESS)
        if stress.weight != Decimal("0"):
            raise DomainValidationError("stress scenario must have zero probability weight")
        starts = {trajectory.periods[0].reference_date for trajectory in self.trajectories}
        lengths = {len(trajectory.periods) for trajectory in self.trajectories}
        if starts != {self.reference_date} or len(lengths) != 1:
            raise DomainValidationError(
                "scenario trajectories must share reference date and horizon"
            )
        if self.approval_status == ScenarioApprovalStatus.APPROVED:
            if self.approved_by is None or self.approval_date is None:
                raise DomainValidationError(
                    "approved scenario set requires approver and approval date"
                )
        elif self.approved_by is not None or self.approval_date is not None:
            raise DomainValidationError("unapproved scenario set cannot carry approval metadata")
