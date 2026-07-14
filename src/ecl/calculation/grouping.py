"""Statistical eligibility and homogeneity controls for collective ECL."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from ...domain.conventions import DecimalInput, decimal_from, money, non_empty, rate
from ...domain.exceptions import DomainValidationError

POLICY_PATH = Path(__file__).resolve().parents[3] / "config" / "ecl_grouping" / "2026.07.1.json"
QUANTUM = Decimal("0.00000001")


class ECLMeasurementRoute(StrEnum):
    INDIVIDUAL = "individual"
    COLLECTIVE_ELIGIBLE = "collective_eligible"


@dataclass(frozen=True, slots=True)
class ECLGroupingPolicy:
    policy_version: str
    evidence_status: str
    individual_ead_threshold: Decimal
    minimum_group_size: int
    minimum_non_score_dimensions: int
    allowed_dimensions: tuple[str, ...]
    maximum_coefficient_of_variation: tuple[tuple[str, Decimal], ...]
    maximum_single_exposure_share: Decimal
    sha256: str


@dataclass(frozen=True, slots=True)
class GroupingMember:
    contract_id: str
    product_code: str
    collateral_type: str
    vintage_year: int
    behavioral_risk_bucket: str
    score_band: str
    pd_12m: DecimalInput
    lgd: DecimalInput
    ead: DecimalInput

    def __post_init__(self) -> None:
        for field in (
            "contract_id",
            "product_code",
            "collateral_type",
            "behavioral_risk_bucket",
            "score_band",
        ):
            object.__setattr__(self, field, non_empty(getattr(self, field), field=field))
        if self.vintage_year < 1900:
            raise DomainValidationError("vintage_year is invalid")
        object.__setattr__(self, "pd_12m", rate(self.pd_12m, field="pd_12m"))
        object.__setattr__(self, "lgd", rate(self.lgd, field="lgd"))
        ead = money(self.ead, field="ead")
        if ead == 0:
            raise DomainValidationError("grouping EAD must be positive")
        object.__setattr__(self, "ead", ead)

    @property
    def vintage_bucket(self) -> str:
        start = self.vintage_year - self.vintage_year % 2
        return f"{start}-{start + 1}"


@dataclass(frozen=True, slots=True)
class HomogeneousGroupDefinition:
    group_name: str
    dimensions: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "group_name", non_empty(self.group_name, field="group_name"))
        if not self.dimensions or len(self.dimensions) != len(set(self.dimensions)):
            raise DomainValidationError("group dimensions must be unique and non-empty")


@dataclass(frozen=True, slots=True)
class HomogeneityMetric:
    variable: str
    mean: Decimal
    coefficient_of_variation: Decimal
    maximum_allowed: Decimal
    passed: bool


@dataclass(frozen=True, slots=True)
class HomogeneityReport:
    group_id: str
    member_count: int
    metrics: tuple[HomogeneityMetric, ...]
    maximum_single_exposure_share: Decimal
    blockers: tuple[str, ...]
    valid: bool
    policy_version: str
    policy_hash: str


def load_ecl_grouping_policy(path: Path = POLICY_PATH) -> ECLGroupingPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    metadata = document["metadata"]
    return ECLGroupingPolicy(
        metadata["policy_version"],
        metadata["evidence_status"],
        Decimal(document["individual_ead_threshold"]),
        int(document["minimum_group_size"]),
        int(document["minimum_non_score_dimensions"]),
        tuple(document["allowed_dimensions"]),
        tuple(
            (name, Decimal(value))
            for name, value in document["maximum_coefficient_of_variation"].items()
        ),
        Decimal(document["maximum_single_exposure_share"]),
        sha256(raw).hexdigest(),
    )


def route_ecl_measurement(member: GroupingMember, policy: ECLGroupingPolicy) -> ECLMeasurementRoute:
    return (
        ECLMeasurementRoute.INDIVIDUAL
        if decimal_from(member.ead, field="ead") >= policy.individual_ead_threshold
        else ECLMeasurementRoute.COLLECTIVE_ELIGIBLE
    )


def _dimension_value(member: GroupingMember, dimension: str) -> str:
    value = getattr(member, dimension)
    return str(value)


def build_homogeneous_group_id(
    member: GroupingMember,
    definition: HomogeneousGroupDefinition,
    policy: ECLGroupingPolicy,
) -> str:
    unknown = set(definition.dimensions) - set(policy.allowed_dimensions)
    if unknown:
        raise DomainValidationError(f"unsupported grouping dimensions: {sorted(unknown)}")
    non_score = [item for item in definition.dimensions if item != "score_band"]
    if len(non_score) < policy.minimum_non_score_dimensions:
        raise DomainValidationError(
            "collective grouping cannot be based only on arbitrary score bands"
        )
    components = [definition.group_name]
    components.extend(
        f"{dimension}={_dimension_value(member, dimension)}" for dimension in definition.dimensions
    )
    return "|".join(components)


def _coefficient_of_variation(values: tuple[Decimal, ...]) -> tuple[Decimal, Decimal]:
    mean = sum(values, Decimal("0")) / Decimal(len(values))
    if mean == 0:
        return mean, Decimal("0") if all(value == 0 for value in values) else Decimal("999")
    variance = sum(((value - mean) ** 2 for value in values), Decimal("0")) / Decimal(len(values))
    return mean, (variance.sqrt() / mean).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def validate_homogeneous_group(
    members: tuple[GroupingMember, ...],
    definition: HomogeneousGroupDefinition,
    policy: ECLGroupingPolicy,
) -> HomogeneityReport:
    if not members:
        raise DomainValidationError("homogeneous group requires members")
    group_ids = {build_homogeneous_group_id(member, definition, policy) for member in members}
    if len(group_ids) != 1:
        raise DomainValidationError("members do not share the proposed grouping dimensions")
    blockers: list[str] = []
    ids = [member.contract_id for member in members]
    if len(ids) != len(set(ids)):
        blockers.append("duplicate_contracts")
    if len(members) < policy.minimum_group_size:
        blockers.append("group_below_minimum_size")
    if any(
        route_ecl_measurement(member, policy) == ECLMeasurementRoute.INDIVIDUAL
        for member in members
    ):
        blockers.append("material_exposure_requires_individual_measurement")
    limits = dict(policy.maximum_coefficient_of_variation)
    metrics: list[HomogeneityMetric] = []
    for variable in ("pd_12m", "lgd", "ead"):
        values = tuple(
            decimal_from(getattr(member, variable), field=variable) for member in members
        )
        mean, cv = _coefficient_of_variation(values)
        passed = cv <= limits[variable]
        metrics.append(HomogeneityMetric(variable, mean, cv, limits[variable], passed))
        if not passed:
            blockers.append(f"{variable}_dispersion_above_limit")
    total_ead = sum((decimal_from(member.ead, field="ead") for member in members), Decimal("0"))
    concentration = max(decimal_from(member.ead, field="ead") for member in members) / total_ead
    concentration = concentration.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    if concentration > policy.maximum_single_exposure_share:
        blockers.append("single_exposure_concentration_above_limit")
    return HomogeneityReport(
        next(iter(group_ids)),
        len(members),
        tuple(metrics),
        concentration,
        tuple(dict.fromkeys(blockers)),
        not blockers,
        policy.policy_version,
        policy.sha256,
    )
