from datetime import date
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.regulatory.cmn4966 import (
    ProvisionPortfolio,
    apply_provision_floor,
    load_provision_floor_policy,
)


def test_bcb352_floor_policy_is_official_versioned_and_hashable() -> None:
    policy = load_provision_floor_policy(date(2026, 7, 14))
    assert policy.policy_version == "2025.01.1"
    assert policy.effective_from == date(2025, 1, 1)
    assert policy.source_id == "SRC-BCB352"
    assert policy.source_locator.endswith("Anexo I")
    assert len(policy.sha256) == 64
    assert policy.rate_for(ProvisionPortfolio.C1, 0) == Decimal("0.05500000")
    assert policy.rate_for(ProvisionPortfolio.C5, 14) == Decimal("0.97600000")
    assert policy.rate_for(ProvisionPortfolio.C2, 20) == Decimal("0.98000000")
    assert policy.rate_for(ProvisionPortfolio.C1, 21) == Decimal("1.00000000")
    assert policy.rate_for(ProvisionPortfolio.C1, 22) == Decimal("1.00000000")


def test_reference_date_without_supported_policy_fails_closed() -> None:
    with pytest.raises(DomainValidationError, match="unsupported"):
        load_provision_floor_policy(date(2024, 12, 31))


def test_all_official_annex_i_month_bands_are_reproduced() -> None:
    policy = load_provision_floor_policy(date(2026, 7, 14))
    expected = {
        ProvisionPortfolio.C1: tuple(
            Decimal("0.055") + Decimal(month) * Decimal("0.045") for month in range(21)
        )
        + (Decimal("1"),),
        ProvisionPortfolio.C2: tuple(
            Decimal("0.300") + Decimal(month) * Decimal("0.034") for month in range(21)
        )
        + (Decimal("1"),),
        ProvisionPortfolio.C3: tuple(
            Decimal("0.450") + Decimal(month) * Decimal("0.037") for month in range(15)
        )
        + (Decimal("1"),) * 7,
        ProvisionPortfolio.C4: tuple(
            Decimal("0.350") + Decimal(month) * Decimal("0.045") for month in range(15)
        )
        + (Decimal("1"),) * 7,
        ProvisionPortfolio.C5: tuple(
            Decimal("0.500") + Decimal(month) * Decimal("0.034") for month in range(15)
        )
        + (Decimal("1"),) * 7,
    }
    for portfolio, rates in expected.items():
        assert tuple(policy.rate_for(portfolio, month) for month in range(22)) == rates


def test_floor_is_applied_after_and_reported_separately_from_economic_ecl() -> None:
    result = apply_provision_floor(
        reference_date=date(2026, 7, 14),
        portfolio=ProvisionPortfolio.C5,
        gross_carrying_amount="1000.00",
        calculated_ecl="320.00",
        days_past_due=120,
        default_date=date(2026, 7, 1),
    )
    assert result.calculated_ecl == Decimal("320.00")
    assert result.floor_rate == Decimal("0.50000000")
    assert result.regulatory_floor == Decimal("500.00")
    assert result.final_provision == Decimal("500.00")
    assert result.floor_applied
    assert result.months_since_default == 0


def test_economic_ecl_remains_final_when_above_floor() -> None:
    result = apply_provision_floor(
        reference_date=date(2026, 7, 31),
        portfolio=ProvisionPortfolio.C1,
        gross_carrying_amount="1000",
        calculated_ecl="80",
        days_past_due=91,
        default_date=date(2026, 7, 1),
    )
    assert result.regulatory_floor == Decimal("55.00")
    assert result.final_provision == Decimal("80.00")
    assert not result.floor_applied


def test_non_delinquent_asset_has_no_incurred_loss_floor() -> None:
    result = apply_provision_floor(
        reference_date=date(2026, 7, 31),
        portfolio=ProvisionPortfolio.C5,
        gross_carrying_amount="1000",
        calculated_ecl="25",
        days_past_due=90,
        default_date=None,
    )
    assert result.floor_rate == Decimal("0")
    assert result.regulatory_floor == Decimal("0.00")
    assert result.final_provision == Decimal("25.00")


def test_calendar_month_band_and_terminal_cap_are_deterministic() -> None:
    second_band = apply_provision_floor(
        reference_date=date(2026, 8, 1),
        portfolio=ProvisionPortfolio.C2,
        gross_carrying_amount="1000",
        calculated_ecl="0",
        days_past_due=130,
        default_date=date(2026, 7, 31),
    )
    terminal = apply_provision_floor(
        reference_date=date(2028, 6, 30),
        portfolio=ProvisionPortfolio.C1,
        gross_carrying_amount="1000",
        calculated_ecl="0",
        days_past_due=800,
        default_date=date(2026, 7, 1),
    )
    assert second_band.months_since_default == 1
    assert second_band.regulatory_floor == Decimal("334.00")
    assert terminal.regulatory_floor == Decimal("1000.00")


def test_invalid_temporal_and_amount_inputs_fail_closed() -> None:
    common = {
        "reference_date": date(2026, 7, 14),
        "portfolio": ProvisionPortfolio.C1,
        "gross_carrying_amount": "1000",
        "calculated_ecl": "10",
        "days_past_due": 91,
    }
    with pytest.raises(DomainValidationError, match="default_date is required"):
        apply_provision_floor(**common, default_date=None)
    with pytest.raises(TemporalConsistencyError, match="cannot be after"):
        apply_provision_floor(**common, default_date=date(2026, 7, 15))
    with pytest.raises(DomainValidationError, match="cannot exceed"):
        apply_provision_floor(
            **{**common, "calculated_ecl": "1000.01"}, default_date=date(2026, 7, 1)
        )
