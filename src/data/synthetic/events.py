"""Post-observation credit events, collections and recovery cash flows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from hashlib import sha256
from random import Random

from .longitudinal import LongitudinalPortfolio, MonthlySnapshotRecord
from .population import CENT, SyntheticPortfolio, _add_months


@dataclass(frozen=True, slots=True)
class DefaultEventRecord:
    default_id: str
    contract_id: str
    default_date: date
    exposure_at_default: Decimal
    trigger: str
    is_redefault: bool


@dataclass(frozen=True, slots=True)
class CollectionEventRecord:
    collection_id: str
    default_id: str
    contract_id: str
    event_date: date
    action: str


@dataclass(frozen=True, slots=True)
class RecoveryRecord:
    recovery_id: str
    default_id: str
    contract_id: str
    recovery_date: date
    source: str
    gross_amount: Decimal
    cost_amount: Decimal
    cost_type: str
    net_amount: Decimal
    post_writeoff: bool


@dataclass(frozen=True, slots=True)
class CureRecord:
    cure_id: str
    default_id: str
    contract_id: str
    cure_date: date
    observation_months: int


@dataclass(frozen=True, slots=True)
class WriteOffRecord:
    writeoff_id: str
    default_id: str
    contract_id: str
    writeoff_date: date
    amount: Decimal
    policy_version: str


@dataclass(frozen=True, slots=True)
class CreditEventHistory:
    defaults: tuple[DefaultEventRecord, ...]
    collections: tuple[CollectionEventRecord, ...]
    recoveries: tuple[RecoveryRecord, ...]
    cures: tuple[CureRecord, ...]
    writeoffs: tuple[WriteOffRecord, ...]
    generator_version: str
    seed: int

    def as_tables(self) -> dict[str, list[dict[str, object]]]:
        return {
            "defaults": [asdict(item) for item in self.defaults],
            "collections": [asdict(item) for item in self.collections],
            "recoveries": [asdict(item) for item in self.recoveries],
            "cures": [asdict(item) for item in self.cures],
            "writeoffs": [asdict(item) for item in self.writeoffs],
        }


def _event_rng(seed: int, contract_id: str) -> Random:
    digest = sha256(f"{seed}:events:{contract_id}".encode()).digest()
    return Random(int.from_bytes(digest[:8], "big"))


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


def _first_default_candidate(
    rows: list[MonthlySnapshotRecord],
    rng: Random,
    *,
    forced_trigger: str | None,
    forced_months_on_book: int,
) -> tuple[MonthlySnapshotRecord, str] | None:
    for row in rows:
        if row.balance <= 0 or row.months_on_book < 6:
            continue
        if row.days_past_due >= 90:
            return row, "90_days_past_due"
        if forced_trigger is not None and row.months_on_book >= forced_months_on_book:
            return row, forced_trigger
        monthly_hazard = 0.0005 + float(row.behavior_score**2) * 0.012
        if rng.random() < monthly_hazard:
            return row, "stochastic_hazard"
    return None


def generate_credit_events(
    population: SyntheticPortfolio, history: LongitudinalPortfolio
) -> CreditEventHistory:
    defaults: list[DefaultEventRecord] = []
    collections: list[CollectionEventRecord] = []
    recoveries: list[RecoveryRecord] = []
    cures: list[CureRecord] = []
    writeoffs: list[WriteOffRecord] = []
    initial_default_count = 0
    collateral_by_contract = {item.contract_id: item for item in population.collateral}

    for contract in population.contracts:
        rows = sorted(
            (item for item in history.snapshots if item.contract_id == contract.contract_id),
            key=lambda item: item.reference_date,
        )
        rng = _event_rng(population.seed, contract.contract_id)
        force_collateral_shock = (
            contract.contract_id in collateral_by_contract
            and int(contract.contract_id[-4:]) % 17 == 0
        )
        force_ccf_shock = (
            contract.facility_type in {"revolving", "commitment", "financial_guarantee"}
            and int(contract.contract_id[-4:]) % 19 == 0
        )
        forced_trigger = None
        forced_months_on_book = 36
        if force_collateral_shock:
            forced_trigger = "idiosyncratic_collateral_shock"
        elif force_ccf_shock:
            forced_trigger = "liquidity_drawdown_shock"
            forced_months_on_book = 6
        candidate = _first_default_candidate(
            rows,
            rng,
            forced_trigger=forced_trigger,
            forced_months_on_book=forced_months_on_book,
        )
        if candidate is None:
            continue
        snapshot, trigger = candidate
        default = DefaultEventRecord(
            f"DEF-{len(defaults) + 1:07d}",
            contract.contract_id,
            _add_months(snapshot.reference_date, 1),
            snapshot.balance,
            trigger,
            False,
        )
        defaults.append(default)
        initial_default_count += 1

        for month, action in ((1, "contact"), (3, "negotiation"), (6, "legal_or_collateral")):
            collections.append(
                CollectionEventRecord(
                    f"COLL-{len(collections) + 1:08d}",
                    default.default_id,
                    contract.contract_id,
                    _add_months(default.default_date, month),
                    action,
                )
            )

        recovered_net = Decimal("0.00")
        for recovery_month in range(1, 7):
            cash_gross = _money(
                default.exposure_at_default * Decimal(str(rng.uniform(0.005, 0.02)))
            )
            cash_cost = _money(cash_gross * Decimal("0.08"))
            cash_net = _money(cash_gross - cash_cost)
            recoveries.append(
                RecoveryRecord(
                    f"REC-{len(recoveries) + 1:08d}",
                    default.default_id,
                    contract.contract_id,
                    _add_months(default.default_date, recovery_month),
                    "cash_collection",
                    cash_gross,
                    cash_cost,
                    "operational",
                    cash_net,
                    False,
                )
            )
            recovered_net += cash_net

        collateral = collateral_by_contract.get(contract.contract_id)
        if collateral is not None:
            available = max(Decimal("0"), default.exposure_at_default - recovered_net)
            gross = min(
                available,
                _money(collateral.appraised_value * collateral.enforceable_share * Decimal("0.65")),
            )
            cost = _money(gross * Decimal("0.12"))
            net = _money(gross - cost)
            recoveries.append(
                RecoveryRecord(
                    f"REC-{len(recoveries) + 1:08d}",
                    default.default_id,
                    contract.contract_id,
                    _add_months(default.default_date, 8),
                    "collateral_execution",
                    gross,
                    cost,
                    "judicial_and_operational",
                    net,
                    False,
                )
            )
            recovered_net += net

        force_cure_and_redefault = initial_default_count == 1
        cured = force_cure_and_redefault or rng.random() < 0.30
        if cured:
            cure_date = _add_months(default.default_date, 6)
            cures.append(
                CureRecord(
                    f"CURE-{len(cures) + 1:07d}",
                    default.default_id,
                    contract.contract_id,
                    cure_date,
                    6,
                )
            )
            if force_cure_and_redefault or rng.random() < 0.50:
                defaults.append(
                    DefaultEventRecord(
                        f"DEF-{len(defaults) + 1:07d}",
                        contract.contract_id,
                        _add_months(cure_date, 3),
                        max(Decimal("0.00"), _money(default.exposure_at_default - recovered_net)),
                        "redefault_after_cure",
                        True,
                    )
                )
                cured = False

        if not cured:
            writeoff_amount = max(
                Decimal("0.00"), _money(default.exposure_at_default - recovered_net)
            )
            writeoff = WriteOffRecord(
                f"WO-{len(writeoffs) + 1:07d}",
                default.default_id,
                contract.contract_id,
                _add_months(default.default_date, 12),
                writeoff_amount,
                contract.policy_version,
            )
            writeoffs.append(writeoff)
            post_gross = _money(writeoff_amount * Decimal(str(rng.uniform(0.01, 0.05))))
            post_cost = _money(post_gross * Decimal("0.10"))
            recoveries.append(
                RecoveryRecord(
                    f"REC-{len(recoveries) + 1:08d}",
                    default.default_id,
                    contract.contract_id,
                    _add_months(writeoff.writeoff_date, 3),
                    "post_writeoff_collection",
                    post_gross,
                    post_cost,
                    "operational",
                    _money(post_gross - post_cost),
                    True,
                )
            )

    return CreditEventHistory(
        tuple(defaults),
        tuple(collections),
        tuple(recoveries),
        tuple(cures),
        tuple(writeoffs),
        "0.1.0",
        population.seed,
    )
