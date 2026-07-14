"""Tests for framework-independent domain types and invariants."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.domain.cashflows import CashFlow, CashFlowType
from src.domain.contracts import Contract, Guarantee, GuaranteeType
from src.domain.counterparties import Client, Counterparty, PartyType
from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.domain.scenarios import MacroVariable, Scenario, ScenarioKind
from src.domain.staging import RiskSnapshot, Stage
from src.ecl.calculation import ECLResult, ScenarioECL


REFERENCE_DATE = date(2026, 6, 30)
UTC_NOW = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)


def test_counterparty_and_client_are_immutable_and_temporally_valid() -> None:
    counterparty = Counterparty("CP-1", PartyType.INDIVIDUAL, date(2020, 1, 1))
    client = Client("CL-1", counterparty.counterparty_id, date(2020, 1, 2), REFERENCE_DATE)
    assert client.counterparty_id == "CP-1"
    with pytest.raises(AttributeError):
        client.client_id = "changed"  # type: ignore[misc]
    with pytest.raises(TemporalConsistencyError):
        Client("CL-2", "CP-2", REFERENCE_DATE, date(2026, 1, 1))


def test_contract_uses_decimal_money_and_half_even_rounding() -> None:
    contract = Contract(
        "CT-1", "CL-1", "CP-1", "LOAN", date(2026, 1, 1), date(2027, 1, 1),
        Decimal("1000.125"), effective_interest_rate="0.123456789",
    )
    assert contract.original_amount == Decimal("1000.12")
    assert contract.effective_interest_rate == Decimal("0.12345679")
    with pytest.raises(DomainValidationError, match="binary floats"):
        Contract("CT-2", "CL-1", "CP-1", "LOAN", date(2026, 1, 1), date(2027, 1, 1), 10.5)


def test_contract_rejects_invalid_timeline_and_currency() -> None:
    with pytest.raises(TemporalConsistencyError):
        Contract("CT-1", "CL-1", "CP-1", "LOAN", date(2027, 1, 1), date(2026, 1, 1), "100")
    with pytest.raises(DomainValidationError, match="BRL"):
        Contract("CT-1", "CL-1", "CP-1", "LOAN", date(2026, 1, 1), date(2027, 1, 1), "100", currency="USD")


def test_guarantee_and_cash_flow_normalize_values() -> None:
    guarantee = Guarantee("G-1", "CT-1", GuaranteeType.REAL_ESTATE, REFERENCE_DATE, "250000.999", "0.8")
    recovery_cost = CashFlow("CT-1", REFERENCE_DATE, "-120.125", CashFlowType.RECOVERY_COST)
    assert guarantee.value == Decimal("250001.00")
    assert guarantee.enforceable_share == Decimal("0.80000000")
    assert recovery_cost.amount == Decimal("-120.12")


def test_snapshot_requires_aware_timestamp_and_coherent_pd() -> None:
    snapshot = RiskSnapshot("SN-1", "CT-1", REFERENCE_DATE, UTC_NOW, Stage.STAGE_2, 31, "0.10", "0.30", "staging-v1")
    assert snapshot.observed_at.tzinfo == timezone.utc
    with pytest.raises(TemporalConsistencyError, match="timezone-aware"):
        RiskSnapshot("SN-2", "CT-1", REFERENCE_DATE, datetime(2026, 7, 1), Stage.STAGE_1, 0, "0.01", "0.02", "v1")
    with pytest.raises(DomainValidationError, match="pd_lifetime"):
        RiskSnapshot("SN-3", "CT-1", REFERENCE_DATE, UTC_NOW, Stage.STAGE_1, 0, "0.20", "0.10", "v1")


def test_scenario_is_versioned_and_variables_are_unique() -> None:
    scenario = Scenario("SC-BASE", "Base", ScenarioKind.BASE, REFERENCE_DATE, 36, "0.6", "2026.06", (MacroVariable("selic", "0.12"),))
    assert scenario.weight == Decimal("0.60000000")
    with pytest.raises(DomainValidationError, match="unique"):
        Scenario("SC", "Bad", ScenarioKind.BASE, REFERENCE_DATE, 12, "1", "v1", (MacroVariable("gdp", "1"), MacroVariable("gdp", "2")))


def test_ecl_result_separates_components_and_requires_weight_sum() -> None:
    result = ECLResult(
        "R-1", "CT-1", REFERENCE_DATE, UTC_NOW, Stage.STAGE_2,
        "100.125", "5.005", "90", "105.13",
        (ScenarioECL("base", "0.6", "80"), ScenarioECL("down", "0.4", "130")),
        "pd-v1", "cfg-v1", "abc123",
    )
    assert result.economic_ecl == Decimal("100.12")
    assert result.management_overlay == Decimal("5.00")
    assert result.reported_ecl == Decimal("105.13")
    with pytest.raises(DomainValidationError, match="sum to 1"):
        ECLResult(
            "R-2", "CT-1", REFERENCE_DATE, UTC_NOW, Stage.STAGE_1,
            "10", "0", "0", "10", (ScenarioECL("base", "0.8", "10"),),
            "pd-v1", "cfg-v1", "abc123",
        )


def test_calculation_timestamp_cannot_precede_reference_date() -> None:
    with pytest.raises(TemporalConsistencyError):
        ECLResult(
            "R-3", "CT-1", REFERENCE_DATE, UTC_NOW - timedelta(days=2), Stage.STAGE_1,
            "10", "0", "0", "10", (ScenarioECL("base", "1", "10"),),
            "pd-v1", "cfg-v1", "abc123",
        )

