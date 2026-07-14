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
    "TrajectoryShock",
    "WeightSensitivityCase",
    "calculate_probability_weighted_scenario_ecl",
    "classify_poci",
    "credit_adjusted_eir",
    "measure_poci_change",
    "load_scenario_sensitivity_policy",
    "run_scenario_sensitivities",
]
