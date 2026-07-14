"""Governed stage transition state machine and immutable history ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ...domain.exceptions import DomainValidationError
from ...domain.staging import Stage
from ..pd import CureDecision, CureEvidence, assess_cure
from ..pd.default_definition import LoadedDefaultPolicy
from .engine import SICRDecision
from .stage3 import Stage3Decision


@dataclass(frozen=True, slots=True)
class StageTransitionContext:
    contract_id: str
    effective_date: date
    current_stage: Stage
    stage3: Stage3Decision
    sicr: SICRDecision
    cure_evidence: CureEvidence | None = None


@dataclass(frozen=True, slots=True)
class StageHistoryRecord:
    sequence: int
    contract_id: str
    effective_date: date
    prior_stage: Stage
    new_stage: Stage
    reasons: tuple[str, ...]
    cure_decision: CureDecision | None
    is_redefault: bool
    default_policy_version: str
    default_policy_sha256: str
    sicr_policy_version: str
    sicr_policy_sha256: str


@dataclass(frozen=True, slots=True)
class StageHistoryLedger:
    contract_id: str
    records: tuple[StageHistoryRecord, ...] = ()

    def append(self, record: StageHistoryRecord) -> StageHistoryLedger:
        if record.contract_id != self.contract_id:
            raise DomainValidationError("stage history contract mismatch")
        if record.sequence != len(self.records) + 1:
            raise DomainValidationError("stage history sequence must be contiguous")
        if self.records:
            prior = self.records[-1]
            if record.effective_date <= prior.effective_date:
                raise DomainValidationError("stage history dates must be strictly increasing")
            if record.prior_stage != prior.new_stage:
                raise DomainValidationError("stage history prior stage must match ledger state")
        return StageHistoryLedger(self.contract_id, (*self.records, record))


def decide_stage_transition(
    context: StageTransitionContext,
    history: StageHistoryLedger,
    default_policy: LoadedDefaultPolicy,
) -> StageHistoryRecord:
    if context.contract_id != history.contract_id:
        raise DomainValidationError("stage transition history contract mismatch")
    if (
        context.stage3.contract_id != context.contract_id
        or context.sicr.contract_id != context.contract_id
    ):
        raise DomainValidationError("stage decisions must refer to the transition contract")
    if history.records and history.records[-1].new_stage != context.current_stage:
        raise DomainValidationError("current stage does not match history")

    cure_decision: CureDecision | None = None
    reasons: list[str] = []
    prior_stage3 = any(item.new_stage is Stage.STAGE_3 for item in history.records)
    is_redefault = False
    if context.stage3.is_stage3:
        new_stage = Stage.STAGE_3
        reasons.extend(context.stage3.reasons)
        is_redefault = context.current_stage is not Stage.STAGE_3 and prior_stage3
        if is_redefault:
            reasons.append("redefault_after_cure")
    elif context.current_stage is Stage.STAGE_3:
        if context.cure_evidence is None:
            new_stage = Stage.STAGE_3
            reasons.append("cure_evidence_missing")
        else:
            cure_decision = assess_cure(context.cure_evidence, default_policy.policy)
            if not cure_decision.eligible:
                new_stage = Stage.STAGE_3
                reasons.extend(f"cure_blocked:{item}" for item in cure_decision.failed_conditions)
            else:
                new_stage = Stage.STAGE_2 if context.sicr.is_sicr else Stage.STAGE_1
                reasons.append("default_cure_criteria_met")
                reasons.extend(f"residual_sicr:{item}" for item in context.sicr.active_triggers)
    else:
        new_stage = Stage.STAGE_2 if context.sicr.is_sicr else Stage.STAGE_1
        reasons.extend(context.sicr.reasons)

    if not reasons:
        reasons.append("stage_unchanged_no_trigger")
    return StageHistoryRecord(
        len(history.records) + 1,
        context.contract_id,
        context.effective_date,
        context.current_stage,
        new_stage,
        tuple(reasons),
        cure_decision,
        is_redefault,
        context.stage3.policy_version,
        context.stage3.policy_sha256,
        context.sicr.policy_version,
        context.sicr.policy_sha256,
    )
