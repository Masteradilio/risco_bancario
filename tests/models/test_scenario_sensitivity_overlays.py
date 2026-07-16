from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.application.services import load_scenario_set
from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.ecl.calculation import (
    BaselineRiskPeriod,
    TrajectoryShock,
    WeightSensitivityCase,
    load_scenario_sensitivity_policy,
    run_scenario_sensitivities,
)
from src.ecl.overlays import ManagementOverlay, apply_management_overlays, reverse_overlay
from src.models.forward_looking import load_macro_risk_policy


def _baseline() -> tuple[BaselineRiskPeriod, ...]:
    return tuple(
        BaselineRiskPeriod(date(2026, month, 1), "0.04", "0.45", "1000", "500", "0.40", "0.99")
        for month in range(1, 7)
    )


def _overlay(overlay_id: str = "OV-1", amount: str = "10") -> ManagementOverlay:
    return ManagementOverlay(
        overlay_id,
        amount,
        "Risco emergente não capturado pelo modelo",
        "comite.risco",
        datetime(2026, 6, 30, 15, tzinfo=UTC),
        date(2026, 7, 1),
        date(2026, 12, 31),
        "1.0.0",
    )


def test_sensitivity_policy_is_versioned_and_demonstrative() -> None:
    policy = load_scenario_sensitivity_policy()
    assert policy.policy_version == "2026.07.1"
    assert policy.evidence_status == "synthetic_demonstrative_only"
    assert len(policy.weight_cases) == 2
    assert len(policy.trajectory_shocks) == 2
    assert len(policy.sha256) == 64


def test_downside_weight_shifts_increase_probability_weighted_ecl() -> None:
    report = run_scenario_sensitivities(
        _baseline(),
        load_scenario_set(seed=91),
        "portfolio",
        load_macro_risk_policy(),
        load_scenario_sensitivity_policy(),
    )
    weight_results = [item for item in report.results if item.kind == "weight"]
    assert len(weight_results) == 2
    assert all(item.delta_from_base > 0 for item in weight_results)
    assert weight_results[1].probability_weighted_ecl > weight_results[0].probability_weighted_ecl


def test_adverse_trajectory_shocks_increase_ecl_and_stress_is_separate() -> None:
    report = run_scenario_sensitivities(
        _baseline(),
        load_scenario_set(seed=91),
        "portfolio",
        load_macro_risk_policy(),
        load_scenario_sensitivity_policy(),
    )
    trajectory_results = [item for item in report.results if item.kind == "trajectory"]
    assert all(item.delta_from_base > 0 for item in trajectory_results)
    assert report.stress_ecl > report.base_ecl
    assert report.stress_delta == report.stress_ecl - report.base_ecl


def test_invalid_sensitivity_inputs_are_rejected() -> None:
    with pytest.raises(DomainValidationError, match="requires upside"):
        WeightSensitivityCase("invalid-kinds", (("base", Decimal("1")),))
    with pytest.raises(DomainValidationError, match="sum to one"):
        WeightSensitivityCase(
            "invalid",
            (("upside", Decimal("0.10")), ("base", Decimal("0.50")), ("downside", Decimal("0.30"))),
        )
    shock = TrajectoryShock("bad", "missing", Decimal("1"), ("base",))
    policy = replace(load_scenario_sensitivity_policy(), trajectory_shocks=(shock,))
    with pytest.raises(DomainValidationError, match="variable not found"):
        run_scenario_sensitivities(
            _baseline(), load_scenario_set(seed=91), "portfolio", load_macro_risk_policy(), policy
        )
    with pytest.raises(DomainValidationError, match="unique scenario ids"):
        TrajectoryShock("empty", "gdp_growth", Decimal("1"), ())
    unknown = TrajectoryShock("unknown", "gdp_growth", Decimal("1"), ("unknown",))
    with pytest.raises(DomainValidationError, match="unknown scenario"):
        run_scenario_sensitivities(
            _baseline(),
            load_scenario_set(seed=91),
            "portfolio",
            load_macro_risk_policy(),
            replace(load_scenario_sensitivity_policy(), trajectory_shocks=(unknown,)),
        )


def test_active_overlays_are_applied_after_and_separate_from_economic_ecl() -> None:
    result = apply_management_overlays(
        "100", (_overlay("OV-1", "10"), _overlay("OV-2", "-5")), date(2026, 7, 14)
    )
    assert result.economic_ecl == Decimal("100.00")
    assert result.overlay_amount == Decimal("5.00")
    assert result.final_ecl == Decimal("105.00")
    assert result.applied_overlay_ids == ("OV-1", "OV-2")


def test_overlay_validity_and_reversal_are_auditable() -> None:
    overlay = _overlay()
    reversed_overlay = reverse_overlay(
        overlay,
        reversed_at=datetime(2026, 7, 20, 12, tzinfo=UTC),
        reversed_by="comite.risco",
        reason="Risco incorporado ao modelo",
    )
    assert apply_management_overlays(
        "100", (reversed_overlay,), date(2026, 7, 19)
    ).final_ecl == Decimal("110.00")
    after = apply_management_overlays("100", (reversed_overlay,), date(2026, 7, 20))
    assert after.final_ecl == Decimal("100.00")
    assert after.applied_overlay_ids == ()
    with pytest.raises(DomainValidationError, match="already reversed"):
        reverse_overlay(
            reversed_overlay,
            reversed_at=datetime(2026, 7, 21, tzinfo=UTC),
            reversed_by="comite.risco",
            reason="duplicado",
        )


def test_overlay_rejects_invalid_window_partial_reversal_and_duplicates() -> None:
    with pytest.raises(TemporalConsistencyError, match="effective_to"):
        replace(_overlay(), effective_to=date(2026, 6, 30))
    with pytest.raises(DomainValidationError, match="requires date"):
        replace(_overlay(), reversed_by="aprovador")
    overlay = _overlay()
    with pytest.raises(DomainValidationError, match="ids must be unique"):
        apply_management_overlays("100", (overlay, overlay), date(2026, 7, 14))
    with pytest.raises(TemporalConsistencyError, match="cannot precede"):
        replace(
            overlay,
            reversed_at=datetime(2026, 6, 30, 14, tzinfo=UTC),
            reversed_by="approver",
            reversal_reason="invalid",
        )
    assert not overlay.is_active(date(2027, 1, 1))
