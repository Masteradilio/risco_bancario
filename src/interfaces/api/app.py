"""FastAPI application factory for the canonical versioned API."""

import hashlib
import json
import logging
from collections.abc import Callable
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...infrastructure.database import DatabaseManager, DatabaseSettings, VersionedRepository
from ...infrastructure.database.repository import canonical_json
from ...security.auth import AuthenticationError, AuthService, Principal
from ...security.confirmations import ConfirmationError, ConfirmationService
from ...security.rate_limit import RateLimiter, RateLimitExceeded
from ...security.rbac import Permission, is_allowed
from ...security.settings import SecuritySettings
from .jobs import JobStore
from .schemas import (
    ECLCalculationRequest,
    ECLCalculationResponse,
    JobAcceptedResponse,
    JobStatusResponse,
    PortfolioRequest,
)
from .security_schemas import (
    ConfirmationRequest,
    ConfirmationResponse,
    LoginRequest,
    TokenResponse,
)
from .service import CanonicalECLApiService

logger = logging.getLogger(__name__)


def create_app(
    settings: DatabaseSettings | None = None,
    security_settings: SecuritySettings | None = None,
) -> FastAPI:
    database = DatabaseManager(settings)
    database.apply_migrations()
    security_configuration = security_settings or SecuritySettings.from_env()
    auth = AuthService(database, security_configuration)
    confirmations = ConfirmationService(database, security_configuration)
    limiter = RateLimiter(
        security_configuration.rate_limit_requests,
        security_configuration.rate_limit_window_seconds,
    )
    service = CanonicalECLApiService(VersionedRepository(database))
    jobs = JobStore(database)
    application = FastAPI(
        title="Risco Bancário — API canônica",
        description="API demonstrativa com dados sintéticos; não homologada pelo BCB.",
        version="1.0.0",
    )
    application.state.auth_service = auth
    bearer = HTTPBearer(auto_error=False)

    def current_principal(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> Principal:
        if credentials is None:
            raise HTTPException(status_code=401, detail="authentication required")
        try:
            return auth.authenticate_token(credentials.credentials)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail="invalid or inactive token") from exc

    def require(permission: Permission) -> Callable[..., Principal]:
        def dependency(
            principal: Annotated[Principal, Depends(current_principal)],
        ) -> Principal:
            if not is_allowed(principal.role, permission):
                raise HTTPException(status_code=403, detail="permission denied")
            try:
                limiter.check(f"{principal.user_id}:{permission.value}")
            except RateLimitExceeded as exc:
                raise HTTPException(status_code=429, detail="rate limit exceeded") from exc
            return principal

        return dependency

    IndividualPrincipal = Annotated[Principal, Depends(require(Permission.CALCULATE_INDIVIDUAL))]
    PortfolioPrincipal = Annotated[Principal, Depends(require(Permission.CALCULATE_PORTFOLIO))]
    ResultPrincipal = Annotated[Principal, Depends(require(Permission.VIEW_RESULT))]
    BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "api_version": "v1"}

    @application.post("/api/v1/auth/token", response_model=TokenResponse, tags=["security"])
    def login(request: LoginRequest) -> TokenResponse:
        try:
            limiter.check(f"login:{request.username.casefold()}")
            token = auth.issue_token(request.username, request.password)
        except RateLimitExceeded as exc:
            raise HTTPException(status_code=429, detail="rate limit exceeded") from exc
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail="invalid credentials") from exc
        return TokenResponse(access_token=token)

    @application.post("/api/v1/auth/logout", status_code=204, tags=["security"])
    def logout(
        credentials: BearerCredentials,
        _principal: Annotated[Principal, Depends(current_principal)],
    ) -> None:
        if credentials is None:
            raise HTTPException(status_code=401, detail="authentication required")
        auth.revoke(credentials.credentials)

    @application.post(
        "/api/v1/security/confirmations",
        response_model=ConfirmationResponse,
        tags=["security"],
    )
    def create_confirmation(
        request: ConfirmationRequest,
        principal: PortfolioPrincipal,
    ) -> ConfirmationResponse:
        confirmation_id = confirmations.issue(
            principal.user_id, request.action, request.payload_hash
        )
        return ConfirmationResponse(
            confirmation_id=confirmation_id,
            expires_in_seconds=security_configuration.confirmation_minutes * 60,
        )

    @application.post(
        "/api/v1/ecl/individual",
        response_model=ECLCalculationResponse,
        tags=["ecl"],
    )
    def calculate_individual(
        request: ECLCalculationRequest,
        _principal: IndividualPrincipal,
    ) -> ECLCalculationResponse:
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
        request: PortfolioRequest,
        background_tasks: BackgroundTasks,
        confirmation_id: Annotated[str, Header(alias="X-Confirmation-Id")],
        principal: PortfolioPrincipal,
    ) -> JobAcceptedResponse:
        request_json = canonical_json(request.model_dump(mode="json"))
        request_hash = hashlib.sha256(request_json.encode()).hexdigest()
        try:
            confirmations.consume(
                confirmation_id,
                principal.user_id,
                "ecl:calculate:portfolio",
                request_hash,
            )
        except ConfirmationError as exc:
            raise HTTPException(status_code=409, detail="critical confirmation invalid") from exc
        job_id = jobs.create(request_json)
        background_tasks.add_task(process_portfolio, job_id, request.calculations)
        return JobAcceptedResponse(
            job_id=job_id,
            status="PENDING",
            status_url=f"/api/v1/ecl/jobs/{job_id}",
        )

    @application.get("/api/v1/ecl/jobs/{job_id}", response_model=JobStatusResponse, tags=["ecl"])
    def job_status(
        job_id: str,
        _principal: PortfolioPrincipal,
    ) -> JobStatusResponse:
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
    def execution_evidence(
        execution_id: str,
        _principal: ResultPrincipal,
    ) -> dict[str, object]:
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
