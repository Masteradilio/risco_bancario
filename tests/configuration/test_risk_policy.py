from copy import deepcopy
from json import loads
from pathlib import Path
from datetime import date, datetime, timezone
import importlib.util
import sys

import pytest
from pydantic import ValidationError

from src.infrastructure.configuration import RiskPolicy, load_risk_policy
from src.domain.staging import Stage
from src.ecl.calculation import ECLResult, ScenarioECL


POLICY_PATH = Path("config/risk_policy/2026.07.1.json")


def raw_policy() -> dict:
    return loads(POLICY_PATH.read_text(encoding="utf-8"))


def test_canonical_policy_loads_with_metadata_and_stable_hash() -> None:
    first = load_risk_policy(POLICY_PATH)
    second = load_risk_policy(POLICY_PATH)
    assert first.policy.metadata.policy_version == "2026.07.1"
    assert first.policy.metadata.evidence_status == "demonstrative"
    assert len(first.configuration_hash) == 64
    assert first.configuration_hash == second.configuration_hash


@pytest.mark.parametrize("mutation, message", [
    (lambda data: data["scenarios"][0].update(weight="0.20"), "weights must sum"),
    (lambda data: data["staging"].update(stage_3_days_past_due=30), "stage 3 threshold"),
    (lambda data: data["rating_bands"][1].update(lower_inclusive="6"), "contiguous"),
    (lambda data: data["ccf_by_product"].update(consignado="1.1"), "CCF values"),
])
def test_invalid_policy_is_rejected(mutation, message: str) -> None:
    data = deepcopy(raw_policy())
    mutation(data)
    with pytest.raises(ValidationError, match=message):
        RiskPolicy.model_validate(data)


def test_unknown_fields_are_rejected() -> None:
    data = raw_policy()
    data["metadata"]["untracked_approval"] = True
    with pytest.raises(ValidationError, match="Extra inputs"):
        RiskPolicy.model_validate(data)


def test_schema_is_versioned_and_exportable() -> None:
    schema = RiskPolicy.model_json_schema()
    assert schema["title"] == "RiskPolicy"
    assert "PolicyMetadata" in schema["$defs"]


def test_ecl_result_carries_exact_loaded_configuration_identity() -> None:
    loaded = load_risk_policy(POLICY_PATH)
    result = ECLResult(
        "R-CFG", "CT-1", date(2026, 7, 14), datetime(2026, 7, 14, 12, tzinfo=timezone.utc),
        Stage.STAGE_1, "10", "0", "0", "10", (ScenarioECL("base", "1", "10"),),
        "model-v1", loaded.policy.metadata.policy_version, loaded.configuration_hash,
    )
    assert result.configuration_version == "2026.07.1"
    assert result.configuration_hash == loaded.configuration_hash


def test_shared_compatibility_exports_come_from_canonical_policy() -> None:
    from shared import utils

    loaded = load_risk_policy(POLICY_PATH)
    assert utils.RISK_POLICY_VERSION == loaded.policy.metadata.policy_version
    assert utils.RISK_POLICY_HASH == loaded.configuration_hash
    assert utils.CCF_POR_PRODUTO["cheque_especial"] == 0.70
    assert utils.CRITERIOS_STAGE["STAGE_3"]["gatilhos"]["dias_atraso_min"] == 91


def test_legacy_scenario_manager_reads_canonical_weights() -> None:
    module_path = Path("backend/perda_esperada/src/cenarios_forward_looking.py")
    spec = importlib.util.spec_from_file_location("legacy_scenarios_for_config_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    GerenciadorCenarios = module.GerenciadorCenarios
    TipoCenario = module.TipoCenario

    assert GerenciadorCenarios.PESOS_PADRAO[TipoCenario.BASE] == 0.70
    assert sum(GerenciadorCenarios.PESOS_PADRAO.values()) == 1.0
