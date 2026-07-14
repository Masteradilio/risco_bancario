from datetime import date
from decimal import Decimal

import pytest

from src.data.synthetic import (
    PopulationConfig,
    generate_credit_events,
    generate_monthly_history,
    generate_population,
)
from src.domain.exceptions import DomainValidationError
from src.models.lgd import build_lgd_workout_dataset


@pytest.fixture(scope="module")
def workout():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    dataset = build_lgd_workout_dataset(population, events, observation_end_date=date(2025, 12, 1))
    return population, events, dataset


def test_every_observed_default_has_one_workout_record(workout) -> None:
    _, events, dataset = workout
    expected = [item for item in events.defaults if item.default_date <= date(2025, 12, 1)]
    assert len(dataset.records) == len(expected)
    assert len({item.default_id for item in dataset.records}) == len(dataset.records)
    assert any(item.is_redefault for item in dataset.records)


def test_default_cohorts_are_quarterly_and_deterministic(workout) -> None:
    _, _, dataset = workout
    assert all(
        item.default_cohort.startswith(str(item.default_date.year)) for item in dataset.records
    )
    assert all(item.default_cohort[-2:] in {"Q1", "Q2", "Q3", "Q4"} for item in dataset.records)


def test_recovery_gross_cost_and_net_totals_reconcile(workout) -> None:
    _, _, dataset = workout
    assert any(item.cashflows for item in dataset.records)
    for record in dataset.records:
        assert record.gross_recovery_total == sum(
            (item.gross_amount for item in record.cashflows), Decimal("0")
        )
        assert record.recovery_cost_total == sum(
            (item.cost_amount for item in record.cashflows), Decimal("0")
        )
        assert record.net_recovery_total == record.gross_recovery_total - record.recovery_cost_total


def test_collateral_cure_and_writeoff_evidence_are_linked(workout) -> None:
    _, _, dataset = workout
    assert any(item.collateral_type is not None for item in dataset.records)
    assert any(item.cure_date is not None for item in dataset.records)
    assert any(item.writeoff_date is not None for item in dataset.records)
    assert all(
        item.collateral_appraised_value >= 0
        and Decimal("0") <= item.collateral_enforceable_share <= Decimal("1")
        for item in dataset.records
    )


def test_workout_window_and_censoring_respect_observation_cutoff(workout) -> None:
    _, _, dataset = workout
    assert dataset.workout_window_months == 24
    assert any(item.is_censored for item in dataset.records)
    assert any(not item.is_censored for item in dataset.records)
    for record in dataset.records:
        cutoff = min(record.workout_end_date, record.observation_end_date)
        assert all(flow.recovery_date <= cutoff for flow in record.cashflows)
        assert record.is_censored == (record.observation_end_date < record.workout_end_date)


def test_invalid_workout_window_fails_closed(workout) -> None:
    population, events, _ = workout
    with pytest.raises(DomainValidationError, match="positive"):
        build_lgd_workout_dataset(
            population,
            events,
            observation_end_date=date(2025, 12, 1),
            workout_window_months=0,
        )
