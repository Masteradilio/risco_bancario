from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.models.lgd import (
    LGDWorkoutDataset,
    LGDWorkoutRecord,
    WorkoutCashFlow,
    calculate_realized_lgd,
    calculate_realized_lgd_dataset,
    load_realized_lgd_policy,
)

POLICY_PATH = Path("config/lgd_policy/2026.07.1.json")


def _record(
    *,
    ead: Decimal = Decimal("100"),
    rate: Decimal = Decimal("0"),
    gross: Decimal = Decimal("60"),
    cost: Decimal = Decimal("10"),
    recovery_date: date = date(2026, 1, 1),
    cure_date: date | None = None,
    censored: bool = False,
) -> LGDWorkoutRecord:
    default_date = date(2026, 1, 1)
    cashflow = WorkoutCashFlow(
        recovery_date,
        "collection",
        gross,
        cost,
        gross - cost,
        False,
    )
    return LGDWorkoutRecord(
        "DEF-001",
        "CTR-001",
        default_date,
        "2026-Q1",
        "personal_loan",
        ead,
        rate,
        24,
        date(2028, 1, 1),
        date(2028, 1, 1),
        censored,
        False,
        "cured" if cure_date else "open_complete",
        cure_date,
        None,
        Decimal("0"),
        None,
        Decimal("0"),
        Decimal("0"),
        gross,
        cost,
        gross - cost,
        (cashflow,),
    )


def test_calculates_ead_costs_and_realized_loss_lgd() -> None:
    result = calculate_realized_lgd(_record(), load_realized_lgd_policy(POLICY_PATH))

    assert result.exposure_at_default == Decimal("100")
    assert result.discounted_gross_recoveries == Decimal("60.00000000")
    assert result.discounted_recovery_costs == Decimal("10.00000000")
    assert result.discounted_net_recoveries == Decimal("50.00000000")
    assert result.raw_lgd == Decimal("0.50000000")
    assert result.realized_lgd == Decimal("0.50000000")
    assert result.outcome_type == "loss_lgd"


def test_discounts_recoveries_and_costs_at_contractual_eir() -> None:
    record = _record(
        rate=Decimal("0.10"),
        gross=Decimal("66"),
        cost=Decimal("11"),
        recovery_date=date(2027, 1, 1),
    )

    result = calculate_realized_lgd(record, load_realized_lgd_policy(POLICY_PATH))

    assert result.discounted_gross_recoveries == Decimal("60.00000000")
    assert result.discounted_recovery_costs == Decimal("10.00000000")
    assert result.realized_lgd == Decimal("0.50000000")


def test_cure_lgd_includes_discounted_residual_exposure_without_double_counting() -> None:
    record = _record(
        rate=Decimal("0.10"),
        gross=Decimal("11"),
        cost=Decimal("1"),
        recovery_date=date(2027, 1, 1),
        cure_date=date(2027, 1, 1),
    )

    result = calculate_realized_lgd(record, load_realized_lgd_policy(POLICY_PATH))

    assert result.discounted_cure_value == Decimal("80.90909091")
    assert result.discounted_net_recoveries == Decimal("90.00000000")
    assert result.realized_lgd == Decimal("0.10000000")
    assert result.outcome_type == "cure_lgd"


@pytest.mark.parametrize(
    ("gross", "cost", "expected_raw", "expected_lgd", "expected_action"),
    [
        (Decimal("150"), Decimal("0"), Decimal("-0.50000000"), Decimal("0"), "floored_at_zero"),
        (Decimal("0"), Decimal("200"), Decimal("3.00000000"), Decimal("1"), "capped_at_one"),
    ],
)
def test_preserves_raw_lgd_and_applies_documented_modeling_bounds(
    gross: Decimal,
    cost: Decimal,
    expected_raw: Decimal,
    expected_lgd: Decimal,
    expected_action: str,
) -> None:
    result = calculate_realized_lgd(
        _record(gross=gross, cost=cost), load_realized_lgd_policy(POLICY_PATH)
    )

    assert result.raw_lgd == expected_raw
    assert result.realized_lgd == expected_lgd
    assert result.bound_action == expected_action


def test_marks_censored_lgd_as_provisional() -> None:
    result = calculate_realized_lgd(_record(censored=True), load_realized_lgd_policy(POLICY_PATH))

    assert result.status == "censored_provisional"
    assert result.is_censored is True


def test_calculates_dataset_with_policy_lineage() -> None:
    policy = load_realized_lgd_policy(POLICY_PATH)
    source = LGDWorkoutDataset((_record(), _record(censored=True)), "0.1.0", 24, date(2028, 1, 1))

    results = calculate_realized_lgd_dataset(source, policy)

    assert len(results) == 2
    assert {item.policy_version for item in results} == {"2026.07.1"}
    assert {item.policy_sha256 for item in results} == {policy.sha256}
