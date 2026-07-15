"""FastAPI application factory for the canonical versioned API."""

from __future__ import annotations

import json
import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, status

from ...infrastructure.database import DatabaseManager, DatabaseSettings, VersionedRepository
from ...infrastructure.database.repository import canonical_json
from .jobs import JobStore
from .schemas import (
    ECLCalculationRequest,
    ECLCalculationResponse,
    JobAcceptedResponse,
    JobStatusResponse,
    PortfolioRequest,
)
from .service import CanonicalECLApiService

logger = logging.getLogger(__name__)


def create_app(settings: DatabaseSettings | None = None) -> FastAPI:
    database = DatabaseManager(settings)
    database.apply_migrations()
    service = CanonicalECLApiService(VersionedRepository(database))
    jobs = JobStore(database)
    application = FastAPI(
        title="Risco Bancário — API canônica",
        description="API demonstrativa com dados sintéticos; não homologada pelo BCB.",
        version="1.0.0",
    )

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "api_version": "v1"}

    @application.post(
        "/api/v1/ecl/individual",
        response_model=ECLCalculationResponse,
        tags=["ecl"],
    )
    def calculate_individual(request: ECLCalculationRequest) -> ECLCalculationResponse:
        try:
            return service.calculate(request)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def process_portfolio(job_id: str, requests: list[ECLCalculationRequest]) -> None:
        jobs.running(job_id)
        try:
            results = [service.calculate(request).model_dump(mode="json") for request in requests]
            jobs.succeeded(job_id, results)
        except Exception:
            logger.exception("Portfolio job failed", extra={"job_id": job_id})
            jobs.failed(job_id, "CALCULATION_FAILED")

    @application.post(
        "/api/v1/ecl/portfolio",
        response_model=JobAcceptedResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["ecl"],
    )
    def calculate_portfolio(
        request: PortfolioRequest, background_tasks: BackgroundTasks
    ) -> JobAcceptedResponse:
        request_json = canonical_json(request.model_dump(mode="json"))
        job_id = jobs.create(request_json)
        background_tasks.add_task(process_portfolio, job_id, request.calculations)
        return JobAcceptedResponse(
            job_id=job_id,
            status="PENDING",
            status_url=f"/api/v1/ecl/jobs/{job_id}",
        )

    @application.get("/api/v1/ecl/jobs/{job_id}", response_model=JobStatusResponse, tags=["ecl"])
    def job_status(job_id: str) -> JobStatusResponse:
        row = jobs.get(job_id)
        if row is None:
            raise HTTPException(status_code=404, detail="job not found")
        result = json.loads(row["result_json"]) if row["result_json"] else None
        return JobStatusResponse(
            job_id=row["job_id"],
            status=row["status"],
            request_hash=row["request_hash"],
            result=result,
            error_code=row["error_code"],
        )

    @application.get("/api/v1/ecl/executions/{execution_id}", tags=["evidence"])
    def execution_evidence(execution_id: str) -> dict[str, object]:
        execution = database.fetch_one(
            "SELECT execution_id, execution_key, revision, previous_execution_id, "
            "reference_date, lineage_json, lineage_hash, status, created_at "
            "FROM calculation_executions WHERE execution_id = ?",
            (execution_id,),
        )
        if execution is None:
            raise HTTPException(status_code=404, detail="execution not found")
        results = database.fetch_all(
            "SELECT contract_id, period, scenario_id, ecl_amount, payload_hash "
            "FROM calculation_results WHERE execution_id = ? "
            "ORDER BY contract_id, scenario_id, period",
            (execution_id,),
        )
        execution["lineage"] = json.loads(execution.pop("lineage_json"))
        execution["results"] = results
        return execution

    return application


app = create_app()
