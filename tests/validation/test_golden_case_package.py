from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from src.validation.golden_cases import calculate_case, load_cases

PACKAGE = Path("docs/golden_cases/golden_cases.json")
LEGACY_FIXTURE = Path("tests/fixtures/golden/ecl_cases.csv")
WORKBOOK = Path("docs/golden_cases/ecl_golden_cases.xlsx")


def test_independent_formulas_reconcile_production_golden_fixture() -> None:
    with LEGACY_FIXTURE.open(encoding="utf-8", newline="") as stream:
        expected = {
            row["case_id"]: Decimal(row["expected_value"]) for row in csv.DictReader(stream)
        }
    cases = load_cases(PACKAGE)

    assert {case["case_id"] for case in cases} == set(expected)
    for case in cases:
        calculated = calculate_case(case)
        assert calculated == Decimal(case["expected"])
        assert calculated == expected[case["case_id"]]
        assert Decimal(case["tolerance"]) == 0


def test_independent_workbook_is_published_as_xlsx() -> None:
    content = WORKBOOK.read_bytes()
    assert content.startswith(b"PK")
    assert len(content) > 10_000
