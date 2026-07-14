from datetime import date
from decimal import Decimal

from src.data.synthetic import PopulationConfig, generate_monthly_history, generate_population


def history():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    return generate_monthly_history(population)


def test_history_is_reproducible_and_spans_at_least_eight_years() -> None:
    first = history()
    second = history()
    assert first == second
    dates = [item.reference_date for item in first.snapshots]
    assert (max(dates).year - min(dates).year) >= 8
    assert all(item.reference_date.day == 1 for item in first.snapshots)


def test_snapshots_have_balances_limits_utilization_arrears_and_rating() -> None:
    result = history()
    assert result.snapshots
    assert all(item.balance >= 0 and item.credit_limit >= item.balance for item in result.snapshots)
    assert all(Decimal("0") <= item.utilization <= Decimal("1") for item in result.snapshots)
    assert any(item.days_past_due > 0 for item in result.snapshots)
    assert len({item.rating for item in result.snapshots}) >= 5


def test_each_contract_has_monotonic_months_and_stable_cohort() -> None:
    result = history()
    for contract_id in {item.contract_id for item in result.snapshots}:
        rows = [item for item in result.snapshots if item.contract_id == contract_id]
        assert rows == sorted(rows, key=lambda item: item.reference_date)
        assert len({item.origination_cohort for item in rows}) == 1
        assert [item.months_on_book for item in rows] == sorted(
            item.months_on_book for item in rows
        )


def test_observable_risk_changes_before_severe_delinquency() -> None:
    result = history()
    severe = [item for item in result.snapshots if item.days_past_due >= 90]
    assert severe
    for event in severe[:20]:
        prior = [
            item
            for item in result.snapshots
            if item.contract_id == event.contract_id and item.reference_date < event.reference_date
        ]
        assert prior
        assert max(item.behavior_score for item in prior[-3:]) >= Decimal("0.45")


def test_modifications_extend_maturity_and_are_reflected_in_snapshots() -> None:
    result = history()
    assert result.modifications
    for modification in result.modifications:
        assert modification.new_maturity_date > modification.old_maturity_date
        assert any(
            item.contract_id == modification.contract_id
            and item.reference_date >= modification.modification_date
            and item.modified
            for item in result.snapshots
        )


def test_public_history_has_no_future_target_default_or_latent_columns() -> None:
    tables = history().as_tables()
    forbidden = {"target", "default_date", "future_default", "_latent"}
    assert all(
        not any(key == item or key.startswith("_latent") for item in forbidden)
        for rows in tables.values()
        for row in rows
        for key in row
    )


def test_custom_window_is_respected() -> None:
    population = generate_population(PopulationConfig(seed=7, clients=8, contracts_per_client=1))
    result = generate_monthly_history(
        population, start_date=date(2020, 1, 1), end_date=date(2021, 12, 1)
    )
    assert all(
        date(2020, 1, 1) <= item.reference_date <= date(2021, 12, 1) for item in result.snapshots
    )
