import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.domain.contracts import (
    AmortizationMethod,
    AmortizationTerms,
    project_amortized_schedule,
)

FIXTURE = Path("tests/fixtures/golden/amortization_cases.csv")
TOLERANCE = Decimal("0.01")


def schedules():
    return {
        method.value: project_amortized_schedule(
            AmortizationTerms(
                f"GOLDEN-{method.value}",
                date(2026, 1, 15),
                "1200",
                3,
                "0.12",
                method,
            )
        )
        for method in AmortizationMethod
    }


def test_periods_match_manual_reference_within_one_cent() -> None:
    generated = schedules()
    with FIXTURE.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 9
    for row in rows:
        period = generated[row["method"]].periods[int(row["period"]) - 1]
        for field in (
            "opening_balance",
            "principal",
            "interest",
            "total_payment",
            "closing_balance",
        ):
            assert abs(getattr(period, field) - Decimal(row[field])) <= TOLERANCE


def test_each_golden_period_reconciles_cash_flow_and_balance() -> None:
    for schedule in schedules().values():
        for period in schedule.periods:
            assert period.opening_balance - period.principal == period.closing_balance
            assert period.principal + period.interest + period.fee == period.total_payment


def test_all_golden_methods_close_principal_exactly() -> None:
    for schedule in schedules().values():
        assert sum(item.principal for item in schedule.periods) == Decimal("1200.00")
        assert schedule.periods[-1].closing_balance == Decimal("0.00")
