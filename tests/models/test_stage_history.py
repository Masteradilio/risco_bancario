from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.contracts import Contract
from src.domain.exceptions import DomainValidationError
from src.domain.staging import Stage
from src.models.pd import CureEvidence, DefaultAssessmentInput, load_default_policy
from src.models.sicr import (
    SICRAssessmentInput,
    Stage3AssessmentInput,
    StageHistoryLedger,
    StageTransitionContext,
    assess_sicr,
    assess_stage3,
    create_origination_baseline,
    decide_stage_transition,
    load_sicr_policy,
)


@pytest.fixture(scope="module")
def policies():
    return load_default_policy(), load_sicr_policy(Path("config/sicr_policy/2026.07.1.json"))


@pytest.fixture(scope="module")
def baseline():
    contract = Contract(
        "CT-HISTORY",
        "CL-1",
        "CP-1",
        "personal_loan",
        date(2026, 1, 1),
        date(2027, 1, 1),
        "1000",
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


def decisions(baseline, policies, *, stage3=False, sicr=False):
    default_policy, sicr_policy = policies
    default_input = DefaultAssessmentInput(
        "CT-HISTORY",
        "CP-1",
        "personal_loan",
        date(2026, 7, 1),
        0,
        Decimal("0"),
        Decimal("1000"),
        ("financial_incapacity",) if stage3 else (),
    )
    stage3_decision = assess_stage3(Stage3AssessmentInput(default_input), default_policy)
    sicr_decision = assess_sicr(
        SICRAssessmentInput(
            baseline,
            date(2026, 7, 1),
            "0.011",
            "A2",
            watchlist=sicr,
        ),
        sicr_policy,
    )
    return stage3_decision, sicr_decision


def context(baseline, policies, effective_date, current_stage, **overrides):
    stage3, sicr = decisions(
        baseline,
        policies,
        stage3=overrides.pop("stage3", False),
        sicr=overrides.pop("sicr", False),
    )
    return StageTransitionContext(
        "CT-HISTORY", effective_date, current_stage, stage3, sicr, **overrides
    )


def valid_cure() -> CureEvidence:
    return CureEvidence(True, 3, True, True)


def test_stage3_trigger_is_recorded_in_history(baseline, policies) -> None:
    ledger = StageHistoryLedger("CT-HISTORY")
    record = decide_stage_transition(
        context(baseline, policies, date(2026, 7, 1), Stage.STAGE_1, stage3=True),
        ledger,
        policies[0],
    )
    ledger = ledger.append(record)
    assert ledger.records[-1].new_stage is Stage.STAGE_3
    assert "financial_incapacity" in record.reasons


def test_stage3_cannot_exit_without_cure_evidence(baseline, policies) -> None:
    record = decide_stage_transition(
        context(baseline, policies, date(2026, 8, 1), Stage.STAGE_3),
        StageHistoryLedger("CT-HISTORY"),
        policies[0],
    )
    assert record.new_stage is Stage.STAGE_3
    assert record.reasons == ("cure_evidence_missing",)


def test_premature_or_incomplete_cure_is_blocked(baseline, policies) -> None:
    evidence = CureEvidence(False, 1, False, False)
    record = decide_stage_transition(
        context(
            baseline,
            policies,
            date(2026, 8, 1),
            Stage.STAGE_3,
            cure_evidence=evidence,
        ),
        StageHistoryLedger("CT-HISTORY"),
        policies[0],
    )
    assert record.new_stage is Stage.STAGE_3
    assert record.cure_decision is not None and not record.cure_decision.eligible
    assert all(item.startswith("cure_blocked:") for item in record.reasons)


def test_valid_cure_returns_to_stage1_when_no_residual_sicr(baseline, policies) -> None:
    record = decide_stage_transition(
        context(
            baseline,
            policies,
            date(2026, 10, 1),
            Stage.STAGE_3,
            cure_evidence=valid_cure(),
        ),
        StageHistoryLedger("CT-HISTORY"),
        policies[0],
    )
    assert record.new_stage is Stage.STAGE_1
    assert record.reasons == ("default_cure_criteria_met",)


def test_valid_default_cure_with_residual_sicr_returns_to_stage2(baseline, policies) -> None:
    record = decide_stage_transition(
        context(
            baseline,
            policies,
            date(2026, 10, 1),
            Stage.STAGE_3,
            sicr=True,
            cure_evidence=valid_cure(),
        ),
        StageHistoryLedger("CT-HISTORY"),
        policies[0],
    )
    assert record.new_stage is Stage.STAGE_2
    assert "residual_sicr:watchlist" in record.reasons


def test_redefault_after_cure_is_identified(baseline, policies) -> None:
    default_policy = policies[0]
    ledger = StageHistoryLedger("CT-HISTORY")
    first = decide_stage_transition(
        context(baseline, policies, date(2026, 7, 1), Stage.STAGE_1, stage3=True),
        ledger,
        default_policy,
    )
    ledger = ledger.append(first)
    cured = decide_stage_transition(
        context(
            baseline,
            policies,
            date(2026, 10, 1),
            Stage.STAGE_3,
            cure_evidence=valid_cure(),
        ),
        ledger,
        default_policy,
    )
    ledger = ledger.append(cured)
    redefault = decide_stage_transition(
        context(baseline, policies, date(2026, 11, 1), Stage.STAGE_1, stage3=True),
        ledger,
        default_policy,
    )
    assert redefault.is_redefault
    assert "redefault_after_cure" in redefault.reasons


def test_history_rejects_non_contiguous_stage_or_date(baseline, policies) -> None:
    ledger = StageHistoryLedger("CT-HISTORY")
    first = decide_stage_transition(
        context(baseline, policies, date(2026, 7, 1), Stage.STAGE_1), ledger, policies[0]
    )
    ledger = ledger.append(first)
    with pytest.raises(DomainValidationError, match="current stage"):
        decide_stage_transition(
            context(baseline, policies, date(2026, 8, 1), Stage.STAGE_2),
            ledger,
            policies[0],
        )
    with pytest.raises(DomainValidationError, match="strictly increasing"):
        ledger.append(
            type(first)(
                2,
                first.contract_id,
                first.effective_date,
                first.new_stage,
                first.new_stage,
                ("invalid",),
                None,
                False,
                first.default_policy_version,
                first.default_policy_sha256,
                first.sicr_policy_version,
                first.sicr_policy_sha256,
            )
        )
