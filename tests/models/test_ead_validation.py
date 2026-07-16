import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

from src.data.synthetic import (
    PopulationConfig,
    generate_credit_events,
    generate_monthly_history,
    generate_population,
)
from src.domain.exceptions import DomainValidationError
from src.models.ead import (
    build_amortized_default_ead_dataset,
    build_revolving_ccf_dataset,
    fit_revolving_ccf_model,
    load_amortized_ead_policy,
    load_ead_validation_policy,
    load_off_balance_ead_policy,
    load_revolving_ccf_policy,
    validate_ead_models,
)
from src.models.ead.validation import _metrics


@pytest.fixture(scope="module")
def validation_bundle():
    ccf_policy = load_revolving_ccf_policy(Path("config/ccf_policy/2026.07.1.json"))
    development = generate_population(
        PopulationConfig(
            seed=ccf_policy.development_seed,
            clients=ccf_policy.development_clients,
            contracts_per_client=ccf_policy.development_contracts_per_client,
        )
    )
    development_history = generate_monthly_history(development)
    development_events = generate_credit_events(development, development_history)
    ccf_dataset = build_revolving_ccf_dataset(
        development, development_history, development_events, ccf_policy
    )
    ccf_model = fit_revolving_ccf_model(ccf_dataset)

    acceptance = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    acceptance_history = generate_monthly_history(acceptance)
    acceptance_events = generate_credit_events(acceptance, acceptance_history)
    amortized = build_amortized_default_ead_dataset(
        acceptance,
        acceptance_history,
        acceptance_events,
        load_amortized_ead_policy(Path("config/ead_policy/2026.07.1.json")),
    )
    off_balance = load_off_balance_ead_policy(Path("config/off_balance_ead_policy/2026.07.1.json"))
    validation_policy = load_ead_validation_policy(Path("config/ead_validation/2026.07.1.json"))
    report = validate_ead_models(amortized, ccf_dataset, ccf_model, off_balance, validation_policy)
    return amortized, ccf_dataset, ccf_model, off_balance, validation_policy, report


def test_amortized_ead_reconciles_predicted_and_observed(validation_bundle) -> None:
    report = validation_bundle[-1]

    assert report.amortized_metrics.observations == 24
    assert report.amortized_metrics.mean_absolute_error == 0
    assert report.amortized_metrics.root_mean_squared_error == 0
    assert report.amortized_metrics.mean_actual == report.amortized_metrics.mean_prediction


def test_ccf_holdout_metrics_use_only_reserved_temporal_rows(validation_bundle) -> None:
    report = validation_bundle[-1]

    assert report.ccf_metrics.observations == 4
    assert report.ccf_metrics.mean_actual == pytest.approx(0.044671705)
    assert report.ccf_metrics.mean_prediction == pytest.approx(0.0376650131)
    assert report.ccf_metrics.mean_absolute_error == pytest.approx(0.0397230481)
    assert report.ccf_metrics.root_mean_squared_error == pytest.approx(0.0548936585)


def test_segment_errors_cover_product_and_horizon_without_pooling(validation_bundle) -> None:
    report = validation_bundle[-1]
    amortized = [item for item in report.segment_errors if item.component == "amortized_ead"]
    ccf = [item for item in report.segment_errors if item.component == "revolving_ccf"]

    assert {item.segment for item in amortized} == {
        "acquired_distressed",
        "mortgage",
        "vehicle_finance",
    }
    assert sum(item.observations for item in amortized) == 24
    assert {item.segment for item in ccf} == {
        "credit_card:3m",
        "credit_card:6m",
        "overdraft:3m",
        "overdraft:6m",
    }
    assert all(item.observations == 1 for item in ccf)


def test_temporal_stability_keeps_years_separate(validation_bundle) -> None:
    report = validation_bundle[-1]
    ccf = [item for item in report.temporal_stability if item.component == "revolving_ccf"]
    amortized = [item for item in report.temporal_stability if item.component == "amortized_ead"]

    assert {item.year for item in ccf} == {2022, 2023}
    assert sum(item.observations for item in ccf) == 4
    assert len({item.year for item in amortized}) >= 5
    assert all(item.mean_absolute_error == 0 for item in amortized)


def test_utilization_horizon_and_limit_sensitivities_are_responsive(
    validation_bundle,
) -> None:
    checks = validation_bundle[-1].sensitivity_checks

    assert {item.name for item in checks} == {
        "ccf_utilization",
        "ccf_horizon",
        "off_balance_current_limit",
    }
    assert all(item.responsive for item in checks)
    limit = next(item for item in checks if item.name == "off_balance_current_limit")
    assert limit.expected_order_passed is True
    assert (
        limit.lower_input_prediction < limit.base_input_prediction < limit.higher_input_prediction
    )


def test_validation_fails_approval_for_volume_coverage_and_evidence(validation_bundle) -> None:
    report = validation_bundle[-1]

    assert report.approval_status == "not_approved"
    assert {
        "ccf_validation_sample_below_minimum",
        "segment_sample_below_minimum",
        "ccf_temporal_coverage_below_minimum",
        "no_limit_change_in_validation",
        "ccf_model_not_approved",
        "off_balance_parameters_not_estimated",
        "validation_evidence_not_institutionally_validated",
    } <= set(report.blockers)
    assert "ccf_mae_above_limit" not in report.blockers
    assert "ccf_rmse_above_limit" not in report.blockers


def test_policy_lineage_and_empty_holdout_fail_closed(validation_bundle) -> None:
    amortized, dataset, model, off_balance, policy, report = validation_bundle

    assert report.policy_version == "2026.07.1"
    assert report.policy_sha256 == policy.sha256
    train_only = replace(
        dataset,
        rows=tuple(replace(item, split="train") for item in dataset.rows),
    )
    with pytest.raises(DomainValidationError, match="empty"):
        validate_ead_models(amortized, train_only, model, off_balance, policy)


def test_ead_validation_policy_and_vectors_fail_closed(tmp_path: Path) -> None:
    source = Path("config/ead_validation/2026.07.1.json")
    document = json.loads(source.read_text(encoding="utf-8"))
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document | {"schema_version": "2.0.0"}), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="policy schema"):
        load_ead_validation_policy(path)
    document["maximum_ccf_mae"] = "-1"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="thresholds"):
        load_ead_validation_policy(path)
    with pytest.raises(DomainValidationError, match="empty or misaligned"):
        _metrics(np.asarray([]), np.asarray([]))


def test_ead_validation_emits_every_quantitative_blocker(validation_bundle) -> None:
    amortized, dataset, model, off_balance, policy, _ = validation_bundle
    strict = replace(
        policy,
        minimum_amortized_observations=10_000,
        maximum_amortized_mae=Decimal("-1"),
        maximum_ccf_mae=Decimal("-1"),
        maximum_ccf_rmse=Decimal("-1"),
        minimum_sensitivity_delta=Decimal("1000000"),
    )
    report = validate_ead_models(amortized, dataset, model, off_balance, strict)
    assert {
        "amortized_sample_below_minimum",
        "amortized_mae_above_limit",
        "ccf_mae_above_limit",
        "ccf_rmse_above_limit",
        "sensitivity_not_responsive",
    } <= set(report.blockers)


def test_ead_validation_can_clear_every_governance_blocker(validation_bundle) -> None:
    amortized, dataset, model, off_balance, policy, _ = validation_bundle
    lenient = replace(
        policy,
        minimum_amortized_observations=0,
        maximum_amortized_mae=Decimal("999"),
        minimum_ccf_validation_observations=0,
        maximum_ccf_mae=Decimal("999"),
        maximum_ccf_rmse=Decimal("999"),
        minimum_segment_observations=0,
        minimum_ccf_validation_years=0,
        require_limit_change_validation=False,
        minimum_sensitivity_delta=Decimal("0.00000001"),
        require_institutional_evidence=False,
        evidence_status="institutionally_validated",
    )
    approved_model = replace(model, status="approved")
    validated_off_balance = replace(off_balance, evidence_status="institutionally_validated")
    report = validate_ead_models(amortized, dataset, approved_model, validated_off_balance, lenient)
    assert report.blockers == ()
    assert report.approval_status == "approved"
