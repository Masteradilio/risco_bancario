import json
from hashlib import sha256
from pathlib import Path

import pyarrow.parquet as pq

from src.data.synthetic.export import REQUIRED_DATASETS, materialize_synthetic_factory


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
