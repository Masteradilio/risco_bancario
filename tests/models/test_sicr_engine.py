from datetime import date
from pathlib import Path

import pytest

from src.domain.contracts import Contract
from src.models.sicr import (
    SICRAssessmentInput,
    assess_sicr,
    create_origination_baseline,
    load_sicr_policy,
)

POLICY_PATH = Path("config/sicr_policy/2026.07.1.json")


@pytest.fixture(scope="module")
def policy():
    return load_sicr_policy(POLICY_PATH)


@pytest.fixture(scope="module")
def baseline():
    contract = Contract(
        "CT-SICR",
        "CL-1",
        "CP-1",
        "personal_loan",
        date(2026, 1, 1),
        date(2027, 1, 1),
        "10000",
    )
    return create_origination_baseline(
        contract,
        "0.01",
        "A2",
        model_name="model",
        model_version="1",
        policy_version="2026.07.1",
        policy_sha256="a" * 64,
    )


def assess(baseline, policy, **overrides):
    values = {
        "baseline": baseline,
        "reference_date": date(2026, 7, 1),
        "current_lifetime_pd": "0.011",
        "current_rating": "A2",
    }
    values.update(overrides)
    return assess_sicr(SICRAssessmentInput(**values), policy)


def test_absolute_and_relative_lifetime_pd_changes_are_reported(baseline, policy) -> None:
    result = assess(
        baseline,
        policy,
        current_lifetime_pd="0.08",
        apply_low_credit_risk_exemption=False,
    )
    assert result.is_sicr
    assert result.absolute_change >= policy.absolute_lifetime_pd_increase
    assert result.relative_ratio is not None
    assert result.relative_ratio >= policy.relative_lifetime_pd_ratio
    assert set(result.active_triggers) == {
        "absolute_lifetime_pd_increase",
        "relative_lifetime_pd_increase",
    }


def test_rating_downgrade_uses_notch_order(baseline, policy) -> None:
    result = assess(baseline, policy, current_rating="B1")
    assert result.rating_downgrade_notches == 2
    assert "rating_downgrade" in result.active_triggers


@pytest.mark.parametrize(
    ("overrides", "trigger"),
    [
        ({"watchlist": True}, "watchlist"),
        ({"concession_or_forbearance": True}, "concession_or_forbearance"),
        ({"qualitative_events": ("covenant_breach",)}, "qualitative:covenant_breach"),
    ],
)
def test_watchlist_concession_and_qualitative_events_are_direct_triggers(
    baseline, policy, overrides, trigger
) -> None:
    result = assess(baseline, policy, **overrides)
    assert result.is_sicr
    assert trigger in result.active_triggers


def test_days_past_due_backstop_is_inclusive(baseline, policy) -> None:
    result = assess(baseline, policy, days_past_due=policy.days_past_due_backstop)
    assert "days_past_due_backstop" in result.active_triggers


def test_low_credit_risk_exemption_suppresses_only_quantitative_triggers(baseline, policy) -> None:
    result = assess(baseline, policy, current_lifetime_pd="0.02")
    assert not result.is_sicr
    assert result.low_credit_risk_exemption_applied
    assert result.active_triggers == ()
    assert result.suppressed_triggers == ("relative_lifetime_pd_increase",)


def test_direct_trigger_overrides_low_credit_risk_exemption(baseline, policy) -> None:
    result = assess(baseline, policy, current_lifetime_pd="0.02", watchlist=True)
    assert result.is_sicr
    assert not result.low_credit_risk_exemption_applied
    assert "watchlist" in result.active_triggers
    assert "relative_lifetime_pd_increase" in result.active_triggers


def test_decision_contains_policy_hash_evidence_and_detailed_reasons(baseline, policy) -> None:
    result = assess(baseline, policy, watchlist=True)
    assert result.policy_version == "2026.07.1"
    assert len(result.policy_sha256) == 64
    assert result.evidence_status == "demonstrative_unvalidated"
    assert "active:watchlist" in result.reasons


def test_no_trigger_returns_explicit_reason(baseline, policy) -> None:
    result = assess(baseline, policy)
    assert not result.is_sicr
    assert result.reasons == ("no_sicr_trigger",)
