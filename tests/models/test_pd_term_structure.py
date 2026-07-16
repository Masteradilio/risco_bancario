from datetime import date

import pytest

from src.domain.exceptions import DomainValidationError
from src.models.pd import project_pd_term_structure
from src.models.pd.term_structure import (
    monthly_hazards_from_horizon_pd,
    remaining_contract_months,
)


def test_flat_curve_reconciles_hazard_survival_and_12m_pd() -> None:
    curve = project_pd_term_structure("CTR-1", date(2026, 1, 15), date(2028, 1, 15), 0.12)
    assert curve.remaining_months == 24
    assert curve.pd_12m == pytest.approx(0.12)
    assert sum(item.marginal_pd for item in curve.points[:12]) == pytest.approx(0.12)
    assert all(item.survival == pytest.approx(1 - item.cumulative_pd) for item in curve.points)


def test_lifetime_pd_uses_actual_contractual_term() -> None:
    short = project_pd_term_structure("SHORT", date(2026, 1, 1), date(2026, 7, 1), 0.08)
    long = project_pd_term_structure("LONG", date(2026, 1, 1), date(2028, 1, 1), 0.08)
    assert short.remaining_months == 6
    assert short.pd_12m == pytest.approx(0.08)
    assert short.lifetime_pd == pytest.approx(0.08)
    assert long.remaining_months == 24
    assert long.lifetime_pd > long.pd_12m


def test_non_flat_term_shape_preserves_horizon_pd() -> None:
    multipliers = tuple(float(month) for month in range(1, 19))
    curve = project_pd_term_structure(
        "SHAPED",
        date(2026, 1, 1),
        date(2027, 7, 1),
        0.2,
        term_multipliers=multipliers,
    )
    assert curve.pd_12m == pytest.approx(0.2)
    assert curve.points[0].hazard < curve.points[-1].hazard


def test_curve_is_bounded_and_cumulative_pd_is_monotonic() -> None:
    curve = project_pd_term_structure("BOUNDS", date(2026, 1, 31), date(2027, 4, 30), 0.35)
    cumulative = [item.cumulative_pd for item in curve.points]
    survival = [item.survival for item in curve.points]
    assert all(0 <= item.hazard < 1 for item in curve.points)
    assert all(0 <= value <= 1 for value in cumulative + survival)
    assert cumulative == sorted(cumulative)
    assert survival == sorted(survival, reverse=True)
    assert curve.points[-1].period_end == curve.maturity_date


@pytest.mark.parametrize(
    ("maturity", "pd", "multipliers"),
    [
        (date(2026, 1, 1), 0.1, None),
        (date(2027, 1, 1), 1.0, None),
        (date(2027, 1, 1), 0.1, (1.0,)),
        (date(2027, 1, 1), 0.1, (0.0,) * 12),
    ],
)
def test_invalid_curve_inputs_fail_closed(maturity, pd, multipliers) -> None:
    with pytest.raises(DomainValidationError):
        project_pd_term_structure(
            "INVALID",
            date(2026, 1, 1),
            maturity,
            pd,
            term_multipliers=multipliers,
        )


def test_term_structure_calendar_rounding_and_direct_boundaries() -> None:
    assert remaining_contract_months(date(2026, 1, 15), date(2026, 1, 16)) == 1
    with pytest.raises(DomainValidationError, match="remaining_months"):
        monthly_hazards_from_horizon_pd(0.1, 0)
    with pytest.raises(DomainValidationError, match="contract_id"):
        project_pd_term_structure(" ", date(2026, 1, 1), date(2027, 1, 1), 0.1)
