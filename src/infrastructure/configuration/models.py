"""Pydantic schemas for governed, versioned risk configuration."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PolicyMetadata(StrictModel):
    schema_version: Literal["1.0.0"]
    policy_version: str = Field(min_length=1)
    effective_from: date
    effective_to: date | None = None
    author: str = Field(min_length=1)
    justification: str = Field(min_length=1)
    evidence_status: Literal["demonstrative", "validated"]
    source_references: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_window(self) -> "PolicyMetadata":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from")
        return self


class RatingBand(StrictModel):
    rating: str = Field(min_length=1)
    lower_inclusive: Decimal = Field(ge=0, le=100)
    upper_exclusive: Decimal = Field(gt=0, le=101)
    pd_12m_min: Decimal = Field(ge=0, le=1)
    pd_12m_max: Decimal = Field(ge=0, le=1)
    lifetime_horizon_years: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self) -> "RatingBand":
        if self.upper_exclusive <= self.lower_inclusive:
            raise ValueError("rating band upper bound must exceed lower bound")
        if self.pd_12m_max < self.pd_12m_min:
            raise ValueError("pd_12m_max cannot be lower than pd_12m_min")
        return self


class StagingPolicy(StrictModel):
    stage_2_days_past_due: int = Field(ge=0)
    stage_3_days_past_due: int = Field(ge=0)
    stage_2_downgrade_notches: int = Field(ge=1)
    stage_2_income_reduction: Decimal = Field(ge=0, le=1)
    stage_2_dti_increase: Decimal = Field(ge=0, le=1)
    stage_2_external_score_drop: int = Field(ge=0)
    stage_3_qualitative_events: tuple[str, ...] = Field(min_length=1)
    score_only_staging_allowed: bool = False

    @model_validator(mode="after")
    def ordered(self) -> "StagingPolicy":
        if self.stage_3_days_past_due <= self.stage_2_days_past_due:
            raise ValueError("stage 3 threshold must exceed stage 2 threshold")
        if len(set(self.stage_3_qualitative_events)) != len(self.stage_3_qualitative_events):
            raise ValueError("stage 3 qualitative events must be unique")
        return self


class ScenarioPolicy(StrictModel):
    scenario_id: str = Field(min_length=1)
    kind: Literal["upside", "base", "downside"]
    weight: Decimal = Field(ge=0, le=1)
    pd_multiplier: Decimal = Field(gt=0)
    lgd_multiplier: Decimal = Field(gt=0)


class LGDPolicy(StrictModel):
    base: Decimal = Field(ge=0, le=1)
    downturn_multiplier: Decimal = Field(ge=1)


class RoundingPolicy(StrictModel):
    currency: Literal["BRL"]
    monetary_quantum: Literal["0.01"]
    rounding_mode: Literal["ROUND_HALF_EVEN"]
    rate_quantum: Literal["0.00000001"]


class RiskPolicy(StrictModel):
    metadata: PolicyMetadata
    rounding: RoundingPolicy
    rating_bands: tuple[RatingBand, ...] = Field(min_length=1)
    staging: StagingPolicy
    lgd_by_guarantee: dict[str, LGDPolicy]
    ccf_by_product: dict[str, Decimal]
    scenarios: tuple[ScenarioPolicy, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def cross_field_invariants(self) -> "RiskPolicy":
        bands = sorted(self.rating_bands, key=lambda item: item.lower_inclusive)
        if bands[0].lower_inclusive != 0:
            raise ValueError("rating bands must start at zero")
        for previous, current in zip(bands, bands[1:]):
            if previous.upper_exclusive != current.lower_inclusive:
                raise ValueError("rating bands must be contiguous and non-overlapping")
        if bands[-1].upper_exclusive != 101:
            raise ValueError("rating bands must cover scores through 100")
        ratings = [band.rating for band in bands]
        if len(ratings) != len(set(ratings)):
            raise ValueError("ratings must be unique")
        if any(not Decimal("0") <= value <= Decimal("1") for value in self.ccf_by_product.values()):
            raise ValueError("CCF values must be between zero and one")
        kinds = [scenario.kind for scenario in self.scenarios]
        if sorted(kinds) != ["base", "downside", "upside"]:
            raise ValueError("exactly one base, upside and downside scenario is required")
        if sum((scenario.weight for scenario in self.scenarios), Decimal("0")) != Decimal("1"):
            raise ValueError("scenario weights must sum to one")
        return self
