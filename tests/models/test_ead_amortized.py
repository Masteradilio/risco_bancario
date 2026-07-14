from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.data.synthetic import (
    PopulationConfig,
    generate_credit_events,
    generate_monthly_history,
    generate_population,
)
from src.domain.contracts import (
    AmortizationMethod,
    AmortizationTerms,
    ModificationRequest,
    apply_prepayment,
    modify_contract,
    project_amortized_schedule,
)
from src.domain.exceptions import DomainValidationError
from src.models.ead import (
    build_amortized_default_ead_dataset,
    calculate_amortized_ead,
    load_amortized_ead_policy,
)

POLICY_PATH = Path("config/ead_policy/2026.07.1.json")


def _terms(
    *,
    principal: Decimal = Decimal("1200"),
    term_months: int = 12,
    origination_date: date = date(2026, 1, 1),
) -> AmortizationTerms:
    return AmortizationTerms(
        "CTR-001",
        origination_date,
        principal,
        term_months,
        Decimal("0"),
        AmortizationMethod.PRICE,
    )


def test_uses_last_observable_period_opening_before_default() -> None:
    schedule = project_amortized_schedule(_terms())

    result = calculate_amortized_ead(
        schedule, date(2026, 5, 1), load_amortized_ead_policy(POLICY_PATH)
    )

    assert result.default_period_number == 3
    assert result.period_opening_balance == Decimal("1000.00")
    assert result.scheduled_principal == Decimal("100.00")
    assert result.ead_at_default == Decimal("1000.00")
    assert result.schedule_source == "original_schedule"


def test_partial_prepayment_replaces_original_balance_schedule() -> None:
    terms = _terms()
    schedule = project_amortized_schedule(terms)
    prepayment = apply_prepayment(terms, 2, Decimal("300"))

    result = calculate_amortized_ead(
        schedule,
        date(2026, 4, 1),
        load_amortized_ead_policy(POLICY_PATH),
        prepayments=(prepayment,),
    )

    assert result.total_prepayment_applied == Decimal("300.00")
    assert result.ead_at_default == Decimal("700.00")
    assert result.schedule_source == "prepayment_revised_schedule"
    assert result.adjustments_applied == ("prepayment_after_period_2",)


def test_total_prepayment_sets_later_ead_to_zero() -> None:
    terms = _terms()
    schedule = project_amortized_schedule(terms)
    prepayment = apply_prepayment(terms, 2, Decimal("5000"))

    result = calculate_amortized_ead(
        schedule,
        date(2026, 4, 1),
        load_amortized_ead_policy(POLICY_PATH),
        prepayments=(prepayment,),
    )

    assert result.total_prepayment_applied == Decimal("1000.00")
    assert result.ead_at_default == 0
    assert result.schedule_source == "fully_prepaid"


def test_modification_uses_revised_schedule_and_preserves_lineage() -> None:
    original = project_amortized_schedule(_terms())
    revised_terms = _terms(
        principal=original.periods[1].closing_balance,
        term_months=20,
        origination_date=date(2026, 3, 1),
    )
    modification = modify_contract(
        original, ModificationRequest(2, revised_terms, derecognize=False)
    )
    policy = load_amortized_ead_policy(POLICY_PATH)

    result = calculate_amortized_ead(
        original,
        date(2026, 4, 1),
        policy,
        modifications=(modification,),
    )

    assert result.ead_at_default == Decimal("1000.00")
    assert result.schedule_source == "modification_revised_schedule"
    assert result.adjustments_applied == ("modification",)
    assert result.policy_sha256 == policy.sha256


def test_adjustments_after_default_do_not_change_ead() -> None:
    terms = _terms()
    schedule = project_amortized_schedule(terms)
    future_prepayment = apply_prepayment(terms, 2, Decimal("300"))

    result = calculate_amortized_ead(
        schedule,
        date(2026, 2, 1),
        load_amortized_ead_policy(POLICY_PATH),
        prepayments=(future_prepayment,),
    )

    assert result.ead_at_default == Decimal("1200.00")
    assert result.adjustments_applied == ()


def test_default_before_origination_fails_and_after_maturity_is_zero() -> None:
    schedule = project_amortized_schedule(_terms())
    policy = load_amortized_ead_policy(POLICY_PATH)

    with pytest.raises(DomainValidationError, match="precedes"):
        calculate_amortized_ead(schedule, date(2025, 12, 1), policy)
    matured = calculate_amortized_ead(schedule, date(2027, 2, 1), policy)
    assert matured.ead_at_default == 0
    assert matured.schedule_source == "matured_schedule"


def test_synthetic_amortized_defaults_reconcile_exactly_to_schedule() -> None:
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    policy = load_amortized_ead_policy(POLICY_PATH)

    dataset = build_amortized_default_ead_dataset(population, history, events, policy)

    assert len(dataset.records) == 24
    assert all(item.absolute_error == 0 for item in dataset.records)
    assert sum(item.predefault_term_extension_observed for item in dataset.records) == 1
    assert {item.product_code for item in dataset.records} == {
        "acquired_distressed",
        "mortgage",
        "vehicle_finance",
    }
    assert {item.policy_sha256 for item in dataset.records} == {policy.sha256}
