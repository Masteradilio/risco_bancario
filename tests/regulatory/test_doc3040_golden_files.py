import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.exceptions import DomainValidationError
from src.regulatory.doc3040 import (
    PortfolioEclControl,
    generate_xml_candidate,
    layout_for_reference_month,
    prevalidate_xml,
)
from tests.regulatory.test_doc3040_validation import controls, reconciled_document

FIXTURES = Path("tests/fixtures/doc3040/2026.07")


def manifest():
    return json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))


def test_valid_golden_is_byte_stable_and_locally_prevalidated() -> None:
    expected = (FIXTURES / "valid_minimal.xml").read_bytes()
    generated = generate_xml_candidate(reconciled_document()).content
    assert expected.rstrip(b"\r\n") == generated
    report = prevalidate_xml(expected, controls())
    assert report.passed
    assert report.status == manifest()["files"]["valid_minimal.xml"]["expected_status"]
    assert report.layout_version == manifest()["layout_version"]


@pytest.mark.parametrize(
    ("filename", "control_values"),
    [
        ("invalid_xsd_missing_cep.xml", controls()),
        (
            "invalid_domain_modality.xml",
            (
                PortfolioEclControl(
                    "123456789999112345678901CONTRATO1",
                    Decimal("980"),
                    Decimal("20"),
                    "ECL-LEDGER-2026-07",
                ),
            ),
        ),
        ("invalid_semantic_total.xml", controls()),
    ],
)
def test_invalid_goldens_fail_in_the_declared_category(filename, control_values) -> None:
    report = prevalidate_xml((FIXTURES / filename).read_bytes(), control_values)
    expected_rule = manifest()["files"][filename]["expected_rule"]
    assert not report.passed
    assert expected_rule in {issue.rule_id for issue in report.errors}


def test_fixture_manifest_hashes_every_xml() -> None:
    declared = manifest()["files"]
    assert set(declared) == {path.name for path in FIXTURES.glob("*.xml")}
    for filename, metadata in declared.items():
        assert hashlib.sha256((FIXTURES / filename).read_bytes()).hexdigest() == metadata["sha256"]


def test_layout_version_regression_blocks_future_and_past_months() -> None:
    layout = layout_for_reference_month(date(2026, 7, 1))
    assert layout.version == manifest()["layout_version"]
    assert layout_for_reference_month(date(2026, 10, 1)).version == layout.version
    for unsupported in (date(2026, 6, 1), date(2026, 11, 1)):
        with pytest.raises(DomainValidationError, match="unsupported Doc3040"):
            layout_for_reference_month(unsupported)


def test_golden_status_never_claims_official_validation() -> None:
    report = prevalidate_xml((FIXTURES / "valid_minimal.xml").read_bytes(), controls())
    assert manifest()["status"] == "synthetic_local_prevalidation_not_bcb_homologation"
    assert not report.official_xsd_executed
    assert not report.official_critics_executed
