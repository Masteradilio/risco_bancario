from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from src.domain.exceptions import DomainValidationError
from src.domain.scenarios import (
    ScenarioKind,
)
from src.validation.monitoring import (
    AlertLevel,
    calculate_psi,
    check_calibration,
    check_scenario_deviation,
    check_schema_drift,
    check_staging_stability,
)


def test_calculate_psi_green() -> None:
    np.random.seed(42)
    reference = np.random.beta(2, 5, 1000)
    actual = np.random.beta(2, 5, 1000)
    report = calculate_psi(reference, actual)
    assert report.level == AlertLevel.GREEN
    assert report.psi_value >= 0
    assert len(report.records) == 10


def test_calculate_psi_yellow() -> None:
    np.random.seed(42)
    reference = np.random.beta(2, 5, 1000)
    actual = np.random.beta(2.1, 4.9, 1000)
    report = calculate_psi(reference, actual)
    assert report.level in (AlertLevel.GREEN, AlertLevel.YELLOW)


def test_calculate_psi_red() -> None:
    np.random.seed(42)
    reference = np.random.beta(2, 5, 1000)
    actual = np.random.beta(5, 2, 1000)  # Heavy drift
    report = calculate_psi(reference, actual)
    assert report.level == AlertLevel.RED


def test_calculate_psi_invalid() -> None:
    with pytest.raises(DomainValidationError, match="non-empty"):
        calculate_psi(np.array([]), np.array([1.0]))
    with pytest.raises(DomainValidationError, match="at least 2 buckets"):
        calculate_psi(np.array([1.0, 2.0]), np.array([1.0, 2.0]), num_buckets=1)


def test_check_schema_drift_no_drift() -> None:
    ref = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    act = pd.DataFrame({"col1": [3, 4], "col2": ["c", "d"]})
    report = check_schema_drift(ref, act)
    assert not report.is_drifted
    assert report.missing_columns == ()
    assert report.added_columns == ()
    assert report.type_mismatches == ()


def test_check_schema_drift_with_drift() -> None:
    ref = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    act = pd.DataFrame(
        {"col1": [3.0, 4.0], "col3": ["c", "d"]}
    )  # col1 type changed, col2 missing, col3 added
    report = check_schema_drift(ref, act)
    assert report.is_drifted
    assert "col2" in report.missing_columns
    assert "col3" in report.added_columns
    assert any(col == "col1" for col, _, _ in report.type_mismatches)


def test_check_schema_drift_missing_rate() -> None:
    ref = pd.DataFrame({"col1": [1, 2]})
    act = pd.DataFrame({"col1": [1, None, None, None]})  # 75% missing
    report = check_schema_drift(ref, act, max_missing_rate=0.20)
    assert report.is_drifted
    assert "col1" in report.missing_rate_exceeded


def test_check_calibration() -> None:
    green = check_calibration("Gini", Decimal("0.60"), Decimal("0.61"))
    assert green.level == AlertLevel.GREEN
    assert green.deviation == Decimal("0.01")

    yellow = check_calibration("Gini", Decimal("0.60"), Decimal("0.54"))
    assert yellow.level == AlertLevel.YELLOW

    red = check_calibration("Gini", Decimal("0.60"), Decimal("0.49"))
    assert red.level == AlertLevel.RED


def test_check_staging_stability() -> None:
    baseline = {1: Decimal("0.80"), 2: Decimal("0.15"), 3: Decimal("0.05")}
    actual = (1, 1, 1, 1, 1, 1, 1, 1, 2, 3)  # 80%, 10%, 10%
    report = check_staging_stability(actual, baseline)
    assert report.level == AlertLevel.GREEN

    # Heavy shift
    bad_actual = (1, 2, 2, 2, 2, 2, 3, 3, 3, 3)  # 10%, 50%, 40%
    report_bad = check_staging_stability(bad_actual, baseline)
    assert report_bad.level in (AlertLevel.YELLOW, AlertLevel.RED)


def test_check_staging_stability_invalid() -> None:
    with pytest.raises(DomainValidationError, match="non-empty"):
        check_staging_stability((), {1: Decimal("1.0")})


def test_check_scenario_deviation() -> None:
    from src.application.services import load_scenario_set

    scenario_set = load_scenario_set(seed=91)
    base_trajectory = next(
        item for item in scenario_set.trajectories if item.kind == ScenarioKind.BASE
    )
    gdp_var = next(
        item for item in base_trajectory.periods[0].variables if item.name == "gdp_growth"
    )
    expected_gdp = gdp_var.value

    green = check_scenario_deviation(
        {"gdp_growth": expected_gdp}, scenario_set, threshold=Decimal("2.0")
    )
    assert green.level == AlertLevel.GREEN
    assert green.deviations == ()

    red = check_scenario_deviation({"gdp_growth": expected_gdp * Decimal("5")}, scenario_set)
    assert red.level == AlertLevel.RED
    assert len(red.deviations) >= 1
    assert red.deviations[0].variable == "gdp_growth"
