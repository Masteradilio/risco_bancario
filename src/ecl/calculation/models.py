"""Auditable output types; calculation algorithms are introduced later."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from ...domain.conventions import DecimalInput, aware_utc, money, non_empty, rate
from ...domain.exceptions import DomainValidationError, TemporalConsistencyError
from ...domain.staging import Stage


@dataclass(frozen=True, slots=True)
class ScenarioECL:
    scenario_id: str
    weight: DecimalInput
    ecl: DecimalInput

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", non_empty(self.scenario_id, field="scenario_id"))
        object.__setattr__(self, "weight", rate(self.weight, field="weight"))
        object.__setattr__(self, "ecl", money(self.ecl, field="ecl"))


@dataclass(frozen=True, slots=True)
class ECLResult:
    result_id: str
    contract_id: str
    reference_date: date
    calculated_at: datetime
    stage: Stage
    economic_ecl: DecimalInput
    management_overlay: DecimalInput
    regulatory_floor: DecimalInput
    reported_ecl: DecimalInput
    scenario_results: tuple[ScenarioECL, ...]
    model_version: str
    configuration_version: str
    configuration_hash: str
    currency: str = "BRL"

    def __post_init__(self) -> None:
        for field in (
            "result_id",
            "contract_id",
            "model_version",
            "configuration_version",
            "configuration_hash",
        ):
            object.__setattr__(self, field, non_empty(getattr(self, field), field=field))
        if self.currency.strip().upper() != "BRL":
            raise DomainValidationError("only BRL is supported in the current scope")
        object.__setattr__(self, "currency", "BRL")
        calculated_at = aware_utc(self.calculated_at, field="calculated_at")
        if calculated_at.date() < self.reference_date:
            raise TemporalConsistencyError("calculated_at cannot precede reference_date")
        object.__setattr__(self, "calculated_at", calculated_at)
        for field in ("economic_ecl", "regulatory_floor", "reported_ecl"):
            object.__setattr__(self, field, money(getattr(self, field), field=field))
        object.__setattr__(
            self,
            "management_overlay",
            money(self.management_overlay, field="management_overlay", allow_negative=True),
        )
        if not self.scenario_results:
            raise DomainValidationError("scenario_results must not be empty")
        total_weight = sum((item.weight for item in self.scenario_results), Decimal("0"))
        if total_weight != Decimal("1.00000000"):
            raise DomainValidationError("scenario weights must sum to 1")
        scenario_ids = [item.scenario_id for item in self.scenario_results]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise DomainValidationError("scenario_ids must be unique")

