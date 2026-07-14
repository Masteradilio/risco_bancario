"""Synthetic data generators; never an implicit production fallback."""

from .population import PopulationConfig, SyntheticPortfolio, generate_population

__all__ = ["PopulationConfig", "SyntheticPortfolio", "generate_population"]
