from datetime import date
from decimal import Decimal

import pytest

from src.data.synthetic import PopulationConfig, generate_population
from src.data.synthetic.population import ContractRecord, _annuity_schedule
from src.domain.exceptions import DomainValidationError


def portfolio():
    return generate_population(PopulationConfig(seed=42, clients=16, contracts_per_client=2))


def test_generation_is_reproducible_and_seed_sensitive() -> None:
    config = PopulationConfig(seed=42, clients=16, contracts_per_client=2)
    assert generate_population(config) == generate_population(config)
    assert generate_population(config) != generate_population(
        PopulationConfig(seed=43, clients=16, contracts_per_client=2)
    )


def test_population_contains_pf_pj_groups_and_valid_relationships() -> None:
    result = portfolio()
    assert {item.client_type for item in result.clients} == {"PF", "PJ"}
    assert result.groups
    counterparty_ids = {item.counterparty_id for item in result.counterparties}
    group_ids = {item.economic_group_id for item in result.groups}
    assert all(item.counterparty_id in counterparty_ids for item in result.clients)
    assert all(
        item.economic_group_id in group_ids
        for item in result.counterparties
        if item.economic_group_id
    )


def test_catalog_covers_facilities_commitments_guarantees_and_poci() -> None:
    result = portfolio()
    facility_types = {item.facility_type for item in result.contracts}
    assert facility_types == {"amortized", "revolving", "commitment", "financial_guarantee"}
    assert any(item.acquired_credit_impaired for item in result.contracts)
    assert all(
        item.initial_drawn_amount == 0
        for item in result.contracts
        if item.facility_type in {"commitment", "financial_guarantee"}
    )


def test_amortized_schedules_reconcile_and_end_at_zero() -> None:
    result = portfolio()
    amortized = [item for item in result.contracts if item.facility_type == "amortized"]
    for contract in amortized:
        rows = [item for item in result.schedules if item.contract_id == contract.contract_id]
        assert rows
        assert sum((item.principal for item in rows), Decimal("0")) == contract.initial_drawn_amount
        assert rows[-1].closing_balance == Decimal("0.00")
        assert rows[-1].due_date == contract.maturity_date


def test_collateral_is_linked_and_valued_above_zero() -> None:
    result = portfolio()
    contract_ids = {item.contract_id for item in result.contracts}
    assert {item.collateral_type for item in result.collateral} == {"vehicle", "real_estate"}
    assert all(
        item.contract_id in contract_ids and item.appraised_value > 0 for item in result.collateral
    )


def test_public_tables_have_no_latent_fields() -> None:
    tables = portfolio().as_tables()
    assert all(
        not key.startswith("_latent") for rows in tables.values() for row in rows for key in row
    )


def test_invalid_population_config_fails_fast() -> None:
    with pytest.raises(DomainValidationError, match="at least 7"):
        PopulationConfig(clients=6)
    with pytest.raises(DomainValidationError, match="positive"):
        PopulationConfig(contracts_per_client=0)
    with pytest.raises(DomainValidationError, match="cannot precede"):
        PopulationConfig(start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))


def test_zero_rate_annuity_schedule_splits_principal_without_interest() -> None:
    contract = ContractRecord(
        "CT-ZERO",
        "CL-1",
        "CP-1",
        "personal_loan",
        "amortized",
        date(2026, 1, 1),
        date(2026, 3, 1),
        Decimal("0"),
        Decimal("90"),
        Decimal("90"),
        Decimal("90"),
        "BRL",
        False,
        "test",
    )

    schedule = _annuity_schedule(contract, 3)

    assert [row.interest for row in schedule] == [Decimal("0.00")] * 3
    assert [row.principal for row in schedule] == [Decimal("30.00")] * 3
