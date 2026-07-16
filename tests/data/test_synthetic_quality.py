from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from src.data.synthetic import (
    PopulationConfig,
    assess_synthetic_quality,
    build_modeling_datasets,
    detect_future_features,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)


@pytest.fixture(scope="module")
def bundle():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    macro = generate_macroeconomic_bundle(seed=91)
    modeling = build_modeling_datasets(population, history, events, macro)
    return population, history, events, macro, modeling


def test_valid_synthetic_bundle_passes_integrity_and_temporal_checks(bundle) -> None:
    report = assess_synthetic_quality(*bundle)
    assert report.passed
    assert not report.issues


def test_orphan_snapshot_is_detected(bundle) -> None:
    population, history, events, macro, modeling = bundle
    broken = replace(
        history,
        snapshots=(replace(history.snapshots[0], contract_id="UNKNOWN"), *history.snapshots[1:]),
    )
    report = assess_synthetic_quality(population, broken, events, macro, modeling)
    assert "orphan_snapshot" in {item.code for item in report.issues}


def test_recovery_before_default_is_detected(bundle) -> None:
    population, history, events, macro, modeling = bundle
    default = next(item for item in events.defaults if not item.is_redefault)
    recovery_index = next(
        index
        for index, item in enumerate(events.recoveries)
        if item.default_id == default.default_id
    )
    recoveries = list(events.recoveries)
    recoveries[recovery_index] = replace(
        recoveries[recovery_index], recovery_date=default.default_date
    )
    broken = replace(events, recoveries=tuple(recoveries))
    report = assess_synthetic_quality(population, history, broken, macro, modeling)
    assert "recovery_before_default" in {item.code for item in report.issues}


def test_future_feature_detector_blocks_outcome_columns() -> None:
    assert detect_future_features(
        ["balance", "future_default", "target_default_12m", "recovery_net"]
    ) == ("future_default", "target_default_12m", "recovery_net")
    assert not detect_future_features(["balance", "days_past_due", "unemployment"])


def test_distribution_and_correlation_diagnostics_cover_pd_features(bundle) -> None:
    report = assess_synthetic_quality(*bundle)
    assert len(report.distributions) == 10
    assert len(report.correlations) == 10
    assert all(item.count == len(bundle[-1].pd) for item in report.distributions)
    assert all(-1 <= item.pearson <= 1 for item in report.correlations)
    assert all(item.feature != item.target for item in report.correlations)


def test_time_splits_include_real_oot_and_backtesting(bundle) -> None:
    modeling = bundle[-1]
    oot_dates = {item.observation_date for item in modeling.pd if item.split == "oot"}
    backtesting_dates = {
        item.observation_date for item in modeling.pd if item.split == "backtesting"
    }
    assert min(oot_dates) == date(2024, 1, 1)
    assert max(oot_dates) == date(2024, 12, 1)
    assert min(backtesting_dates) == date(2025, 1, 1)


def test_data_card_and_dictionary_document_limitations() -> None:
    card = Path("docs/data/DATA_CARD_SYNTHETIC_FACTORY.md").read_text(encoding="utf-8")
    dictionary = Path("docs/data/DATA_DICTIONARY.md").read_text(encoding="utf-8")
    assert "## Limitações" in card
    assert "não são dados reais" in card
    assert "target_default_12m" in dictionary
    assert "target_realized_lgd_undiscounted" in dictionary


def test_factory_covers_modeling_stage3_poci_and_reporting_sources(bundle) -> None:
    population, _, events, _, modeling = bundle
    assert modeling.pd and modeling.lgd and modeling.ead and modeling.sicr
    assert any(not item.is_redefault for item in events.defaults)
    assert any(item.acquired_credit_impaired for item in population.contracts)
    assert population.clients and population.contracts and modeling.pd


def test_quality_detects_orphan_defaults_and_references(bundle) -> None:
    population, history, events, macro, modeling = bundle
    orphan_default = replace(events.defaults[0], contract_id="UNKNOWN")
    broken_defaults = replace(events, defaults=(orphan_default, *events.defaults[1:]))
    report = assess_synthetic_quality(population, history, broken_defaults, macro, modeling)
    assert "orphan_default" in {item.code for item in report.issues}

    orphan_collection = replace(events.collections[0], default_id="UNKNOWN")
    broken_collections = replace(events, collections=(orphan_collection, *events.collections[1:]))
    report = assess_synthetic_quality(population, history, broken_collections, macro, modeling)
    assert "orphan_default_reference" in {item.code for item in report.issues}


def test_quality_detects_duplicate_and_unreconciled_event_records(bundle) -> None:
    population, history, events, macro, modeling = bundle
    duplicate_history = replace(history, snapshots=(*history.snapshots, history.snapshots[0]))
    report = assess_synthetic_quality(population, duplicate_history, events, macro, modeling)
    assert "duplicate_snapshot" in {item.code for item in report.issues}

    recovery = events.recoveries[0]
    broken_recovery = replace(recovery, net_amount=recovery.net_amount + 1)
    broken_events = replace(events, recoveries=(broken_recovery, *events.recoveries[1:]))
    report = assess_synthetic_quality(population, history, broken_events, macro, modeling)
    assert "recovery_not_reconciled" in {item.code for item in report.issues}

    cure = events.cures[0]
    default = next(item for item in events.defaults if item.default_id == cure.default_id)
    broken_cure = replace(cure, cure_date=default.default_date)
    broken_events = replace(events, cures=(broken_cure, *events.cures[1:]))
    report = assess_synthetic_quality(population, history, broken_events, macro, modeling)
    assert "cure_before_default" in {item.code for item in report.issues}


def test_quality_detects_modeling_horizon_target_and_split_failures(bundle) -> None:
    population, history, events, macro, modeling = bundle
    future = replace(modeling.pd[0], observation_date=date(2026, 1, 1))
    report = assess_synthetic_quality(
        population, history, events, macro, replace(modeling, pd=(future, *modeling.pd[1:]))
    )
    assert "observation_after_cutoff" in {item.code for item in report.issues}

    mature_index = next(
        index for index, row in enumerate(modeling.pd) if row.observation_date <= date(2024, 12, 1)
    )
    rows = list(modeling.pd)
    rows[mature_index] = replace(rows[mature_index], target_default_12m=None)
    report = assess_synthetic_quality(
        population, history, events, macro, replace(modeling, pd=tuple(rows))
    )
    assert "missing_mature_target" in {item.code for item in report.issues}

    future_index = next(
        index for index, row in enumerate(modeling.pd) if row.observation_date > date(2024, 12, 1)
    )
    rows = list(modeling.pd)
    rows[future_index] = replace(rows[future_index], target_default_12m=0)
    report = assess_synthetic_quality(
        population, history, events, macro, replace(modeling, pd=tuple(rows))
    )
    assert "premature_future_target" in {item.code for item in report.issues}

    incomplete_macro = replace(macro, observed=macro.observed[:-1])
    report = assess_synthetic_quality(population, history, events, incomplete_macro, modeling)
    assert "macro_history_incomplete" in {item.code for item in report.issues}

    missing_split = replace(modeling, pd=tuple(row for row in modeling.pd if row.split != "train"))
    report = assess_synthetic_quality(population, history, events, macro, missing_split)
    assert "missing_time_split" in {item.code for item in report.issues}
