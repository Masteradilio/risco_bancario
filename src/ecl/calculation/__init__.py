"""Typed ECL calculation result contracts."""

from .models import ECLResult, ScenarioECL
from .poci import (
    POCICashFlow,
    POCIClassification,
    POCIMeasurement,
    classify_poci,
    credit_adjusted_eir,
    measure_poci_change,
)
from .scenario_engine import (
    BaselineRiskPeriod,
    ProbabilityWeightedScenarioECL,
    ScenarioIntegral,
    ScenarioRiskPeriod,
    calculate_probability_weighted_scenario_ecl,
)
from .sensitivity import (
    ScenarioSensitivityPolicy,
    ScenarioSensitivityReport,
    SensitivityResult,
    TrajectoryShock,
    WeightSensitivityCase,
    load_scenario_sensitivity_policy,
    run_scenario_sensitivities,
)
from .stage1 import (
    Stage1ContractInput,
    Stage1ECLResult,
    Stage1RiskPeriod,
    calculate_stage1_ecl,
)
from .stage2 import (
    Stage2CalculationMode,
    Stage2ContractInput,
    Stage2ECLResult,
    Stage2RiskPeriod,
    calculate_stage2_ecl,
)

__all__ = [
    "ECLResult",
    "BaselineRiskPeriod",
    "POCICashFlow",
    "POCIClassification",
    "POCIMeasurement",
    "ProbabilityWeightedScenarioECL",
    "ScenarioECL",
    "ScenarioIntegral",
    "ScenarioRiskPeriod",
    "ScenarioSensitivityPolicy",
    "ScenarioSensitivityReport",
    "SensitivityResult",
    "Stage1ContractInput",
    "Stage1ECLResult",
    "Stage1RiskPeriod",
    "Stage2CalculationMode",
    "Stage2ContractInput",
    "Stage2ECLResult",
    "Stage2RiskPeriod",
    "TrajectoryShock",
    "WeightSensitivityCase",
    "calculate_probability_weighted_scenario_ecl",
    "calculate_stage1_ecl",
    "calculate_stage2_ecl",
    "classify_poci",
    "credit_adjusted_eir",
    "measure_poci_change",
    "load_scenario_sensitivity_policy",
    "run_scenario_sensitivities",
]
