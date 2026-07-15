"""Regression contract for the canonical release journey."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.e2e_pipeline import resolve_code_version
from src.application.e2e import run_e2e_journey


def test_canonical_e2e_is_reconciled_and_fail_closed(tmp_path: Path) -> None:
    output = tmp_path / "evidence"
    report = run_e2e_journey(output, tmp_path / "work", "abcdef1")

    assert report["status"] == "COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS"
    assert report["approval_blockers"] == ["pd", "sicr", "lgd", "ead"]
    assert report["ecl"]["reconciled"] is True
    assert report["ecl"]["economic_ecl"] == "4.00"
    assert report["ecl"]["final_ecl"] == "5.00"
    assert report["persistence"]["execution_status"] == "COMPLETED"
    assert report["persistence"]["result_rows"] == 4
    assert report["doc3040"]["passed"] is True
    assert report["doc3040"]["official_xsd_executed"] is False
    assert report["doc3040"]["official_critics_executed"] is False
    assert {path.name for path in output.iterdir()} == {
        "doc3040.xml",
        "journey.json",
        "prevalidation.json",
        "report.md",
    }
    persisted = json.loads((output / "journey.json").read_text(encoding="utf-8"))
    assert persisted == report


def test_archive_without_git_metadata_uses_deterministic_source_fingerprint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 128, "", "not a repo"),
    )

    first = resolve_code_version(None, tmp_path)
    second = resolve_code_version(None, tmp_path)

    assert len(first) == 12
    assert first == second
    assert all(character in "0123456789abcdef" for character in first)


def test_explicit_e2e_commit_must_follow_lineage_contract() -> None:
    with pytest.raises(ValueError, match="lowercase hexadecimal"):
        resolve_code_version("unknown")
