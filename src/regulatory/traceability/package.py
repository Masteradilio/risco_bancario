"""Export a deterministic regulatory evidence package from canonical sources."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .report import load_requirements, release_blockers, render_report


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def export_regulatory_package(output: Path) -> dict[str, Any]:
    matrix = Path("docs/regulatory/TRACEABILITY_MATRIX.csv")
    limitations = Path("docs/validation/LIMITATION_REGISTER.md")
    sources = Path("docs/regulatory/SOURCE_REGISTER.md")
    requirements = load_requirements(matrix)
    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(matrix, output / "traceability_matrix.csv")
    (output / "coverage.md").write_text(render_report(requirements), encoding="utf-8", newline="\n")

    coverage = []
    for requirement in requirements:
        paths = [Path(item.strip()) for item in requirement.test.split(";") if item.strip()]
        coverage.append(
            {
                "requirement_id": requirement.requirement_id,
                "test_paths": [path.as_posix() for path in paths],
                "test_functions": sum(
                    len(re.findall(r"^def test_", path.read_text(encoding="utf-8"), re.MULTILINE))
                    for path in paths
                    if path.is_file() and path.suffix == ".py"
                ),
                "status": requirement.implementation_status,
            }
        )
    _write(output / "test_coverage.json", coverage)
    _write(
        output / "limitations_and_not_applicable.json",
        {
            "limitation_register": {"path": limitations.as_posix(), "sha256": _hash(limitations)},
            "not_applicable": [
                asdict(item) for item in requirements if item.applicability == "not_applicable"
            ],
            "release_blockers": [item.requirement_id for item in release_blockers(requirements)],
        },
    )
    layouts = []
    for path in sorted(Path("config/regulatory/doc3040/layouts").glob("*.json")):
        layouts.append(
            {
                "path": path.as_posix(),
                "sha256": _hash(path),
                "document": json.loads(path.read_text(encoding="utf-8")),
            }
        )
    _write(
        output / "sources_and_layouts.json",
        {
            "source_register": {"path": sources.as_posix(), "sha256": _hash(sources)},
            "layouts": layouts,
        },
    )
    artifacts = sorted(path for path in output.iterdir() if path.name != "manifest.json")
    manifest = {
        "schema_version": "1.0.0",
        "scope": "synthetic_prevalidation_not_certification",
        "requirements": len(requirements),
        "release_blockers": len(release_blockers(requirements)),
        "artifacts": [{"path": path.name, "sha256": _hash(path)} for path in artifacts],
    }
    _write(output / "manifest.json", manifest)
    return manifest
