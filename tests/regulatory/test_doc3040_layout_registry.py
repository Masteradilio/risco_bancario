import hashlib
import json
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
from src.regulatory.doc3040.layout_registry import load_layout_manifest

MANIFEST = Path("config/regulatory/doc3040/layouts/2026.07-observed-20260714.json")


def _payload() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _write(tmp_path: Path, payload: object, name: str = "layout.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


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


def test_layout_artifact_lookup_rejects_unknown_name() -> None:
    with pytest.raises(DomainValidationError, match="does not declare artifact"):
        load_layout_registry()[0].artifact("unknown")


@pytest.mark.parametrize("value", [None, "", " padded "])
def test_manifest_required_text_is_strict(tmp_path: Path, value: object) -> None:
    payload = _payload()
    payload["source_id"] = value
    with pytest.raises(DomainValidationError, match="source_id must be non-empty"):
        load_layout_manifest(_write(tmp_path, payload))


@pytest.mark.parametrize("value", [None, [], ["ok", ""]])
def test_manifest_text_lists_are_strict(tmp_path: Path, value: object) -> None:
    payload = _payload()
    payload["normative_acts"] = value
    with pytest.raises(DomainValidationError, match="non-empty list"):
        load_layout_manifest(_write(tmp_path, payload))


def test_manifest_root_dates_hashes_and_artifacts_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(DomainValidationError, match="root must be an object"):
        load_layout_manifest(_write(tmp_path, []))

    mutations = (
        (lambda p: p.update(artifacts={}), "requires official artifacts"),
        (
            lambda p: p["artifacts"].update(layout_and_domains="bad"),
            "must be an object",
        ),
        (
            lambda p: p["artifacts"]["layout_and_domains"].update(url="https://example.com/a"),
            "official BCB URL",
        ),
        (
            lambda p: p["artifacts"]["layout_and_domains"].update(sha256="bad"),
            "lowercase SHA-256",
        ),
        (lambda p: p.update(observed_at="not-a-date"), "must be ISO date"),
    )
    for index, (mutate, message) in enumerate(mutations):
        payload = _payload()
        mutate(payload)
        with pytest.raises(DomainValidationError, match=message):
            load_layout_manifest(_write(tmp_path, payload, f"invalid-{index}.json"))


def test_manifest_catalog_and_xsd_provenance_fail_closed(tmp_path: Path) -> None:
    mutations = (
        (lambda p: p.pop("domain_catalog"), "requires domain and critic"),
        (
            lambda p: p["domain_catalog"].update(artifact="unknown"),
            "unknown artifact",
        ),
        (lambda p: p.update(xsd="bad"), "xsd must be an object"),
        (
            lambda p: p.update(
                xsd={
                    "document_code": "3040",
                    "filename": "doc.xsd",
                    "source_url": "https://example.com/doc.xsd",
                    "sha256": "0" * 64,
                }
            ),
            "official BCB URL",
        ),
        (lambda p: p.update(derived_xsd="bad"), "derived_xsd must be an object"),
        (
            lambda p: p["derived_xsd"].update(derived_from_artifact="unknown"),
            "declared source artifact",
        ),
    )
    for index, (mutate, message) in enumerate(mutations):
        payload = _payload()
        mutate(payload)
        with pytest.raises(DomainValidationError, match=message):
            load_layout_manifest(_write(tmp_path, payload, f"provenance-{index}.json"))

    valid_xsd = _payload()
    valid_xsd["xsd"] = {
        "document_code": "3040",
        "filename": "doc3040.xsd",
        "source_url": "https://www.bcb.gov.br/doc3040.xsd",
        "sha256": "0" * 64,
    }
    assert load_layout_manifest(_write(tmp_path, valid_xsd, "valid-xsd.json")).xsd is not None


def test_manifest_layout_invariants_fail_closed(tmp_path: Path) -> None:
    mutations = (
        (lambda p: p.update(document_code="3045"), "only document 3040"),
        (lambda p: p.update(effective_from="2026-07-02"), "first day"),
        (lambda p: p.update(effective_to="2026-06-01"), "must precede"),
        (lambda p: p["derived_xsd"].update(document_code="3045"), "identify document 3040"),
        (
            lambda p: (p.update(derived_xsd=None), p.update(generation_enabled=True)),
            "cannot be enabled",
        ),
    )
    for index, (mutate, message) in enumerate(mutations):
        payload = _payload()
        mutate(payload)
        with pytest.raises(DomainValidationError, match=message):
            load_layout_manifest(_write(tmp_path, payload, f"invariant-{index}.json"))


def test_registry_rejects_empty_duplicate_and_overlapping_versions(tmp_path: Path) -> None:
    with pytest.raises(DomainValidationError, match="no Doc3040"):
        load_layout_registry(tmp_path)

    first = _payload()
    second = _payload()
    _write(tmp_path, first, "one.json")
    _write(tmp_path, second, "two.json")
    with pytest.raises(DomainValidationError, match="versions must be unique"):
        load_layout_registry(tmp_path)

    second["version"] = "second"
    second["effective_from"] = "2026-10-01"
    second["effective_to"] = "2027-01-01"
    _write(tmp_path, second, "two.json")
    with pytest.raises(DomainValidationError, match="must not overlap"):
        load_layout_registry(tmp_path)

    periods = (
        ("one", "2026-01-01", "2026-03-01"),
        ("two", "2026-03-01", "2026-05-01"),
        ("three", "2026-05-01", "2026-07-01"),
    )
    for filename, start, end in periods:
        payload = _payload()
        payload.update(version=filename, effective_from=start, effective_to=end)
        _write(tmp_path, payload, f"{filename}.json")
    assert len(load_layout_registry(tmp_path)) == 3


def test_official_and_derived_xsd_loaders_cover_success_and_integrity(tmp_path: Path) -> None:
    content = b"<schema/>"
    digest = hashlib.sha256(content).hexdigest()
    official_path = tmp_path / "doc3040.xsd"
    official_path.write_bytes(content)
    layout = replace(
        load_layout_registry()[0],
        xsd=XsdRef("3040", official_path.name, "https://www.bcb.gov.br/doc3040.xsd", digest),
    )
    assert load_official_xsd(layout, official_path) == content

    without_derived = replace(layout, derived_xsd=None)
    with pytest.raises(DomainValidationError, match="has no derived"):
        load_derived_xsd(without_derived)
    missing = replace(layout.derived_xsd, path=tmp_path / "missing.xsd")
    with pytest.raises(DomainValidationError, match="does not exist"):
        load_derived_xsd(replace(layout, derived_xsd=missing))
    wrong_path = tmp_path / "derived.xsd"
    wrong_path.write_bytes(b"wrong")
    wrong = replace(layout.derived_xsd, path=wrong_path)
    with pytest.raises(DomainValidationError, match="SHA-256 mismatch"):
        load_derived_xsd(replace(layout, derived_xsd=wrong))
