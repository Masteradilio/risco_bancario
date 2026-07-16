from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from src.data.synthetic import (
    PopulationConfig,
    build_modeling_datasets,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)


@pytest.fixture(scope="module")
def datasets():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    macro = generate_macroeconomic_bundle(seed=91)
    return population, history, events, build_modeling_datasets(population, history, events, macro)


def test_pd_observation_dates_and_targets_are_point_in_time(datasets) -> None:
    _, _, events, modeling = datasets
    defaults = [item for item in events.defaults if not item.is_redefault]
    assert modeling.pd
    assert max(item.observation_date for item in modeling.pd) == date(2025, 12, 1)
    labeled = [item for item in modeling.pd if item.target_default_12m is not None]
    assert max(item.observation_date for item in labeled) == date(2024, 12, 1)
    for row in labeled:
        expected = int(
            any(
                row.observation_date
                < item.default_date
                <= date(
                    row.observation_date.year + 1,
                    row.observation_date.month,
                    1,
                )
                and item.contract_id == row.contract_id
                for item in defaults
            )
        )
        assert row.target_default_12m == expected


def test_monthly_hazard_is_subset_of_default_target(datasets) -> None:
    modeling = datasets[-1]
    assert any(item.target_hazard_1m for item in modeling.pd)
    assert all(
        item.target_hazard_1m <= item.target_default_12m
        for item in modeling.pd
        if item.target_hazard_1m is not None and item.target_default_12m is not None
    )


def test_lgd_dataset_reconciles_realized_net_recoveries(datasets) -> None:
    _, _, _, modeling = datasets
    assert modeling.lgd
    assert all(
        item.target_realized_lgd_undiscounted
        == max(
            Decimal("0"),
            (Decimal("1") - item.recovery_net_total / item.exposure_at_default).quantize(
                Decimal("0.00000001")
            ),
        )
        for item in modeling.lgd
    )


def test_ead_dataset_uses_only_pre_default_observations(datasets) -> None:
    modeling = datasets[-1]
    assert modeling.ead
    assert any(item.target_ccf is not None for item in modeling.ead)
    assert all(item.observation_date < item.default_date for item in modeling.ead)
    assert all(
        item.target_ccf is None or Decimal("0") <= item.target_ccf <= Decimal("1")
        for item in modeling.ead
    )


def test_sicr_dataset_has_future_deterioration_targets(datasets) -> None:
    modeling = datasets[-1]
    assert len(modeling.sicr) == len(modeling.pd)
    assert {item.target_sicr_12m for item in modeling.sicr} == {0, 1, None}


def test_time_splits_are_disjoint_and_ordered(datasets) -> None:
    modeling = datasets[-1]
    dates_by_split: dict[str, list[date]] = {}
    for item in modeling.pd:
        dates_by_split.setdefault(item.split, []).append(item.observation_date)
    assert set(dates_by_split) == {
        "train",
        "validation",
        "calibration",
        "oot",
        "backtesting",
    }
    order = ["train", "validation", "calibration", "oot", "backtesting"]
    assert all(
        max(dates_by_split[left]) < min(dates_by_split[right])
        for left, right in zip(order[:-1], order[1:], strict=True)
    )
    assert all(
        (min(dates_by_split[right]).year - max(dates_by_split[left]).year) * 12
        + min(dates_by_split[right]).month
        - max(dates_by_split[left]).month
        >= 12
        for left, right in zip(order[:-2], order[1:-1], strict=True)
    )


def test_modeling_feature_columns_exclude_latents_and_future_events(datasets) -> None:
    tables = datasets[-1].as_tables()
    for rows in tables.values():
        for row in rows:
            assert not any(key.startswith("_latent") for key in row)
    for table_name in ("pd_modeling", "sicr_modeling"):
        for row in tables[table_name]:
            assert "default_date" not in row
            assert "recovery_net_total" not in row
            assert "target_exposure_at_default" not in row


def test_observations_after_the_modeling_cutoff_are_ignored(datasets) -> None:
    population, history, events, _ = datasets
    macro = generate_macroeconomic_bundle(seed=91)
    eligible = next(
        item
        for item in history.snapshots
        if not next(
            contract
            for contract in population.contracts
            if contract.contract_id == item.contract_id
        ).acquired_credit_impaired
    )
    future = replace(eligible, reference_date=date(2026, 1, 1))
    extended_history = replace(history, snapshots=(*history.snapshots, future))

    result = build_modeling_datasets(population, extended_history, events, macro)

    assert all(item.observation_date <= date(2025, 12, 1) for item in result.pd)
