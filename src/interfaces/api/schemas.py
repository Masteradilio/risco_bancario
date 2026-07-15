"""Strict versioned API contracts for canonical ECL calculation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Rate = Annotated[Decimal, Field(ge=0, le=1)]
Money = Annotated[Decimal, Field(ge=0, max_digits=24, decimal_places=8)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RiskPeriodRequest(StrictModel):
    reference_date: date
    conditional_hazard: Rate
    lgd: Rate
    drawn_ead: Money
    undrawn_amount: Money = Decimal("0")
    ccf: Rate = Decimal("0")
    discount_factor: Annotated[Decimal, Field(gt=0, le=1)]


class MacroPointRequest(StrictModel):
    reference_date: date
    variables: dict[str, Decimal] = Field(min_length=1)


class ScenarioRequest(StrictModel):
    scenario_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    kind: Literal["base", "upside", "downside", "stress"]
    weight: Rate
    periods: list[MacroPointRequest] = Field(min_length=1)


class StageAssessmentRequest(StrictModel):
    """Traceable staging decision compared with the origination state."""

    origination_stage: Literal[1, 2, 3]
    current_stage: Literal[1, 2, 3]
    origination_rating: str = Field(min_length=1, max_length=50)
    current_rating: str = Field(min_length=1, max_length=50)
    origination_lifetime_pd: Rate
    current_lifetime_pd: Rate
    reason_codes: list[str] = Field(min_length=1, max_length=20)


class ECLCalculationRequest(StrictModel):
    execution_key: str = Field(min_length=1, max_length=200)
    contract_id: str = Field(min_length=1, max_length=200)
    source_version: str = Field(min_length=1, max_length=100)
    reference_date: date
    stage: Literal[1, 2]
    stage_assessment: StageAssessmentRequest
    segment: str = Field(default="portfolio", min_length=1, max_length=100)
    periods: list[RiskPeriodRequest] = Field(min_length=1)
    scenario_version: str = Field(min_length=1, max_length=100)
    scenario_source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    scenarios: list[ScenarioRequest] = Field(min_length=4, max_length=4)
    model_versions: dict[str, str] = Field(min_length=1)
    configuration_version: str = Field(min_length=1, max_length=100)
    configuration_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    code_commit: str = Field(pattern=r"^[0-9a-f]{7,40}$")
    reprocess: bool = False

    @model_validator(mode="after")
    def validate_horizons(self) -> ECLCalculationRequest:
        if self.stage_assessment.current_stage != self.stage:
            raise ValueError("stage_assessment.current_stage must match stage")
        if self.stage == 1 and len(self.periods) > 12:
            raise ValueError("Stage 1 accepts at most 12 periods")
        risk_dates = [period.reference_date for period in self.periods]
        if risk_dates != sorted(risk_dates) or risk_dates[0] <= self.reference_date:
            raise ValueError("risk periods must be ordered after reference_date")
        if any(len(scenario.periods) < len(self.periods) for scenario in self.scenarios):
            raise ValueError("every scenario must cover the risk horizon")
        return self


class PeriodResult(StrictModel):
    reference_date: date
    survival_at_start: Decimal
    marginal_pd: Decimal
    lgd: Decimal
    ead: Decimal
    ccf: Decimal
    discount_factor: Decimal
    expected_loss: Decimal


class ScenarioResult(StrictModel):
    scenario_id: str
    kind: str
    weight: Decimal
    ecl: Decimal
    weighted_contribution: Decimal
    periods: list[PeriodResult]


class ECLCalculationResponse(StrictModel):
    execution_id: str
    revision: int
    reused: bool
    contract_id: str
    stage: int
    stage_assessment: StageAssessmentRequest
    probability_weighted_ecl: Decimal
    stress_ecl: Decimal
    scenarios: list[ScenarioResult]
    lineage_hash: str
    scenario_version: str
    macro_policy_version: str


class PortfolioRequest(StrictModel):
    calculations: list[ECLCalculationRequest] = Field(min_length=1, max_length=10_000)


class JobAcceptedResponse(StrictModel):
    job_id: str
    status: Literal["PENDING"]
    status_url: str


class JobStatusResponse(StrictModel):
    job_id: str
    status: Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]
    request_hash: str
    result: list[ECLCalculationResponse] | None = None
    error_code: str | None = None
