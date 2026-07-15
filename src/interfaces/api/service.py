"""Canonical calculation orchestration used by the HTTP API."""

from __future__ import annotations

from typing import Any

from ...domain.scenarios import (
    MacroTrajectoryPoint,
    MacroVariable,
    ScenarioApprovalStatus,
    ScenarioKind,
    ScenarioSet,
    ScenarioTrajectory,
)
from ...ecl.calculation.scenario_engine import (
    BaselineRiskPeriod,
    calculate_probability_weighted_scenario_ecl,
)
from ...infrastructure.database import VersionedRepository
from ...models.forward_looking import load_macro_risk_policy
from .schemas import (
    ECLCalculationRequest,
    ECLCalculationResponse,
    PeriodResult,
    ScenarioResult,
)


class CanonicalECLApiService:
    """Translate validated API payloads into canonical domain calculations."""

    def __init__(self, repository: VersionedRepository) -> None:
        self.repository = repository
        self.macro_policy = load_macro_risk_policy()

    @staticmethod
    def _scenario_set(request: ECLCalculationRequest) -> ScenarioSet:
        trajectories = tuple(
            ScenarioTrajectory(
                scenario_id=scenario.scenario_id,
                name=scenario.name,
                kind=ScenarioKind(scenario.kind),
                weight=scenario.weight,
                periods=tuple(
                    MacroTrajectoryPoint(
                        reference_date=period.reference_date,
                        variables=tuple(
                            MacroVariable(name=name, value=value)
                            for name, value in sorted(period.variables.items())
                        ),
                    )
                    for period in scenario.periods
                ),
            )
            for scenario in request.scenarios
        )
        return ScenarioSet(
            reference_date=trajectories[0].periods[0].reference_date,
            version=request.scenario_version,
            approval_status=ScenarioApprovalStatus.NOT_APPROVED,
            source_snapshot_hash=request.scenario_source_hash,
            trajectories=trajectories,
        )

    def calculate(self, request: ECLCalculationRequest) -> ECLCalculationResponse:
        scenario_set = self._scenario_set(request)
        baseline = tuple(
            BaselineRiskPeriod(
                reference_date=period.reference_date,
                conditional_hazard=period.conditional_hazard,
                lgd=period.lgd,
                drawn_ead=period.drawn_ead,
                undrawn_amount=period.undrawn_amount,
                ccf=period.ccf,
                discount_factor=period.discount_factor,
            )
            for period in request.periods
        )
        calculation = calculate_probability_weighted_scenario_ecl(
            baseline, scenario_set, request.segment, self.macro_policy
        )
        request_document = request.model_dump(mode="json")
        contract_hash = self.repository.persist_contract(
            request.contract_id,
            request.source_version,
            {
                "contract_id": request.contract_id,
                "reference_date": request_document["reference_date"],
                "stage": request.stage,
                "segment": request.segment,
                "periods": request_document["periods"],
            },
        )
        self.repository.persist_scenario(
            "scenario-set", request.scenario_version, {"scenarios": request_document["scenarios"]}
        )
        for model_id, version in sorted(request.model_versions.items()):
            self.repository.persist_model(model_id, version, {"version": version})
        lineage: dict[str, Any] = {
            "contract_hash": contract_hash,
            "scenario_version": calculation.scenario_version,
            "scenario_source_hash": calculation.scenario_source_hash,
            "macro_policy_version": calculation.macro_policy_version,
            "macro_policy_hash": calculation.macro_policy_hash,
            "model_versions": request.model_versions,
            "configuration_version": request.configuration_version,
            "configuration_hash": request.configuration_hash,
            "code_commit": request.code_commit,
        }
        execution = self.repository.start_execution(
            execution_key=request.execution_key,
            reference_date=request.reference_date,
            lineage=lineage,
            reprocess=request.reprocess,
        )
        scenario_responses: list[ScenarioResult] = []
        for scenario in calculation.scenario_results:
            period_responses = [
                PeriodResult(
                    reference_date=period.reference_date,
                    survival_at_start=period.survival_at_start,
                    marginal_pd=period.marginal_pd,
                    lgd=period.lgd,
                    ead=period.ead,
                    ccf=period.ccf,
                    discount_factor=period.discount_factor,
                    expected_loss=period.expected_loss,
                )
                for period in scenario.periods
            ]
            scenario_responses.append(
                ScenarioResult(
                    scenario_id=scenario.scenario_id,
                    kind=scenario.kind.value,
                    weight=scenario.weight,
                    ecl=scenario.ecl,
                    weighted_contribution=scenario.weighted_contribution,
                    periods=period_responses,
                )
            )
            for index, period in enumerate(scenario.periods, start=1):
                self.repository.persist_ecl_result(
                    execution_id=execution["execution_id"],
                    contract_id=request.contract_id,
                    period=index,
                    scenario_id=scenario.scenario_id,
                    ecl_amount=period.expected_loss,
                    payload={
                        "stage": request.stage,
                        "reference_date": period.reference_date,
                        "marginal_pd": period.marginal_pd,
                        "lgd": period.lgd,
                        "ead": period.ead,
                        "discount_factor": period.discount_factor,
                    },
                )
        self.repository.record_lineage_event(
            execution_id=execution["execution_id"],
            event_type="ECL_CALCULATED",
            payload={
                "contract_id": request.contract_id,
                "reported_ecl": calculation.probability_weighted_ecl,
            },
        )
        return ECLCalculationResponse(
            execution_id=execution["execution_id"],
            revision=execution["revision"],
            reused=execution["reused"],
            contract_id=request.contract_id,
            stage=request.stage,
            probability_weighted_ecl=calculation.probability_weighted_ecl,
            stress_ecl=calculation.stress_ecl,
            scenarios=scenario_responses,
            lineage_hash=execution["lineage_hash"],
            scenario_version=calculation.scenario_version,
            macro_policy_version=calculation.macro_policy_version,
        )
