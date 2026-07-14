"""Point-in-time workout dataset linking defaults to observed recovery evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ...data.synthetic.events import CreditEventHistory
from ...data.synthetic.population import SyntheticPortfolio, _add_months
from ...domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class WorkoutCashFlow:
    recovery_date: date
    source: str
    gross_amount: Decimal
    cost_amount: Decimal
    net_amount: Decimal
    post_writeoff: bool


@dataclass(frozen=True, slots=True)
class LGDWorkoutRecord:
    default_id: str
    contract_id: str
    default_date: date
    default_cohort: str
    product_code: str
    exposure_at_default: Decimal
    effective_interest_rate: Decimal
    workout_window_months: int
    workout_end_date: date
    observation_end_date: date
    is_censored: bool
    is_redefault: bool
    outcome_status: str
    cure_date: date | None
    writeoff_date: date | None
    writeoff_amount: Decimal
    collateral_type: str | None
    collateral_appraised_value: Decimal
    collateral_enforceable_share: Decimal
    gross_recovery_total: Decimal
    recovery_cost_total: Decimal
    net_recovery_total: Decimal
    cashflows: tuple[WorkoutCashFlow, ...]


@dataclass(frozen=True, slots=True)
class LGDWorkoutDataset:
    records: tuple[LGDWorkoutRecord, ...]
    version: str
    workout_window_months: int
    observation_end_date: date


def _cohort(value: date) -> str:
    return f"{value.year}-Q{(value.month - 1) // 3 + 1}"


def build_lgd_workout_dataset(
    population: SyntheticPortfolio,
    events: CreditEventHistory,
    *,
    observation_end_date: date,
    workout_window_months: int = 24,
) -> LGDWorkoutDataset:
    if workout_window_months <= 0:
        raise DomainValidationError("workout_window_months must be positive")
    contracts = {item.contract_id: item for item in population.contracts}
    collateral = {item.contract_id: item for item in population.collateral}
    records: list[LGDWorkoutRecord] = []
    for default in sorted(events.defaults, key=lambda item: (item.default_date, item.default_id)):
        if default.default_date > observation_end_date:
            continue
        contract = contracts.get(default.contract_id)
        if contract is None:
            raise DomainValidationError(
                f"default references unknown contract: {default.contract_id}"
            )
        workout_end = _add_months(default.default_date, workout_window_months)
        evidence_cutoff = min(workout_end, observation_end_date)
        recoveries = sorted(
            (
                item
                for item in events.recoveries
                if item.default_id == default.default_id
                and default.default_date < item.recovery_date <= evidence_cutoff
            ),
            key=lambda item: (item.recovery_date, item.recovery_id),
        )
        cashflows = tuple(
            WorkoutCashFlow(
                item.recovery_date,
                item.source,
                item.gross_amount,
                item.cost_amount,
                item.net_amount,
                item.post_writeoff,
            )
            for item in recoveries
        )
        cure = next(
            (
                item
                for item in events.cures
                if item.default_id == default.default_id and item.cure_date <= evidence_cutoff
            ),
            None,
        )
        writeoff = next(
            (
                item
                for item in events.writeoffs
                if item.default_id == default.default_id and item.writeoff_date <= evidence_cutoff
            ),
            None,
        )
        guarantee = collateral.get(default.contract_id)
        if cure is not None:
            outcome = "cured"
        elif writeoff is not None:
            outcome = "written_off"
        else:
            outcome = "open_censored" if observation_end_date < workout_end else "open_complete"
        records.append(
            LGDWorkoutRecord(
                default.default_id,
                default.contract_id,
                default.default_date,
                _cohort(default.default_date),
                contract.product_code,
                default.exposure_at_default,
                contract.effective_interest_rate,
                workout_window_months,
                workout_end,
                observation_end_date,
                observation_end_date < workout_end,
                default.is_redefault,
                outcome,
                cure.cure_date if cure is not None else None,
                writeoff.writeoff_date if writeoff is not None else None,
                writeoff.amount if writeoff is not None else Decimal("0"),
                guarantee.collateral_type if guarantee is not None else None,
                guarantee.appraised_value if guarantee is not None else Decimal("0"),
                guarantee.enforceable_share if guarantee is not None else Decimal("0"),
                sum((item.gross_amount for item in cashflows), Decimal("0")),
                sum((item.cost_amount for item in cashflows), Decimal("0")),
                sum((item.net_amount for item in cashflows), Decimal("0")),
                cashflows,
            )
        )
    return LGDWorkoutDataset(tuple(records), "0.1.0", workout_window_months, observation_end_date)
