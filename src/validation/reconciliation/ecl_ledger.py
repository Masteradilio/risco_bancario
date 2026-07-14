"""Immutable ECL execution ledger and multi-level reconciliation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from hashlib import sha256

from ...domain.conventions import DecimalInput, aware_utc, decimal_from, money, non_empty, rate
from ...domain.exceptions import DomainValidationError

MONEY_QUANTUM = Decimal("0.01")
CONTRIBUTION_QUANTUM = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class ECLLedgerEntry:
    contract_id: str
    client_id: str
    product_code: str
    period_date: date
    scenario_id: str
    scenario_weight: DecimalInput
    period_ecl: DecimalInput

    def __post_init__(self) -> None:
        for field in ("contract_id", "client_id", "product_code", "scenario_id"):
            object.__setattr__(self, field, non_empty(getattr(self, field), field=field))
        object.__setattr__(self, "scenario_weight", rate(self.scenario_weight, field="weight"))
        object.__setattr__(self, "period_ecl", money(self.period_ecl, field="period_ecl"))

    @property
    def weighted_period_ecl(self) -> Decimal:
        return (
            decimal_from(self.period_ecl, field="period_ecl")
            * decimal_from(self.scenario_weight, field="scenario_weight")
        ).quantize(CONTRIBUTION_QUANTUM, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True, slots=True)
class ContractECLAdjustment:
    contract_id: str
    economic_ecl: DecimalInput
    management_overlay: DecimalInput
    regulatory_floor: DecimalInput
    final_ecl: DecimalInput

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", non_empty(self.contract_id, field="contract_id"))
        economic = money(self.economic_ecl, field="economic_ecl")
        overlay = money(self.management_overlay, field="management_overlay", allow_negative=True)
        floor = money(self.regulatory_floor, field="regulatory_floor")
        final = money(self.final_ecl, field="final_ecl")
        expected = max(economic + overlay, floor, Decimal("0")).quantize(MONEY_QUANTUM)
        if final != expected:
            raise DomainValidationError(
                "final ECL must equal max(economic ECL plus overlay, floor)"
            )
        object.__setattr__(self, "economic_ecl", economic)
        object.__setattr__(self, "management_overlay", overlay)
        object.__setattr__(self, "regulatory_floor", floor)
        object.__setattr__(self, "final_ecl", final)


@dataclass(frozen=True, slots=True)
class PeriodReconciliation:
    period_date: date
    weighted_ecl: Decimal


@dataclass(frozen=True, slots=True)
class ScenarioReconciliation:
    scenario_id: str
    weight: Decimal
    scenario_ecl: Decimal
    weighted_ecl: Decimal


@dataclass(frozen=True, slots=True)
class DimensionReconciliation:
    dimension_key: str
    economic_ecl: Decimal
    management_overlay: Decimal
    regulatory_floor: Decimal
    final_ecl: Decimal


@dataclass(frozen=True, slots=True)
class ECLReconciliationReport:
    period_totals: tuple[PeriodReconciliation, ...]
    scenario_totals: tuple[ScenarioReconciliation, ...]
    contract_totals: tuple[DimensionReconciliation, ...]
    client_totals: tuple[DimensionReconciliation, ...]
    product_totals: tuple[DimensionReconciliation, ...]
    portfolio_total: DimensionReconciliation
    reconciled: bool


@dataclass(frozen=True, slots=True)
class ECLExecutionLedger:
    execution_id: str
    reference_date: date
    created_at: datetime
    entries: tuple[ECLLedgerEntry, ...]
    adjustments: tuple[ContractECLAdjustment, ...]
    reconciliation: ECLReconciliationReport
    model_version: str
    configuration_version: str
    configuration_hash: str
    previous_ledger_hash: str | None
    ledger_hash: str


def _money_sum(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, Decimal("0")).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)


def _dimension_total(
    key: str, adjustments: tuple[ContractECLAdjustment, ...]
) -> DimensionReconciliation:
    return DimensionReconciliation(
        key,
        _money_sum(
            tuple(decimal_from(item.economic_ecl, field="economic_ecl") for item in adjustments)
        ),
        _money_sum(
            tuple(decimal_from(item.management_overlay, field="overlay") for item in adjustments)
        ),
        _money_sum(
            tuple(decimal_from(item.regulatory_floor, field="floor") for item in adjustments)
        ),
        _money_sum(tuple(decimal_from(item.final_ecl, field="final_ecl") for item in adjustments)),
    )


def _build_reconciliation(
    entries: tuple[ECLLedgerEntry, ...], adjustments: tuple[ContractECLAdjustment, ...]
) -> ECLReconciliationReport:
    period_dates = sorted({item.period_date for item in entries})
    period_totals = tuple(
        PeriodReconciliation(
            period_date,
            _money_sum(
                tuple(
                    item.weighted_period_ecl for item in entries if item.period_date == period_date
                )
            ),
        )
        for period_date in period_dates
    )
    scenario_ids = sorted({item.scenario_id for item in entries})
    scenario_totals: list[ScenarioReconciliation] = []
    for scenario_id in scenario_ids:
        scenario_entries = tuple(item for item in entries if item.scenario_id == scenario_id)
        weight = decimal_from(scenario_entries[0].scenario_weight, field="scenario_weight")
        scenario_ecl = _money_sum(
            tuple(decimal_from(item.period_ecl, field="period_ecl") for item in scenario_entries)
        )
        weighted_ecl = _money_sum(tuple(item.weighted_period_ecl for item in scenario_entries))
        scenario_totals.append(
            ScenarioReconciliation(scenario_id, weight, scenario_ecl, weighted_ecl)
        )
    metadata = {
        contract_id: next(item for item in entries if item.contract_id == contract_id)
        for contract_id in {item.contract_id for item in entries}
    }
    adjustment_map = {item.contract_id: item for item in adjustments}
    contract_totals = tuple(
        _dimension_total(contract_id, (adjustment_map[contract_id],))
        for contract_id in sorted(adjustment_map)
    )

    def aggregate_by(attribute: str) -> tuple[DimensionReconciliation, ...]:
        keys = sorted({str(getattr(item, attribute)) for item in metadata.values()})
        return tuple(
            _dimension_total(
                key,
                tuple(
                    adjustment_map[contract_id]
                    for contract_id, item in metadata.items()
                    if str(getattr(item, attribute)) == key
                ),
            )
            for key in keys
        )

    client_totals = aggregate_by("client_id")
    product_totals = aggregate_by("product_code")
    portfolio = _dimension_total("portfolio", adjustments)
    scenario_weighted_total = _money_sum(tuple(item.weighted_ecl for item in scenario_totals))
    period_weighted_total = _money_sum(tuple(item.weighted_ecl for item in period_totals))
    reconciled = (
        scenario_weighted_total == portfolio.economic_ecl
        and period_weighted_total == portfolio.economic_ecl
        and _money_sum(tuple(item.economic_ecl for item in contract_totals))
        == portfolio.economic_ecl
        and _money_sum(tuple(item.final_ecl for item in contract_totals)) == portfolio.final_ecl
    )
    return ECLReconciliationReport(
        period_totals,
        tuple(scenario_totals),
        contract_totals,
        client_totals,
        product_totals,
        portfolio,
        reconciled,
    )


def create_ecl_execution_ledger(
    *,
    execution_id: str,
    reference_date: date,
    created_at: datetime,
    entries: tuple[ECLLedgerEntry, ...],
    adjustments: tuple[ContractECLAdjustment, ...],
    model_version: str,
    configuration_version: str,
    configuration_hash: str,
    previous_ledger_hash: str | None = None,
) -> ECLExecutionLedger:
    normalized_execution_id = non_empty(execution_id, field="execution_id")
    normalized_created_at = aware_utc(created_at, field="created_at")
    for value, field in (
        (model_version, "model_version"),
        (configuration_version, "configuration_version"),
        (configuration_hash, "configuration_hash"),
    ):
        non_empty(value, field=field)
    if not entries or not adjustments:
        raise DomainValidationError("ECL ledger requires entries and adjustments")
    if any(item.period_date <= reference_date for item in entries):
        raise DomainValidationError("ECL ledger periods must follow reference date")
    if previous_ledger_hash is not None and (
        len(previous_ledger_hash) != 64
        or any(character not in "0123456789abcdef" for character in previous_ledger_hash)
    ):
        raise DomainValidationError("previous ledger hash must be SHA-256")
    sorted_entries = tuple(
        sorted(entries, key=lambda item: (item.contract_id, item.scenario_id, item.period_date))
    )
    keys = [(item.contract_id, item.scenario_id, item.period_date) for item in sorted_entries]
    if len(keys) != len(set(keys)):
        raise DomainValidationError("ECL ledger entries must be unique")
    scenario_weights: dict[str, Decimal] = {}
    for item in sorted_entries:
        weight = decimal_from(item.scenario_weight, field="scenario_weight")
        if item.scenario_id in scenario_weights and scenario_weights[item.scenario_id] != weight:
            raise DomainValidationError("scenario weight must be consistent across ledger")
        scenario_weights[item.scenario_id] = weight
    if sum(scenario_weights.values(), Decimal("0")) != Decimal("1"):
        raise DomainValidationError("ledger scenario weights must sum to one")
    scenario_ids = set(scenario_weights)
    for contract_id in {item.contract_id for item in sorted_entries}:
        contract_entries = tuple(item for item in sorted_entries if item.contract_id == contract_id)
        if {item.scenario_id for item in contract_entries} != scenario_ids:
            raise DomainValidationError("each contract must cover every ledger scenario")
        if len({(item.client_id, item.product_code) for item in contract_entries}) != 1:
            raise DomainValidationError("contract metadata must be stable across ledger entries")
    sorted_adjustments = tuple(sorted(adjustments, key=lambda item: item.contract_id))
    adjustment_ids = [item.contract_id for item in sorted_adjustments]
    contract_ids = {item.contract_id for item in sorted_entries}
    if set(adjustment_ids) != contract_ids or len(adjustment_ids) != len(set(adjustment_ids)):
        raise DomainValidationError("ledger requires one adjustment for every contract")
    for adjustment in sorted_adjustments:
        measured = _money_sum(
            tuple(
                item.weighted_period_ecl
                for item in sorted_entries
                if item.contract_id == adjustment.contract_id
            )
        )
        if measured != adjustment.economic_ecl:
            raise DomainValidationError("contract economic ECL does not reconcile to periods")
    reconciliation = _build_reconciliation(sorted_entries, sorted_adjustments)
    if not reconciliation.reconciled:
        raise DomainValidationError("ECL execution failed multi-level reconciliation")
    payload = {
        "execution_id": normalized_execution_id,
        "reference_date": reference_date,
        "created_at": normalized_created_at,
        "entries": [asdict(item) for item in sorted_entries],
        "adjustments": [asdict(item) for item in sorted_adjustments],
        "reconciliation": asdict(reconciliation),
        "model_version": model_version,
        "configuration_version": configuration_version,
        "configuration_hash": configuration_hash,
        "previous_ledger_hash": previous_ledger_hash,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ledger_hash = sha256(encoded).hexdigest()
    return ECLExecutionLedger(
        normalized_execution_id,
        reference_date,
        normalized_created_at,
        sorted_entries,
        sorted_adjustments,
        reconciliation,
        model_version,
        configuration_version,
        configuration_hash,
        previous_ledger_hash,
        ledger_hash,
    )
