"""Point-in-time modeling datasets derived from synthetic observable history."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from .events import CreditEventHistory, DefaultEventRecord
from .longitudinal import LongitudinalPortfolio, MonthlySnapshotRecord
from .macroeconomics import MacroeconomicBundle, MacroObservation
from .population import RATE, SyntheticPortfolio, _add_months

RATING_ORDER = ("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "D", "DEFAULT")
MAX_LABELED_OBSERVATION_DATE = date(2024, 12, 1)
MAX_OBSERVATION_DATE = date(2025, 12, 1)


@dataclass(frozen=True, slots=True)
class PDModelingRow:
    observation_date: date
    contract_id: str
    client_id: str
    origination_cohort: str
    product_code: str
    balance: Decimal
    credit_limit: Decimal
    utilization: Decimal
    days_past_due: int
    behavior_score: Decimal
    rating: str
    gdp_growth: Decimal
    inflation: Decimal
    policy_rate: Decimal
    unemployment: Decimal
    household_debt: Decimal
    target_default_12m: int | None
    target_hazard_1m: int | None
    split: str


@dataclass(frozen=True, slots=True)
class LGDModelingRow:
    default_id: str
    default_date: date
    contract_id: str
    product_code: str
    exposure_at_default: Decimal
    collateral_coverage_at_origination: Decimal
    recovery_net_total: Decimal
    target_realized_lgd_undiscounted: Decimal
    split: str


@dataclass(frozen=True, slots=True)
class EADModelingRow:
    default_id: str
    observation_date: date
    default_date: date
    contract_id: str
    product_code: str
    facility_type: str
    observed_balance: Decimal
    observed_limit: Decimal
    observed_utilization: Decimal
    target_exposure_at_default: Decimal
    target_ccf: Decimal | None
    split: str


@dataclass(frozen=True, slots=True)
class SICRModelingRow:
    observation_date: date
    contract_id: str
    origination_rating: str
    current_rating: str
    days_past_due: int
    target_sicr_12m: int | None
    split: str


@dataclass(frozen=True, slots=True)
class ModelingDatasets:
    pd: tuple[PDModelingRow, ...]
    lgd: tuple[LGDModelingRow, ...]
    ead: tuple[EADModelingRow, ...]
    sicr: tuple[SICRModelingRow, ...]
    version: str

    def as_tables(self) -> dict[str, list[dict[str, object]]]:
        return {
            "pd_modeling": [asdict(item) for item in self.pd],
            "lgd_modeling": [asdict(item) for item in self.lgd],
            "ead_modeling": [asdict(item) for item in self.ead],
            "sicr_modeling": [asdict(item) for item in self.sicr],
        }


def _split(reference_date: date) -> str:
    if reference_date <= date(2019, 12, 1):
        return "train"
    if reference_date <= date(2020, 12, 1):
        return "validation"
    if reference_date <= date(2021, 12, 1):
        return "calibration"
    if reference_date <= date(2023, 12, 1):
        return "oot"
    return "backtesting"


def _pd_split(reference_date: date) -> str | None:
    """Return horizon-purged development splits; ``None`` is an embargo row."""
    if reference_date <= date(2018, 12, 1):
        return "train"
    if date(2020, 1, 1) <= reference_date <= date(2020, 12, 1):
        return "validation"
    if date(2022, 1, 1) <= reference_date <= date(2022, 12, 1):
        return "calibration"
    if date(2024, 1, 1) <= reference_date <= date(2024, 12, 1):
        return "oot"
    if date(2025, 1, 1) <= reference_date <= date(2025, 12, 1):
        return "backtesting"
    return None


def _between(event_date: date, start: date, months: int) -> bool:
    return start < event_date <= _add_months(start, months)


def _macro_map(bundle: MacroeconomicBundle) -> dict[date, MacroObservation]:
    return {item.reference_date: item for item in bundle.observed}


def _initial_defaults(events: CreditEventHistory) -> tuple[DefaultEventRecord, ...]:
    return tuple(item for item in events.defaults if not item.is_redefault)


def build_modeling_datasets(
    population: SyntheticPortfolio,
    history: LongitudinalPortfolio,
    events: CreditEventHistory,
    macro: MacroeconomicBundle,
) -> ModelingDatasets:
    contracts = {item.contract_id: item for item in population.contracts}
    collateral = {item.contract_id: item for item in population.collateral}
    initial_defaults = _initial_defaults(events)
    defaults_by_contract: dict[str, list[DefaultEventRecord]] = {}
    for default in events.defaults:
        defaults_by_contract.setdefault(default.contract_id, []).append(default)

    snapshots_by_contract: dict[str, list[MonthlySnapshotRecord]] = {}
    for snapshot in history.snapshots:
        snapshots_by_contract.setdefault(snapshot.contract_id, []).append(snapshot)
    for rows in snapshots_by_contract.values():
        rows.sort(key=lambda item: item.reference_date)

    macro_by_date = _macro_map(macro)
    pd_rows: list[PDModelingRow] = []
    sicr_rows: list[SICRModelingRow] = []
    rating_rank = {rating: index for index, rating in enumerate(RATING_ORDER)}
    for contract_id, rows in snapshots_by_contract.items():
        contract = contracts[contract_id]
        if contract.acquired_credit_impaired:
            continue
        contract_defaults = defaults_by_contract.get(contract_id, [])
        first_default_date = min(
            (item.default_date for item in contract_defaults), default=date.max
        )
        origination_rating = rows[0].rating
        for index, snapshot in enumerate(rows):
            if snapshot.reference_date > MAX_OBSERVATION_DATE:
                continue
            if snapshot.reference_date >= first_default_date:
                continue
            split = _pd_split(snapshot.reference_date)
            if split is None:
                continue
            macro_row = macro_by_date[snapshot.reference_date]
            labels_complete = snapshot.reference_date <= MAX_LABELED_OBSERVATION_DATE
            target_default = (
                int(
                    any(
                        _between(item.default_date, snapshot.reference_date, 12)
                        for item in contract_defaults
                    )
                )
                if labels_complete
                else None
            )
            target_hazard = (
                int(
                    any(
                        _between(item.default_date, snapshot.reference_date, 1)
                        for item in contract_defaults
                    )
                )
                if labels_complete
                else None
            )
            pd_rows.append(
                PDModelingRow(
                    snapshot.reference_date,
                    contract_id,
                    snapshot.client_id,
                    snapshot.origination_cohort,
                    contract.product_code,
                    snapshot.balance,
                    snapshot.credit_limit,
                    snapshot.utilization,
                    snapshot.days_past_due,
                    snapshot.behavior_score,
                    snapshot.rating,
                    macro_row.gdp_growth,
                    macro_row.inflation,
                    macro_row.policy_rate,
                    macro_row.unemployment,
                    macro_row.household_debt,
                    target_default,
                    target_hazard,
                    split,
                )
            )
            future = [
                item
                for item in rows[index + 1 :]
                if item.reference_date <= _add_months(snapshot.reference_date, 12)
            ]
            future_deterioration = max(
                (rating_rank[item.rating] - rating_rank[origination_rating] for item in future),
                default=0,
            )
            sicr_target = (
                int(
                    bool(target_default)
                    or any(item.days_past_due >= 31 for item in future)
                    or future_deterioration >= 2
                )
                if labels_complete
                else None
            )
            sicr_rows.append(
                SICRModelingRow(
                    snapshot.reference_date,
                    contract_id,
                    origination_rating,
                    snapshot.rating,
                    snapshot.days_past_due,
                    sicr_target,
                    split,
                )
            )

    lgd_rows: list[LGDModelingRow] = []
    ead_rows: list[EADModelingRow] = []
    for default in initial_defaults:
        contract = contracts[default.contract_id]
        recovery_total = sum(
            (
                item.net_amount
                for item in events.recoveries
                if item.default_id == default.default_id
            ),
            Decimal("0"),
        )
        realized_lgd = max(
            Decimal("0"),
            (Decimal("1") - recovery_total / default.exposure_at_default).quantize(
                RATE, rounding=ROUND_HALF_EVEN
            ),
        )
        collateral_item = collateral.get(default.contract_id)
        coverage = Decimal("0")
        if collateral_item is not None:
            coverage = min(
                Decimal("1"),
                (
                    collateral_item.appraised_value
                    * collateral_item.enforceable_share
                    / default.exposure_at_default
                ).quantize(RATE, rounding=ROUND_HALF_EVEN),
            )
        lgd_rows.append(
            LGDModelingRow(
                default.default_id,
                default.default_date,
                default.contract_id,
                contract.product_code,
                default.exposure_at_default,
                coverage,
                recovery_total,
                realized_lgd,
                _split(default.default_date),
            )
        )

        prior = [
            item
            for item in snapshots_by_contract[default.contract_id]
            if item.reference_date < default.default_date
        ]
        target_observation = _add_months(default.default_date, -12)
        observation = min(
            prior,
            key=lambda item: abs(
                (item.reference_date.year - target_observation.year) * 12
                + item.reference_date.month
                - target_observation.month
            ),
        )
        undrawn = observation.credit_limit - observation.balance
        target_ccf = None
        if contract.facility_type in {"revolving", "commitment", "financial_guarantee"}:
            drawn_after_observation = max(
                Decimal("0"), default.exposure_at_default - observation.balance
            )
            target_ccf = (
                min(Decimal("1"), drawn_after_observation / undrawn).quantize(
                    RATE, rounding=ROUND_HALF_EVEN
                )
                if undrawn > 0
                else Decimal("0")
            )
        ead_rows.append(
            EADModelingRow(
                default.default_id,
                observation.reference_date,
                default.default_date,
                default.contract_id,
                contract.product_code,
                contract.facility_type,
                observation.balance,
                observation.credit_limit,
                observation.utilization,
                default.exposure_at_default,
                target_ccf,
                _split(observation.reference_date),
            )
        )

    return ModelingDatasets(
        tuple(pd_rows), tuple(lgd_rows), tuple(ead_rows), tuple(sicr_rows), "0.2.0"
    )
