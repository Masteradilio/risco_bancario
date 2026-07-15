"""Monthly observable states for a synthetic contract population."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from hashlib import sha256
from math import sin
from pathlib import Path
from random import Random

from ...infrastructure.configuration import load_risk_policy
from .population import CENT, ContractRecord, ScheduleRecord, SyntheticPortfolio, _add_months

_POLICY_PATH = Path(__file__).resolve().parents[3] / "config" / "risk_policy" / "2026.07.1.json"
_RATING_BANDS = tuple(
    sorted(
        load_risk_policy(_POLICY_PATH).policy.rating_bands, key=lambda item: item.lower_inclusive
    )
)


@dataclass(frozen=True, slots=True)
class MonthlySnapshotRecord:
    contract_id: str
    client_id: str
    reference_date: date
    origination_cohort: str
    months_on_book: int
    balance: Decimal
    credit_limit: Decimal
    utilization: Decimal
    scheduled_payment: Decimal
    paid_amount: Decimal
    days_past_due: int
    behavior_score: Decimal
    rating: str
    modified: bool
    policy_version: str


@dataclass(frozen=True, slots=True)
class ModificationRecord:
    modification_id: str
    contract_id: str
    modification_date: date
    modification_type: str
    old_maturity_date: date
    new_maturity_date: date
    concession: bool


@dataclass(frozen=True, slots=True)
class LongitudinalPortfolio:
    snapshots: tuple[MonthlySnapshotRecord, ...]
    modifications: tuple[ModificationRecord, ...]
    generator_version: str
    seed: int

    def as_tables(self) -> dict[str, list[dict[str, object]]]:
        return {
            "monthly_snapshots": [asdict(item) for item in self.snapshots],
            "modifications": [asdict(item) for item in self.modifications],
        }


def _contract_rng(seed: int, contract_id: str) -> Random:
    digest = sha256(f"{seed}:monthly:{contract_id}".encode()).digest()
    return Random(int.from_bytes(digest[:8], "big"))  # noqa: S311 - deterministic synthetic data


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


def _ratio(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN)


def _rating(score: Decimal) -> str:
    value = score * 100
    return next(
        band.rating
        for band in _RATING_BANDS
        if band.lower_inclusive <= value < band.upper_exclusive
    )


def _schedule_by_month(rows: tuple[ScheduleRecord, ...]) -> dict[date, ScheduleRecord]:
    return {date(item.due_date.year, item.due_date.month, 1): item for item in rows}


def _base_risk(contract: ContractRecord) -> float:
    return {
        "mortgage": 0.08,
        "vehicle_finance": 0.15,
        "personal_loan": 0.24,
        "credit_card": 0.32,
        "overdraft": 0.38,
        "credit_commitment": 0.18,
        "financial_guarantee": 0.20,
        "acquired_distressed": 0.72,
    }[contract.product_code]


def generate_monthly_history(
    portfolio: SyntheticPortfolio,
    *,
    start_date: date = date(2016, 1, 1),
    end_date: date = date(2025, 12, 1),
) -> LongitudinalPortfolio:
    schedules_by_contract: dict[str, tuple[ScheduleRecord, ...]] = {}
    for contract in portfolio.contracts:
        schedules_by_contract[contract.contract_id] = tuple(
            item for item in portfolio.schedules if item.contract_id == contract.contract_id
        )

    snapshots: list[MonthlySnapshotRecord] = []
    modifications: list[ModificationRecord] = []
    for contract in portfolio.contracts:
        rng = _contract_rng(portfolio.seed, contract.contract_id)
        schedule = _schedule_by_month(schedules_by_contract[contract.contract_id])
        current = max(
            date(contract.origination_date.year, contract.origination_date.month, 1), start_date
        )
        effective_maturity = contract.maturity_date
        revolving_balance = contract.initial_drawn_amount
        risk = _base_risk(contract)
        days_past_due = 0
        modified = False
        while current <= end_date and current <= effective_maturity:
            months_on_book = (
                (current.year - contract.origination_date.year) * 12
                + current.month
                - contract.origination_date.month
            )
            macro_cycle = 0.10 * sin(months_on_book / 9.0) + (
                0.12 if 54 <= months_on_book <= 72 else 0.0
            )
            shock = rng.uniform(-0.08, 0.08)
            risk = min(
                0.99, max(0.01, 0.82 * risk + 0.18 * (_base_risk(contract) + macro_cycle + shock))
            )

            if risk >= 0.68 and rng.random() < risk * 0.38:
                days_past_due = min(120, days_past_due + 30)
            elif risk < 0.40 and days_past_due and rng.random() < 0.55:
                days_past_due = max(0, days_past_due - 30)

            due = schedule.get(current)
            if contract.facility_type == "amortized":
                balance = (
                    due.opening_balance
                    if due
                    else contract.initial_drawn_amount if months_on_book == 0 else Decimal("0.00")
                )
                scheduled_payment = due.payment if due else Decimal("0.00")
            elif contract.facility_type == "revolving":
                target = min(
                    0.98,
                    max(
                        0.02,
                        float(revolving_balance / contract.credit_limit) * 0.75
                        + risk * 0.25
                        + rng.uniform(-0.08, 0.08),
                    ),
                )
                revolving_balance = _money(contract.credit_limit * Decimal(str(target)))
                balance = revolving_balance
                scheduled_payment = _money(balance * Decimal("0.15"))
            else:
                balance = contract.initial_drawn_amount
                scheduled_payment = Decimal("0.00")

            paid_amount = Decimal("0.00") if days_past_due >= 60 else scheduled_payment
            utilization = _ratio(balance / contract.credit_limit if contract.credit_limit else 0)
            observed_score = min(0.99999999, max(0.0, risk + min(days_past_due, 90) / 300.0))

            if not modified and int(contract.contract_id[-4:]) % 9 == 0 and months_on_book == 18:
                old_maturity = effective_maturity
                effective_maturity = _add_months(effective_maturity, 12)
                modified = True
                modifications.append(
                    ModificationRecord(
                        f"MOD-{len(modifications) + 1:07d}",
                        contract.contract_id,
                        current,
                        "term_extension",
                        old_maturity,
                        effective_maturity,
                        True,
                    )
                )

            snapshots.append(
                MonthlySnapshotRecord(
                    contract.contract_id,
                    contract.client_id,
                    current,
                    f"{contract.origination_date:%Y-%m}",
                    months_on_book,
                    balance,
                    contract.credit_limit,
                    utilization,
                    scheduled_payment,
                    paid_amount,
                    days_past_due,
                    _ratio(observed_score),
                    _rating(_ratio(observed_score)),
                    modified,
                    contract.policy_version,
                )
            )
            current = _add_months(current, 1)

    return LongitudinalPortfolio(tuple(snapshots), tuple(modifications), "0.1.0", portfolio.seed)
