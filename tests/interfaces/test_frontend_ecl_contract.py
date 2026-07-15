from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_active_frontend_routes_only_to_canonical_ecl_workspace() -> None:
    app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")

    assert 'path="perda-esperada"' in app
    assert "ECLDashboardPage" in app
    assert "@/pages/DashboardPage" not in app
    assert "@/pages/propensao/PropensaoPage" not in app
    assert "@/pages/prinad/PrinadPage" not in app


def test_frontend_has_no_embedded_demo_credentials() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "frontend/src").rglob("*.ts*")
    )

    for forbidden in ("analista123", "gestor123", "auditor123", "admin123", "MOCK_USERS"):
        assert forbidden not in sources


def test_ecl_workspace_is_evidence_driven_and_discloses_limits() -> None:
    dashboard = (ROOT / "frontend/src/pages/ecl/ECLDashboardPage.tsx").read_text(encoding="utf-8")

    for required in (
        "getExecutionEvidence",
        "payloadHash",
        "stage_assessment",
        "Curvas marginais PD / LGD",
        "Curva EAD",
        "ECL por período e cenário",
        "Overlays e pisos",
        "getLimitationRegister",
        "DADOS SINTÉTICOS",
        "Nenhum dado substituto foi exibido",
    ):
        assert required in dashboard


def test_legacy_random_agent_is_not_mounted_and_active_agent_is_grounded() -> None:
    legacy_main = (ROOT / "backend/main.py").read_text(encoding="utf-8")
    app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    agent_page = (ROOT / "frontend/src/pages/agent/EvidenceAgentPage.tsx").read_text(
        encoding="utf-8"
    )

    assert "agent_router" not in legacy_main
    assert 'path="agent"' in app
    for required in (
        "queryEvidenceAgent",
        "EVIDÊNCIAS SINTÉTICAS PERSISTIDAS",
        "Citações internas verificáveis",
        "Nenhuma resposta alternativa foi gerada",
    ):
        assert required in agent_page
