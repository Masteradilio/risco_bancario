import json
from pathlib import Path

from src.regulatory.traceability.package import export_regulatory_package


def test_package_exports_traceability_coverage_limits_sources_and_layouts(tmp_path: Path) -> None:
    manifest = export_regulatory_package(tmp_path)
    assert manifest["requirements"] == 27
    assert manifest["release_blockers"] == 6
    assert {item["path"] for item in manifest["artifacts"]} == {
        "coverage.md",
        "limitations_and_not_applicable.json",
        "sources_and_layouts.json",
        "test_coverage.json",
        "traceability_matrix.csv",
    }
    limitations = json.loads(
        (tmp_path / "limitations_and_not_applicable.json").read_text(encoding="utf-8")
    )
    assert {item["requirement_id"] for item in limitations["not_applicable"]} == {
        "IFRS9-HEDGE-NA",
        "DOC3040-SEND-NA",
    }
    assert len(limitations["release_blockers"]) == 6


def test_package_is_byte_stable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    export_regulatory_package(first)
    export_regulatory_package(second)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
