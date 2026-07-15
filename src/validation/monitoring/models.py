"""Typed domain models for validation monitoring."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class AlertLevel(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass(frozen=True, slots=True)
class SchemaDriftReport:
    missing_columns: tuple[str, ...]
    added_columns: tuple[str, ...]
    type_mismatches: tuple[tuple[str, str, str], ...]  # (column, expected_type, actual_type)
    missing_rate_exceeded: tuple[str, ...]
    is_drifted: bool


@dataclass(frozen=True, slots=True)
class PSIRecord:
    bucket: str
    expected_pct: Decimal
    actual_pct: Decimal
    psi_contribution: Decimal


@dataclass(frozen=True, slots=True)
class PSIReport:
    psi_value: Decimal
    level: AlertLevel
    records: tuple[PSIRecord, ...]


@dataclass(frozen=True, slots=True)
class StagingStabilityReport:
    stage_proportions: tuple[tuple[int, Decimal], ...]  # (stage, proportion)
    level: AlertLevel


@dataclass(frozen=True, slots=True)
class CalibrationAlertReport:
    metric_name: str
    baseline_value: Decimal
    actual_value: Decimal
    deviation: Decimal
    level: AlertLevel


@dataclass(frozen=True, slots=True)
class MacroScenarioDeviation:
    variable: str
    scenario_id: str
    deviation_pct: Decimal


@dataclass(frozen=True, slots=True)
class ScenarioMonitorReport:
    deviations: tuple[MacroScenarioDeviation, ...]
    level: AlertLevel
