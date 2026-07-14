from datetime import date
from decimal import Decimal

import pytest

from src.domain.scenarios import Scenario, ScenarioKind
from src.domain.staging import Stage
from src.infrastructure.configuration import load_risk_policy


@pytest.mark.regulatory("IFRS9-ECL-002")
def test_IFRS9_ECL_002_scenario_is_typed_and_weighted() -> None:
    scenario = Scenario("base", "Base", ScenarioKind.BASE, date(2026, 7, 14), 12, "1", "v1")
    assert scenario.weight == Decimal("1.00000000")


@pytest.mark.regulatory("IFRS9-FL-001")
def test_IFRS9_FL_001_forward_looking_weights_are_versioned() -> None:
    loaded = load_risk_policy("config/risk_policy/2026.07.1.json")
    assert sum(item.weight for item in loaded.policy.scenarios) == Decimal("1")
    assert loaded.policy.metadata.evidence_status == "demonstrative"


@pytest.mark.regulatory("CMN4966-STAGE-001")
def test_CMN4966_STAGE_001_stage_type_and_policy_are_explicit() -> None:
    loaded = load_risk_policy("config/risk_policy/2026.07.1.json")
    assert tuple(Stage) == (Stage.STAGE_1, Stage.STAGE_2, Stage.STAGE_3)
    assert loaded.policy.staging.score_only_staging_allowed is False
