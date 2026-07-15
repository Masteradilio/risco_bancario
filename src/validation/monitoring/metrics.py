"""Operational and statistical monitoring metric calculations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import ScenarioSet
from .models import (
    AlertLevel,
    CalibrationAlertReport,
    MacroScenarioDeviation,
    PSIRecord,
    PSIReport,
    ScenarioMonitorReport,
    SchemaDriftReport,
    StagingStabilityReport,
)


def calculate_psi(
    reference: np.ndarray[Any, Any],
    actual: np.ndarray[Any, Any],
    num_buckets: int = 10,
    yellow_threshold: Decimal = Decimal("0.10"),
    red_threshold: Decimal = Decimal("0.25"),
) -> PSIReport:
    """Calculate the Population Stability Index between reference and actual distributions."""
    if len(reference) == 0 or len(actual) == 0:
        raise DomainValidationError(
            "PSI calculation requires non-empty reference and actual arrays"
        )
    if num_buckets < 2:
        raise DomainValidationError("PSI calculation requires at least 2 buckets")

    # Percentiles based on reference
    percentiles = np.percentile(reference, np.linspace(0, 100, num_buckets + 1))

    # Histogram counts
    ref_counts, _ = np.histogram(reference, bins=percentiles)
    act_counts, _ = np.histogram(actual, bins=percentiles)

    ref_total = ref_counts.sum()
    act_total = act_counts.sum()

    ref_props = ref_counts / ref_total if ref_total > 0 else np.zeros_like(ref_counts, dtype=float)
    act_props = act_counts / act_total if act_total > 0 else np.zeros_like(act_counts, dtype=float)

    # Clip to avoid log(0) or division by zero
    ref_props = np.clip(ref_props, 1e-10, 1.0)
    act_props = np.clip(act_props, 1e-10, 1.0)

    psi_contribs = (act_props - ref_props) * np.log(act_props / ref_props)
    psi_value = Decimal(str(float(psi_contribs.sum())))

    records = []
    for i in range(len(psi_contribs)):
        bucket_range = f"{percentiles[i]:.4f} - {percentiles[i+1]:.4f}"
        records.append(
            PSIRecord(
                bucket=bucket_range,
                expected_pct=Decimal(str(float(ref_props[i]))),
                actual_pct=Decimal(str(float(act_props[i]))),
                psi_contribution=Decimal(str(float(psi_contribs[i]))),
            )
        )

    if psi_value >= red_threshold:
        level = AlertLevel.RED
    elif psi_value >= yellow_threshold:
        level = AlertLevel.YELLOW
    else:
        level = AlertLevel.GREEN

    return PSIReport(psi_value, level, tuple(records))


def check_schema_drift(
    reference: pd.DataFrame,
    actual: pd.DataFrame,
    max_missing_rate: float = 0.05,
) -> SchemaDriftReport:
    """Analyze schema changes and missing value rates between datasets."""
    ref_cols = set(reference.columns)
    act_cols = set(actual.columns)

    missing_cols = tuple(sorted(ref_cols - act_cols))
    added_cols = tuple(sorted(act_cols - ref_cols))

    type_mismatches = []
    for col in ref_cols & act_cols:
        ref_type = str(reference[col].dtype)
        act_type = str(actual[col].dtype)
        if ref_type != act_type:
            type_mismatches.append((col, ref_type, act_type))

    # Check missing rate on columns
    exceeded = []
    for col in act_cols:
        missing_rate = actual[col].isnull().mean()
        if missing_rate > max_missing_rate:
            exceeded.append(col)

    is_drifted = len(missing_cols) > 0 or len(type_mismatches) > 0 or len(exceeded) > 0

    return SchemaDriftReport(
        missing_columns=missing_cols,
        added_columns=added_cols,
        type_mismatches=tuple(sorted(type_mismatches)),
        missing_rate_exceeded=tuple(sorted(exceeded)),
        is_drifted=is_drifted,
    )


def check_calibration(
    metric_name: str,
    baseline_value: Decimal,
    actual_value: Decimal,
    yellow_threshold: Decimal = Decimal("0.05"),
    red_threshold: Decimal = Decimal("0.10"),
) -> CalibrationAlertReport:
    """Check performance metric deviation from baseline calibration."""
    deviation = abs(actual_value - baseline_value)
    if deviation >= red_threshold:
        level = AlertLevel.RED
    elif deviation >= yellow_threshold:
        level = AlertLevel.YELLOW
    else:
        level = AlertLevel.GREEN

    return CalibrationAlertReport(metric_name, baseline_value, actual_value, deviation, level)


def check_staging_stability(
    actual_stages: tuple[int, ...],
    baseline_proportions: dict[int, Decimal],
    threshold: Decimal = Decimal("0.10"),
) -> StagingStabilityReport:
    """Analyze staging distribution shift against baseline proportions."""
    if not actual_stages:
        raise DomainValidationError(
            "Staging stability calculation requires non-empty actual stages"
        )
    total = Decimal(len(actual_stages))

    proportions = {}
    for stage in (1, 2, 3):
        count = sum(1 for item in actual_stages if item == stage)
        proportions[stage] = Decimal(count) / total

    # Check deviation from baseline
    max_deviation = Decimal("0")
    for stage, baseline_prop in baseline_proportions.items():
        actual_prop = proportions.get(stage, Decimal("0"))
        deviation = abs(actual_prop - baseline_prop)
        if deviation > max_deviation:
            max_deviation = deviation

    level = AlertLevel.GREEN
    if max_deviation >= threshold:
        level = AlertLevel.YELLOW
    if max_deviation >= threshold * 2:
        level = AlertLevel.RED

    prop_tuples = tuple((stage, proportions[stage]) for stage in sorted(proportions))
    return StagingStabilityReport(prop_tuples, level)


def check_scenario_deviation(
    observed_values: dict[str, Decimal],
    scenario_set: ScenarioSet,
    threshold: Decimal = Decimal("0.15"),
) -> ScenarioMonitorReport:
    """Monitor deviation between observed macroeconomic variables and predicted trajectories."""
    deviations = []
    for trajectory in scenario_set.trajectories:
        latest_point = trajectory.periods[0]
        for var in latest_point.variables:
            observed = observed_values.get(var.name)
            if observed is not None:
                expected = Decimal(str(var.value))
                if expected != 0:
                    dev = abs(observed - expected) / abs(expected)
                    if dev >= threshold:
                        deviations.append(
                            MacroScenarioDeviation(var.name, trajectory.scenario_id, dev)
                        )

    level = AlertLevel.GREEN
    if len(deviations) > 0:
        level = AlertLevel.YELLOW
    if any(item.deviation_pct >= threshold * 2 for item in deviations):
        level = AlertLevel.RED

    return ScenarioMonitorReport(tuple(deviations), level)
