import pytest

from src.data.synthetic import (
    PopulationConfig,
    build_modeling_datasets,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)
from src.models.sicr import validate_sicr_staging


@pytest.fixture(scope="module")
def report():
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    modeling = build_modeling_datasets(
        population, history, events, generate_macroeconomic_bundle(91)
    )
    return validate_sicr_staging(modeling)


def test_future_event_confusion_reconciles_oot_population(report) -> None:
    confusion = report.definition_comparison.relative_confusion
    assert (
        confusion.true_positive
        + confusion.false_positive
        + confusion.true_negative
        + confusion.false_negative
        == report.sample_count
    )
    assert confusion.true_positive + confusion.false_negative == report.event_count
    assert isinstance(report.false_positive_contracts, tuple)
    assert report.false_negative_contracts


def test_stability_index_is_reported_by_temporal_period(report) -> None:
    assert {item.period for item in report.stability} == {
        "train",
        "validation",
        "calibration",
        "oot",
    }
    train = next(item for item in report.stability if item.period == "train")
    assert train.population_stability_index == pytest.approx(0)
    assert all(item.population_stability_index >= 0 for item in report.stability)


def test_stage_migration_rates_reconcile_by_origin_stage(report) -> None:
    assert report.migrations
    for stage in {item.from_stage for item in report.migrations}:
        assert sum(
            item.rate_from_origin for item in report.migrations if item.from_stage == stage
        ) == pytest.approx(1)


def test_threshold_sensitivity_covers_downgrade_and_dpd_variants(report) -> None:
    settings = {(item.downgrade_notches, item.days_past_due) for item in report.sensitivity}
    assert settings == {(1, 31), (2, 15), (2, 31), (2, 60), (3, 31)}
    assert len({item.predicted_stage2_rate for item in report.sensitivity}) > 1


def test_relative_and_absolute_definitions_are_compared(report) -> None:
    comparison = report.definition_comparison
    assert 0 <= comparison.agreement_rate <= 1
    assert comparison.relative_confusion != comparison.absolute_confusion


def test_validation_remains_proxy_and_not_approved(report) -> None:
    assert report.evaluation_split == "oot"
    assert report.evidence_scope == "synthetic_proxy_without_approved_pd"
    assert report.approval_status == "not_approved"
