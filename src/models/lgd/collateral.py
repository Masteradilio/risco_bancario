"""Versioned collateral recovery projection and double-counting control."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

from ...data.synthetic.population import CollateralRecord, _add_months
from ...domain.exceptions import DomainValidationError
from .realized import discount_recovery_cash_flow
from .workout import LGDWorkoutRecord

QUANTUM = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class CollateralAssumption:
    collateral_type: str
    annual_value_change: Decimal
    haircut: Decimal
    cost_rate: Decimal
    execution_months: int


@dataclass(frozen=True, slots=True)
class CollateralSensitivity:
    scenario: str
    annual_value_change_delta: Decimal
    haircut_delta: Decimal
    cost_rate_delta: Decimal
    execution_months_delta: int


@dataclass(frozen=True, slots=True)
class CollateralPolicy:
    policy_version: str
    effective_from: date
    evidence_status: str
    assumptions: tuple[CollateralAssumption, ...]
    sensitivities: tuple[CollateralSensitivity, ...]
    double_counting_rule: str
    sha256: str


@dataclass(frozen=True, slots=True)
class CollateralProjection:
    default_id: str
    collateral_type: str
    scenario: str
    value_at_default: Decimal
    enforceable_value: Decimal
    haircut: Decimal
    projected_gross_recovery: Decimal
    projected_execution_cost: Decimal
    execution_date: date
    projected_discounted_net_recovery: Decimal
    discounted_noncollateral_recovery: Decimal
    excluded_observed_collateral_recovery: Decimal
    collateral_recovery_used: Decimal
    combined_discounted_recovery: Decimal
    policy_version: str
    policy_sha256: str


def load_collateral_policy(path: Path) -> CollateralPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document["schema_version"] != "1.0.0":
        raise DomainValidationError("unsupported collateral policy schema")
    assumptions = tuple(
        CollateralAssumption(
            collateral_type,
            Decimal(values["annual_value_change"]),
            Decimal(values["haircut"]),
            Decimal(values["cost_rate"]),
            int(values["execution_months"]),
        )
        for collateral_type, values in sorted(document["assumptions"].items())
    )
    sensitivities = tuple(
        CollateralSensitivity(
            scenario,
            Decimal(values["annual_value_change_delta"]),
            Decimal(values["haircut_delta"]),
            Decimal(values["cost_rate_delta"]),
            int(values["execution_months_delta"]),
        )
        for scenario, values in sorted(document["sensitivities"].items())
    )
    if {item.scenario for item in sensitivities} != {"upside", "base", "downside"}:
        raise DomainValidationError("collateral policy requires upside, base and downside")
    if any(
        not Decimal("0") <= item.haircut <= Decimal("1")
        or not Decimal("0") <= item.cost_rate <= Decimal("1")
        or item.execution_months <= 0
        or item.annual_value_change <= Decimal("-1")
        for item in assumptions
    ):
        raise DomainValidationError("collateral base assumptions are invalid")
    return CollateralPolicy(
        document["policy_version"],
        date.fromisoformat(document["effective_from"]),
        document["evidence_status"],
        assumptions,
        sensitivities,
        document["double_counting_rule"],
        sha256(raw).hexdigest(),
    )


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _effective_assumption(
    policy: CollateralPolicy, collateral_type: str, scenario: str
) -> CollateralAssumption:
    base = next(
        (item for item in policy.assumptions if item.collateral_type == collateral_type), None
    )
    sensitivity = next((item for item in policy.sensitivities if item.scenario == scenario), None)
    if base is None or sensitivity is None:
        raise DomainValidationError("collateral type or sensitivity scenario is unsupported")
    haircut = base.haircut + sensitivity.haircut_delta
    cost = base.cost_rate + sensitivity.cost_rate_delta
    execution = base.execution_months + sensitivity.execution_months_delta
    change = base.annual_value_change + sensitivity.annual_value_change_delta
    if not Decimal("0") <= haircut <= Decimal("1") or not Decimal("0") <= cost <= Decimal("1"):
        raise DomainValidationError("effective collateral haircut or cost is invalid")
    if execution <= 0 or change <= Decimal("-1"):
        raise DomainValidationError("effective collateral timing or value change is invalid")
    return CollateralAssumption(collateral_type, change, haircut, cost, execution)


def _discounted_recoveries(
    record: LGDWorkoutRecord,
) -> tuple[Decimal, Decimal]:
    noncollateral = Decimal("0")
    collateral = Decimal("0")
    for cashflow in record.cashflows:
        discounted = discount_recovery_cash_flow(
            cashflow.net_amount,
            record.default_date,
            cashflow.recovery_date,
            record.effective_interest_rate,
        )
        if cashflow.source == "collateral_execution":
            collateral += discounted
        else:
            noncollateral += discounted
    return _quantize(noncollateral), _quantize(collateral)


def project_collateral_recovery(
    record: LGDWorkoutRecord,
    collateral: CollateralRecord | None,
    policy: CollateralPolicy,
    *,
    scenario: str = "base",
) -> CollateralProjection:
    noncollateral, observed_collateral = _discounted_recoveries(record)
    if collateral is None:
        if observed_collateral != 0:
            raise DomainValidationError("observed collateral cash flow has no collateral record")
        return CollateralProjection(
            record.default_id,
            "none",
            scenario,
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            record.default_date,
            Decimal("0"),
            noncollateral,
            Decimal("0"),
            Decimal("0"),
            min(noncollateral, record.exposure_at_default),
            policy.policy_version,
            policy.sha256,
        )
    if (
        collateral.contract_id != record.contract_id
        or collateral.valuation_date > record.default_date
    ):
        raise DomainValidationError("collateral record does not match the default point in time")
    assumption = _effective_assumption(policy, collateral.collateral_type, scenario)
    years = Decimal((record.default_date - collateral.valuation_date).days) / Decimal("365")
    with localcontext() as context:
        context.prec = 28
        value_at_default = (
            collateral.appraised_value * (Decimal("1") + assumption.annual_value_change) ** years
        )
    value_at_default = _quantize(value_at_default)
    enforceable = _quantize(value_at_default * collateral.enforceable_share)
    gross = min(record.exposure_at_default, _quantize(enforceable * (1 - assumption.haircut)))
    cost = _quantize(gross * assumption.cost_rate)
    execution_date = _add_months(record.default_date, assumption.execution_months)
    projected_discounted = discount_recovery_cash_flow(
        gross - cost,
        record.default_date,
        execution_date,
        record.effective_interest_rate,
    )
    headroom = max(Decimal("0"), record.exposure_at_default - noncollateral)
    collateral_used = min(projected_discounted, headroom)
    combined = min(record.exposure_at_default, noncollateral + collateral_used)
    return CollateralProjection(
        record.default_id,
        collateral.collateral_type,
        scenario,
        value_at_default,
        enforceable,
        assumption.haircut,
        gross,
        cost,
        execution_date,
        projected_discounted,
        noncollateral,
        observed_collateral,
        collateral_used,
        combined,
        policy.policy_version,
        policy.sha256,
    )


def project_collateral_sensitivities(
    record: LGDWorkoutRecord,
    collateral: CollateralRecord | None,
    policy: CollateralPolicy,
) -> tuple[CollateralProjection, ...]:
    return tuple(
        project_collateral_recovery(record, collateral, policy, scenario=scenario)
        for scenario in ("upside", "base", "downside")
    )
