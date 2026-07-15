from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[2]


def _scorecard() -> dict[str, Any]:
    path = ROOT / "evidence/release/final_scorecard.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _setup_smoke() -> dict[str, Any]:
    path = ROOT / "evidence/release/setup_smoke.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_final_scorecard_covers_every_dimension_with_real_evidence() -> None:
    scorecard = _scorecard()
    dimensions = scorecard["dimensions"]

    assert scorecard["technical_score"] == "10/10"
    assert scorecard["scope"] == "synthetic_engineering_completeness_not_institutional_approval"
    assert {item["id"] for item in dimensions} == {
        "architecture",
        "pd",
        "lgd",
        "ead",
        "ecl",
        "staging",
        "regulation",
        "validation",
        "security",
        "experience_and_portfolio",
    }
    assert all(item["score"] == 10 for item in dimensions)
    assert all(item["technical_status"] == "complete" for item in dimensions)
    assert all(item["residual_limit"] for item in dimensions)
    assert all((ROOT / path).is_file() for item in dimensions for path in item["evidence"])


def test_scorecard_preserves_model_and_regulatory_blockers() -> None:
    dimensions = {item["id"]: item for item in _scorecard()["dimensions"]}

    assert all(
        dimensions[item]["decision_status"] == "not_approved"
        for item in ("pd", "lgd", "ead", "staging")
    )
    assert dimensions["ecl"]["decision_status"] == "reconciliation_passed_backtest_rejected"
    assert dimensions["regulation"]["decision_status"] == "prevalidated_derived_xsd_only"
    assert "BLOCKED" in _scorecard()["institutional_release_status"]


def test_human_assessment_defines_the_score_without_claiming_approval() -> None:
    report = (ROOT / "docs/FINAL_RELEASE_ASSESSMENT.md").read_text(encoding="utf-8")

    assert "10/10 de completude técnica" in report
    assert "não é\naprovação de modelo" in report
    assert "COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS" in report
    assert "PREVALIDATED_DERIVED_XSD" in report


def test_obsolete_plans_and_legacy_schemas_do_not_claim_regulatory_completion() -> None:
    todo = (ROOT / "TODO.md").read_text(encoding="utf-8")
    legacy_database = (ROOT / "backend/bancos_de_dados/README.md").read_text(encoding="utf-8")

    assert "não usar como backlog" in todo
    assert "TODO - Próximos Passos" not in todo
    assert "Este modelo de dados atende aos requisitos" not in legacy_database
    assert "não comprovam aderência regulatória" in legacy_database


def test_legacy_exports_are_explicitly_non_official() -> None:
    paths = (
        "backend/perda_esperada/src/api.py",
        "backend/perda_esperada/src/modulo_exportacao_bacen.py",
        "backend/perda_esperada/src/modulo_forward_looking.py",
        "backend/perda_esperada/src/modulo_pd_behavior.py",
        "frontend/src/pages/ecl/ECLExportacaoPage.tsx",
        "frontend-nextjs-backup/src/app/perda-esperada/exportacao/page.tsx",
    )
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in paths)

    assert "conforme Resolução CMN 4966" not in combined
    assert "Validação contra schema XSD oficial" not in combined
    assert "SEM_PROTOCOLO_OFICIAL" in combined
    assert "não homologado" in combined


def test_clean_setup_and_demo_evidence_preserve_expected_blockers() -> None:
    smoke = _setup_smoke()

    assert smoke["setup_status"] == "passed"
    assert smoke["demo_status"] == "COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS"
    assert smoke["approval_blockers"] == ["pd", "sicr", "lgd", "ead"]
    assert smoke["ecl_reconciled"] is True
    assert smoke["doc3040_status"] == "PREVALIDATED_DERIVED_XSD"
    assert smoke["official_xsd_executed"] is False
    assert smoke["official_critics_executed"] is False
