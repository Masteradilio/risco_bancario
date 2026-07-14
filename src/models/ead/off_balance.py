"""Parameterized EAD for loan commitments and financial guarantees."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

from ...data.synthetic.longitudinal import LongitudinalPortfolio, MonthlySnapshotRecord
from ...data.synthetic.population import SyntheticPortfolio
from ...domain.exceptions import DomainValidationError

QUANTUM = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class OffBalanceAssumption:
    facility_type: str
    monthly_utilization_probability: Decimal
    conditional_utilized_share: Decimal
    utilization_sensitivity: Decimal


@dataclass(frozen=True, slots=True)
class OffBalanceEADPolicy:
    policy_version: str
    effective_from: date
    evidence_status: str
    probability_basis: str
    assumptions: tuple[OffBalanceAssumption, ...]
    minimum_risk_multiplier: Decimal
    maximum_risk_multiplier: Decimal
    limit_treatment: str
    sha256: str


@dataclass(frozen=True, slots=True)
class OffBalanceEADProjection:
    facility_type: str
    horizon_months: int
    original_limit: Decimal
    current_limit: Decimal
    current_drawn: Decimal
    current_utilization: Decimal
    available_amount: Decimal
    risk_multiplier: Decimal
    monthly_utilization_probability: Decimal
    cumulative_utilization_probability: Decimal
    conditional_utilized_share: Decimal
    expected_incremental_utilization: Decimal
    projected_ead: Decimal
    limit_status: str
    status: str
    policy_version: str
    policy_sha256: str


@dataclass(frozen=True, slots=True)
class OffBalancePortfolioProjection:
    contract_id: str
    product_code: str
    reference_date: date
    projection: OffBalanceEADProjection


def load_off_balance_ead_policy(path: Path) -> OffBalanceEADPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document["schema_version"] != "1.0.0":
        raise DomainValidationError("unsupported off-balance EAD policy schema")
    assumptions = tuple(
        OffBalanceAssumption(
            facility_type,
            Decimal(values["monthly_utilization_probability"]),
            Decimal(values["conditional_utilized_share"]),
            Decimal(values["utilization_sensitivity"]),
        )
        for facility_type, values in sorted(document["assumptions"].items())
    )
    if {item.facility_type for item in assumptions} != {"commitment", "financial_guarantee"}:
        raise DomainValidationError("off-balance policy requires commitment and guarantee")
    if any(
        not Decimal("0") <= item.monthly_utilization_probability <= Decimal("1")
        or not Decimal("0") <= item.conditional_utilized_share <= Decimal("1")
        or item.utilization_sensitivity < 0
        for item in assumptions
    ):
        raise DomainValidationError("off-balance EAD assumptions are invalid")
    bounds = document["risk_multiplier_bounds"]
    minimum = Decimal(bounds["minimum"])
    maximum = Decimal(bounds["maximum"])
    if minimum < 0 or maximum <= minimum:
        raise DomainValidationError("off-balance risk multiplier bounds are invalid")
    return OffBalanceEADPolicy(
        document["policy_version"],
        date.fromisoformat(document["effective_from"]),
        document["evidence_status"],
        document["probability_basis"],
        assumptions,
        minimum,
        maximum,
        document["limit_treatment"],
        sha256(raw).hexdigest(),
    )


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def project_off_balance_ead(
    *,
    facility_type: str,
    horizon_months: int,
    original_limit: Decimal,
    current_limit: Decimal,
    current_drawn: Decimal,
    risk_multiplier: Decimal,
    policy: OffBalanceEADPolicy,
) -> OffBalanceEADProjection:
    assumption = next(
        (item for item in policy.assumptions if item.facility_type == facility_type), None
    )
    if assumption is None:
        raise DomainValidationError("unsupported off-balance facility type")
    if horizon_months <= 0:
        raise DomainValidationError("off-balance EAD horizon must be positive")
    if original_limit < 0 or current_limit < 0 or current_drawn < 0:
        raise DomainValidationError("off-balance EAD amounts must be non-negative")
    if current_limit > original_limit or current_drawn > current_limit:
        raise DomainValidationError("current off-balance limit or drawn amount is invalid")
    if not policy.minimum_risk_multiplier <= risk_multiplier <= policy.maximum_risk_multiplier:
        raise DomainValidationError("off-balance risk multiplier is outside policy bounds")
    if current_limit == 0:
        utilization = Decimal("0")
        limit_status = "cancelled"
    else:
        utilization = current_drawn / current_limit
        limit_status = "reduced" if current_limit < original_limit else "unchanged"
    monthly = min(
        Decimal("1"),
        assumption.monthly_utilization_probability
        * risk_multiplier
        * (Decimal("1") + assumption.utilization_sensitivity * utilization),
    )
    with localcontext() as context:
        context.prec = 28
        cumulative = Decimal("1") - (Decimal("1") - monthly) ** horizon_months
    available = current_limit - current_drawn
    incremental = available * cumulative * assumption.conditional_utilized_share
    projected = min(current_limit, current_drawn + incremental)
    return OffBalanceEADProjection(
        facility_type,
        horizon_months,
        original_limit,
        current_limit,
        current_drawn,
        _quantize(utilization),
        _quantize(available),
        risk_multiplier,
        _quantize(monthly),
        _quantize(cumulative),
        assumption.conditional_utilized_share,
        _quantize(incremental),
        _quantize(projected),
        limit_status,
        "parameterized_not_estimated",
        policy.policy_version,
        policy.sha256,
    )


def build_off_balance_portfolio_projections(
    population: SyntheticPortfolio,
    history: LongitudinalPortfolio,
    policy: OffBalanceEADPolicy,
    *,
    horizon_months: int = 12,
    risk_multiplier: Decimal = Decimal("1"),
) -> tuple[OffBalancePortfolioProjection, ...]:
    snapshots: dict[str, list[MonthlySnapshotRecord]] = {}
    for item in history.snapshots:
        snapshots.setdefault(item.contract_id, []).append(item)
    results: list[OffBalancePortfolioProjection] = []
    for contract in population.contracts:
        if contract.facility_type not in {"commitment", "financial_guarantee"}:
            continue
        contract_snapshots = snapshots.get(contract.contract_id, [])
        if not contract_snapshots:
            raise DomainValidationError("off-balance contract has no observable snapshot")
        reference = min(contract_snapshots, key=lambda item: item.reference_date)
        projection = project_off_balance_ead(
            facility_type=contract.facility_type,
            horizon_months=horizon_months,
            original_limit=contract.credit_limit,
            current_limit=reference.credit_limit,
            current_drawn=reference.balance,
            risk_multiplier=risk_multiplier,
            policy=policy,
        )
        results.append(
            OffBalancePortfolioProjection(
                contract.contract_id,
                contract.product_code,
                reference.reference_date,
                projection,
            )
        )
    return tuple(results)
