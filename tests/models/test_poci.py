import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.exceptions import DomainValidationError
from src.ecl.calculation import (
    POCICashFlow,
    classify_poci,
    credit_adjusted_eir,
    measure_poci_change,
)


def test_poci_classification_covers_acquired_and_originated_credit_impaired() -> None:
    acquired = classify_poci(
        "CT-A", acquired_credit_impaired=True, originated_credit_impaired=False
    )
    originated = classify_poci(
        "CT-O", acquired_credit_impaired=False, originated_credit_impaired=True
    )
    performing = classify_poci(
        "CT-P", acquired_credit_impaired=False, originated_credit_impaired=False
    )
    assert acquired.is_poci and acquired.classification_reason == "acquired_credit_impaired"
    assert originated.is_poci and originated.classification_reason == "originated_credit_impaired"
    assert not performing.is_poci and performing.classification_reason is None


def test_credit_adjusted_eir_uses_initial_expected_cashflows() -> None:
    result = credit_adjusted_eir(
        "80",
        date(2026, 1, 1),
        (POCICashFlow(date(2027, 1, 1), "88"),),
    )
    assert result == Decimal("0.10000000")


@pytest.mark.parametrize(
    "row",
    list(csv.DictReader(Path("tests/fixtures/golden/poci_cases.csv").open(encoding="utf-8"))),
    ids=lambda row: row["case_id"],
)
def test_poci_golden_cases_reconcile_manual_measurement(row) -> None:
    recognition = date(2026, 1, 1)
    payment = date(2027, 1, 1)
    result = measure_poci_change(
        row["case_id"],
        recognition,
        row["purchase_price"],
        (POCICashFlow(payment, row["contractual_cashflow"]),),
        (POCICashFlow(payment, row["initial_expected"]),),
        (POCICashFlow(payment, row["current_expected"]),),
    )
    assert result.credit_adjusted_eir == Decimal(row["expected_eir"])
    assert result.initial_lifetime_ecl == Decimal(row["expected_initial_ecl"])
    assert result.current_lifetime_ecl == Decimal(row["expected_current_ecl"])
    assert result.cumulative_lifetime_ecl_change == Decimal(row["expected_change"])
    expected_classification = (
        "impairment_loss" if Decimal(row["expected_change"]) > 0 else "impairment_gain"
    )
    assert result.change_classification == expected_classification
    assert result.status == "synthetic_unapproved"


def test_poci_expected_cashflows_must_align_and_not_exceed_contractual() -> None:
    recognition = date(2026, 1, 1)
    with pytest.raises(DomainValidationError, match="match contractual dates"):
        measure_poci_change(
            "CT",
            recognition,
            "80",
            (POCICashFlow(date(2027, 1, 1), "100"),),
            (POCICashFlow(date(2027, 2, 1), "88"),),
            (POCICashFlow(date(2027, 1, 1), "77"),),
        )
    with pytest.raises(DomainValidationError, match="cannot exceed"):
        measure_poci_change(
            "CT",
            recognition,
            "80",
            (POCICashFlow(date(2027, 1, 1), "100"),),
            (POCICashFlow(date(2027, 1, 1), "101"),),
            (POCICashFlow(date(2027, 1, 1), "77"),),
        )


def test_poci_credit_adjusted_eir_fails_when_price_cannot_reconcile() -> None:
    with pytest.raises(DomainValidationError, match="cannot be reconciled"):
        credit_adjusted_eir(
            "1000000",
            date(2026, 1, 1),
            (POCICashFlow(date(2027, 1, 1), "88"),),
        )
