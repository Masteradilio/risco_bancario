import json
import sys
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pyarrow.parquet as pq
import pytest

from src.data.synthetic import export
from src.data.synthetic.export import REQUIRED_DATASETS, _write_table, materialize_synthetic_factory


def _manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_materialization_writes_all_required_parquets_and_manifest(tmp_path: Path) -> None:
    manifest_path = materialize_synthetic_factory(tmp_path / "factory")
    manifest = _manifest(manifest_path)
    assert all((manifest_path.parent / f"{name}.parquet").exists() for name in REQUIRED_DATASETS)
    assert manifest["seed"] == 91
    assert manifest["factory_version"] == "0.1.0"


def test_manifest_counts_schemas_and_hashes_match_files(tmp_path: Path) -> None:
    manifest_path = materialize_synthetic_factory(tmp_path / "factory")
    manifest = _manifest(manifest_path)
    for filename, metadata in manifest["files"].items():
        path = manifest_path.parent / filename
        assert sha256(path.read_bytes()).hexdigest() == metadata["sha256"]
        assert pq.read_metadata(path).num_rows == metadata["rows"]
        assert metadata["schema"]


def test_same_inputs_produce_identical_bytes(tmp_path: Path) -> None:
    first = materialize_synthetic_factory(tmp_path / "first")
    second = materialize_synthetic_factory(tmp_path / "second")
    first_files = {item.name: item.read_bytes() for item in first.parent.iterdir()}
    second_files = {item.name: item.read_bytes() for item in second.parent.iterdir()}
    assert first_files == second_files


def test_regulatory_source_is_neutral_and_does_not_invent_layout_fields(
    tmp_path: Path,
) -> None:
    manifest = materialize_synthetic_factory(tmp_path / "factory")
    schema = pq.read_schema(manifest.parent / "regulatory_reporting_input.parquet")
    assert {"contract_id", "counterparty_id", "balance", "days_past_due"} <= set(schema.names)
    assert not {"cosif", "ipoc", "cep", "doc3040_code"} & set(schema.names)


def test_derived_tables_reconcile_to_canonical_snapshots(tmp_path: Path) -> None:
    manifest_path = materialize_synthetic_factory(tmp_path / "factory")
    manifest = _manifest(manifest_path)
    snapshot_rows = manifest["files"]["monthly_snapshots.parquet"]["rows"]
    assert manifest["files"]["payments.parquet"]["rows"] == snapshot_rows
    assert manifest["files"]["delinquencies.parquet"]["rows"] == snapshot_rows
    assert manifest["files"]["limits_and_drawdowns.parquet"]["rows"] == snapshot_rows


def test_tracked_acceptance_artifact_matches_its_manifest() -> None:
    root = Path("data/synthetic/acceptance-v0.1.0")
    manifest = _manifest(root / "manifest.json")
    for filename, metadata in manifest["files"].items():
        path = root / filename
        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == metadata["sha256"]


def test_export_rejects_empty_table_failed_quality_and_missing_manifest_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValueError, match="cannot materialize empty"):
        _write_table(tmp_path / "empty.parquet", [])

    monkeypatch.setattr(
        export,
        "assess_synthetic_quality",
        lambda *_args: SimpleNamespace(passed=False, issues=("forced",)),
    )
    with pytest.raises(ValueError, match="quality gate failed"):
        materialize_synthetic_factory(tmp_path / "failed")

    monkeypatch.undo()
    monkeypatch.setattr(export, "REQUIRED_DATASETS", (*REQUIRED_DATASETS, "missing"))
    monkeypatch.setattr(
        export,
        "assess_synthetic_quality",
        lambda *_args: SimpleNamespace(passed=True, issues=()),
    )
    with pytest.raises(ValueError, match="missing required datasets"):
        materialize_synthetic_factory(tmp_path / "missing")


def test_export_main_parses_cli_and_prints_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "factory"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "synthetic-export",
            "--output",
            str(destination),
            "--seed",
            "7",
            "--clients",
            "8",
            "--contracts-per-client",
            "1",
        ],
    )
    expected = destination / "manifest.json"
    monkeypatch.setattr(export, "materialize_synthetic_factory", lambda *_args, **_kwargs: expected)
    export.main()
    assert capsys.readouterr().out.strip() == str(expected)
