import runpy
import sys
from pathlib import Path

import pytest

from src.regulatory.traceability.report import (
    Requirement,
    load_requirements,
    main,
    release_blockers,
    render_report,
)

MATRIX = Path("docs/regulatory/TRACEABILITY_MATRIX.csv")


def test_report_covers_every_matrix_row() -> None:
    requirements = load_requirements(MATRIX)
    report = render_report(requirements)
    assert all(f"`{item.requirement_id}`" in report for item in requirements)


def test_release_is_blocked_while_mandatory_requirements_are_incomplete(tmp_path: Path) -> None:
    requirements = load_requirements(MATRIX)
    assert release_blockers(requirements)
    output = tmp_path / "coverage.md"
    assert main(["--matrix", str(MATRIX), "--output", str(output), "--enforce"]) == 1
    assert "Release blockers:" in output.read_text(encoding="utf-8")


def test_non_enforcing_report_is_generated(tmp_path: Path) -> None:
    output = tmp_path / "coverage.md"
    assert main(["--matrix", str(MATRIX), "--output", str(output)]) == 0
    assert output.is_file()


def test_report_without_blockers_and_script_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    complete = Requirement(
        "REQ",
        "SRC",
        "Topic",
        "applicable",
        "implemented",
        "src/file.py",
        str(Path(__file__)),
        "evidence/file",
    )
    assert "- None" in render_report((complete,))

    output = tmp_path / "entrypoint.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report.py",
            "--matrix",
            str(MATRIX),
            "--output",
            str(output),
        ],
    )
    monkeypatch.delitem(sys.modules, "src.regulatory.traceability.report")
    with pytest.raises(SystemExit, match="0"):
        runpy.run_module("src.regulatory.traceability.report", run_name="__main__")
