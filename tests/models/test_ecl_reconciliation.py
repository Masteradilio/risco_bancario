from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.validation.reconciliation import (
    ContractECLAdjustment,
    ECLLedgerEntry,
    create_ecl_execution_ledger,
)


def _entries() -> tuple[ECLLedgerEntry, ...]:
    period = date(2026, 1, 31)
    return (
        ECLLedgerEntry("CTR-1", "CLI-1", "mortgage", period, "base", "0.70", "10"),
        ECLLedgerEntry("CTR-1", "CLI-1", "mortgage", period, "downside", "0.30", "20"),
        ECLLedgerEntry("CTR-2", "CLI-2", "mortgage", period, "base", "0.70", "30"),
        ECLLedgerEntry("CTR-2", "CLI-2", "mortgage", period, "downside", "0.30", "50"),
    )


def _adjustments() -> tuple[ContractECLAdjustment, ...]:
    return (
        ContractECLAdjustment("CTR-1", "13", "2", "20", "20"),
        ContractECLAdjustment("CTR-2", "36", "-1", "0", "35"),
    )


def _ledger(
    entries: tuple[ECLLedgerEntry, ...] | None = None,
    adjustments: tuple[ContractECLAdjustment, ...] | None = None,
    previous_hash: str | None = None,
):
    return create_ecl_execution_ledger(
        execution_id="RUN-001",
        reference_date=date(2025, 12, 31),
        created_at=datetime(2026, 1, 2, 12, tzinfo=UTC),
        entries=entries or _entries(),
        adjustments=adjustments or _adjustments(),
        model_version="ecl-0.1.0",
        configuration_version="2026.07.1",
        configuration_hash="a" * 64,
        previous_ledger_hash=previous_hash,
    )


def test_ledger_reconciles_period_scenario_contract_and_portfolio() -> None:
    ledger = _ledger()
    report = ledger.reconciliation
    assert report.reconciled
    assert report.period_totals[0].weighted_ecl == Decimal("49.00")
    scenarios = {item.scenario_id: item for item in report.scenario_totals}
    assert scenarios["base"].scenario_ecl == Decimal("40.00")
    assert scenarios["base"].weighted_ecl == Decimal("28.00")
    assert scenarios["downside"].scenario_ecl == Decimal("70.00")
    assert scenarios["downside"].weighted_ecl == Decimal("21.00")
    assert report.portfolio_total.economic_ecl == Decimal("49.00")


def test_ledger_reconciles_client_product_overlay_floor_and_final() -> None:
    report = _ledger().reconciliation
    assert len(report.client_totals) == 2
    assert len(report.product_totals) == 1
    mortgage = report.product_totals[0]
    assert mortgage.dimension_key == "mortgage"
    assert mortgage.economic_ecl == Decimal("49.00")
    assert mortgage.management_overlay == Decimal("1.00")
    assert mortgage.regulatory_floor == Decimal("20.00")
    assert mortgage.final_ecl == Decimal("55.00")
    assert report.portfolio_total == replace(mortgage, dimension_key="portfolio")


def test_multi_period_entries_reconcile_to_same_contract_ecl() -> None:
    entries: list[ECLLedgerEntry] = []
    for item in _entries():
        amount = Decimal(str(item.period_ecl)) / 2
        entries.append(replace(item, period_date=date(2026, 1, 31), period_ecl=amount))
        entries.append(replace(item, period_date=date(2026, 2, 28), period_ecl=amount))
    report = _ledger(entries=tuple(entries)).reconciliation
    assert [item.weighted_ecl for item in report.period_totals] == [
        Decimal("24.50"),
        Decimal("24.50"),
    ]
    assert report.portfolio_total.economic_ecl == Decimal("49.00")


def test_contract_adjustment_formula_and_period_reconciliation_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="final ECL"):
        ContractECLAdjustment("CTR", "10", "2", "0", "11")
    bad = (replace(_adjustments()[0], economic_ecl="12", final_ecl="20"), _adjustments()[1])
    with pytest.raises(DomainValidationError, match="does not reconcile"):
        _ledger(adjustments=bad)


def test_invalid_scenario_weights_and_coverage_fail_closed() -> None:
    weights = tuple(
        replace(item, scenario_weight="0.20") if item.scenario_id == "downside" else item
        for item in _entries()
    )
    with pytest.raises(DomainValidationError, match="sum to one"):
        _ledger(entries=weights)
    incomplete = tuple(
        item
        for item in _entries()
        if not (item.contract_id == "CTR-2" and item.scenario_id == "downside")
    )
    with pytest.raises(DomainValidationError, match="every ledger scenario"):
        _ledger(entries=incomplete)


def test_duplicate_entries_and_unstable_metadata_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="must be unique"):
        _ledger(entries=_entries() + (_entries()[0],))
    unstable = list(_entries())
    unstable[1] = replace(unstable[1], client_id="OTHER")
    with pytest.raises(DomainValidationError, match="metadata must be stable"):
        _ledger(entries=tuple(unstable))


def test_ledger_is_frozen_content_addressed_and_chainable() -> None:
    first = _ledger()
    reordered = _ledger(
        entries=tuple(reversed(_entries())), adjustments=tuple(reversed(_adjustments()))
    )
    assert first.ledger_hash == reordered.ledger_hash
    assert len(first.ledger_hash) == 64
    chained = _ledger(previous_hash=first.ledger_hash)
    assert chained.previous_ledger_hash == first.ledger_hash
    assert chained.ledger_hash != first.ledger_hash
    with pytest.raises(FrozenInstanceError):
        first.execution_id = "MUTATED"  # type: ignore[misc]


def test_ledger_requires_aware_timestamp_and_valid_previous_hash() -> None:
    with pytest.raises(TemporalConsistencyError, match="timezone-aware"):
        create_ecl_execution_ledger(
            execution_id="RUN",
            reference_date=date(2025, 12, 31),
            created_at=datetime(2026, 1, 2),
            entries=_entries(),
            adjustments=_adjustments(),
            model_version="v1",
            configuration_version="v1",
            configuration_hash="hash",
        )
    with pytest.raises(DomainValidationError, match="previous ledger hash"):
        _ledger(previous_hash="invalid")
