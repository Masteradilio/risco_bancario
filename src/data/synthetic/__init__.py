"""Synthetic data generators; never an implicit production fallback."""

from .events import CreditEventHistory, generate_credit_events
from .longitudinal import LongitudinalPortfolio, generate_monthly_history
from .macroeconomics import MacroeconomicBundle, generate_macroeconomic_bundle
from .modeling import ModelingDatasets, build_modeling_datasets
from .population import PopulationConfig, SyntheticPortfolio, generate_population
from .quality import SyntheticQualityReport, assess_synthetic_quality, detect_future_features

__all__ = [
    "CreditEventHistory",
    "LongitudinalPortfolio",
    "MacroeconomicBundle",
    "ModelingDatasets",
    "PopulationConfig",
    "SyntheticPortfolio",
    "SyntheticQualityReport",
    "assess_synthetic_quality",
    "detect_future_features",
    "generate_credit_events",
    "generate_monthly_history",
    "generate_macroeconomic_bundle",
    "generate_population",
    "build_modeling_datasets",
]
