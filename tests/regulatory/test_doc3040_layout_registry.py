from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from src.domain.exceptions import DomainValidationError
from src.regulatory.doc3040 import (
    XsdRef,
    layout_for_reference_month,
    load_derived_xsd,
    load_layout_registry,
    load_official_xsd,
    verify_artifact_file,
)


def test_doc3040_layout_001_selects_only_observed_supported_reference_months() -> None:
    registry = load_layout_registry()
    assert len(registry) == 1
    assert (
        layout_for_reference_month(date(2026, 7, 1), registry).version
        == "2026.07-observed-20260714"
    )
    assert (
        layout_for_reference_month(date(2026, 10, 1), registry).version
        == "2026.07-observed-20260714"
    )
    for unsupported in (date(2026, 5, 1), date(2026, 11, 1), date(2027, 1, 1)):
        with pytest.raises(DomainValidationError, match="unsupported Doc3040"):
            layout_for_reference_month(unsupported, registry)


def test_manifest_versions_domain_and_critic_artifacts_by_hash() -> None:
    layout = load_layout_registry()[0]
    assert layout.domain_catalog.artifact == "layout_and_domains"
    assert "NR3" in layout.domain_catalog.future_markers_must_be_filtered
    assert layout.critic_catalog.critics_last_update == date(2026, 7, 10)
    assert layout.critic_catalog.execution_status == "versioned_not_yet_executed"
    assert all(len(artifact.sha256) == 64 for artifact in layout.artifacts.values())
    assert {"critics", "bacen_reconciliation_rules"} <= set(layout.critic_catalog.artifacts)


def test_doc3040_xsd_001_fails_closed_when_official_page_has_no_3040_xsd() -> None:
    layout = load_layout_registry()[0]
    assert layout.generation_enabled
    assert layout.derived_xsd is not None
    assert load_derived_xsd(layout).startswith(b'<?xml version="1.0"')
    with pytest.raises(DomainValidationError, match="lists_xsd_3045_not_3040"):
        layout.require_official_xsd()


def test_doc3040_xsd_001_rejects_xsd_for_a_different_document(tmp_path: Path) -> None:
    layout = load_layout_registry()[0]
    wrong = replace(
        layout,
        xsd=XsdRef(
            document_code="3045",
            filename="doc3045.xsd",
            source_url="https://www.bcb.gov.br/doc3045.xsd",
            sha256="0" * 64,
        ),
    )
    with pytest.raises(DomainValidationError, match="cannot validate document 3040"):
        load_official_xsd(wrong, tmp_path / "doc3045.xsd")


def test_artifact_loader_checks_filename_and_sha256(tmp_path: Path) -> None:
    layout = load_layout_registry()[0]
    artifact = layout.artifact("layout_and_domains")
    wrong_name = tmp_path / "layout.xls"
    wrong_name.write_bytes(b"not the official workbook")
    with pytest.raises(DomainValidationError, match="filename mismatch"):
        verify_artifact_file(artifact, wrong_name)
    expected_name = tmp_path / artifact.filename
    expected_name.write_bytes(b"not the official workbook")
    with pytest.raises(DomainValidationError, match="SHA-256 mismatch"):
        verify_artifact_file(artifact, expected_name)


def test_reference_month_must_be_month_start() -> None:
    with pytest.raises(DomainValidationError, match="first day"):
        layout_for_reference_month(date(2026, 7, 31))
