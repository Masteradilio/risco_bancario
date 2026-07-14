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
    "calculate_probability_weighted_scenario_ecl",
    "classify_poci",
    "credit_adjusted_eir",
    "measure_poci_change",
]
