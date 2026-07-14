"""Discounted realized workout LGD with explicit cure and bounds policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

from ...domain.exceptions import DomainValidationError
from .workout import LGDWorkoutDataset, LGDWorkoutRecord

QUANTUM = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class RealizedLGDPolicy:
    policy_version: str
    effective_from: date
    evidence_status: str
    discount_rate: str
    cure_treatment: str
    lower_bound: Decimal
    upper_bound: Decimal
    out_of_bounds_treatment: str
    sha256: str


@dataclass(frozen=True, slots=True)
class RealizedLGD:
    default_id: str
    contract_id: str
    exposure_at_default: Decimal
    discounted_gross_recoveries: Decimal
    discounted_recovery_costs: Decimal
    discounted_cure_value: Decimal
    discounted_net_recoveries: Decimal
    raw_lgd: Decimal
    realized_lgd: Decimal
    bound_action: str
    outcome_type: str
    is_censored: bool
    policy_version: str
    policy_sha256: str
    status: str


def load_realized_lgd_policy(path: Path) -> RealizedLGDPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document["schema_version"] != "1.0.0":
        raise DomainValidationError("unsupported realized LGD policy schema")
    lower = Decimal(document["lower_bound"])
    upper = Decimal(document["upper_bound"])
    if lower < 0 or upper > 1 or lower >= upper:
        raise DomainValidationError("realized LGD policy bounds are invalid")
    return RealizedLGDPolicy(
        document["policy_version"],
        date.fromisoformat(document["effective_from"]),
        document["evidence_status"],
        document["discount_rate"],
        document["cure_treatment"],
        lower,
        upper,
        document["out_of_bounds_treatment"],
        sha256(raw).hexdigest(),
    )


def _discount(amount: Decimal, start: date, end: date, annual_rate: Decimal) -> Decimal:
    if annual_rate <= Decimal("-1") or end < start:
        raise DomainValidationError("LGD discount rate or cash-flow date is invalid")
    years = Decimal((end - start).days) / Decimal("365")
    with localcontext() as context:
        context.prec = 28
        value = amount / (Decimal("1") + annual_rate) ** years
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def calculate_realized_lgd(record: LGDWorkoutRecord, policy: RealizedLGDPolicy) -> RealizedLGD:
    if record.exposure_at_default <= 0:
        raise DomainValidationError("EAD at default must be positive")
    gross = sum(
        (
            _discount(
                item.gross_amount,
                record.default_date,
                item.recovery_date,
                record.effective_interest_rate,
            )
            for item in record.cashflows
        ),
        Decimal("0"),
    )
    costs = sum(
        (
            _discount(
                item.cost_amount,
                record.default_date,
                item.recovery_date,
                record.effective_interest_rate,
            )
            for item in record.cashflows
        ),
        Decimal("0"),
    )
    cure_value = Decimal("0")
    if record.cure_date is not None:
        residual = max(Decimal("0"), record.exposure_at_default - record.gross_recovery_total)
        cure_value = _discount(
            residual, record.default_date, record.cure_date, record.effective_interest_rate
        )
    net = gross - costs + cure_value
    raw = (Decimal("1") - net / record.exposure_at_default).quantize(
        QUANTUM, rounding=ROUND_HALF_EVEN
    )
    if raw < policy.lower_bound:
        bounded = policy.lower_bound
        action = "floored_at_zero"
    elif raw > policy.upper_bound:
        bounded = policy.upper_bound
        action = "capped_at_one"
    else:
        bounded = raw
        action = "none"
    outcome = "cure_lgd" if record.cure_date is not None else "loss_lgd"
    status = "censored_provisional" if record.is_censored else "complete_synthetic"
    return RealizedLGD(
        record.default_id,
        record.contract_id,
        record.exposure_at_default,
        gross,
        costs,
        cure_value,
        net,
        raw,
        bounded,
        action,
        outcome,
        record.is_censored,
        policy.policy_version,
        policy.sha256,
        status,
    )


def calculate_realized_lgd_dataset(
    dataset: LGDWorkoutDataset, policy: RealizedLGDPolicy
) -> tuple[RealizedLGD, ...]:
    return tuple(calculate_realized_lgd(item, policy) for item in dataset.records)
