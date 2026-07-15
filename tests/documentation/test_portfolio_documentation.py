from __future__ import annotations

import json
from pathlib import Path

from src.interfaces.api.schemas import ECLCalculationRequest

ROOT = Path(__file__).parents[2]


def test_portfolio_documentation_is_complete_and_uses_canonical_paths() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required = (
        "src/interfaces/api",
        "powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\setup.ps1",
        "scripts\\e2e_pipeline.py",
        "docs/architecture/SYSTEM_ARCHITECTURE.md",
        "docs/tutorials/ECL_TUTORIAL.md",
        "docs/api/EXAMPLES.md",
        "docs/portfolio/TECHNICAL_INTERVIEW_GUIDE.md",
        "docs/demo/screenshots/ecl-evidence-workspace.png",
        "COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS",
        "PREVALIDATED_DERIVED_XSD",
    )
    assert all(item in readme for item in required)
    assert "fallback automático" not in readme
    assert "backend/perda_esperada/src/pipeline_ecl.py" not in readme
    assert "conformidade regulatória BACEN" not in readme


def test_api_example_is_a_valid_reproducible_calculation() -> None:
    fixture = ROOT / "docs/api/examples/ecl_individual.json"
    request = ECLCalculationRequest.model_validate(json.loads(fixture.read_text(encoding="utf-8")))

    assert request.contract_id == "C-SYNTHETIC-API-1"
    assert sum(scenario.weight for scenario in request.scenarios) == 1
    assert len(request.scenarios) == 4


def test_documented_artifacts_and_screenshot_exist() -> None:
    expected = (
        "docs/architecture/SYSTEM_ARCHITECTURE.md",
        "docs/tutorials/ECL_TUTORIAL.md",
        "docs/api/EXAMPLES.md",
        "docs/portfolio/TECHNICAL_INTERVIEW_GUIDE.md",
        "docs/demo/README.md",
        "docs/demo/screenshots/ecl-evidence-workspace.png",
    )
    assert all((ROOT / item).is_file() for item in expected)
