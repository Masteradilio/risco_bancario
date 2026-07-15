"""FastAPI application factory for the canonical versioned API."""

import hashlib
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...agent import AgentQuery, AgentResponse, GroundedEvidenceAgent
from ...agent.evidence import ExecutionNotFoundError
from ...audit import AuditService
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
    audit = AuditService(database)
    confirmations = ConfirmationService(database, security_configuration)
    limiter = RateLimiter(
        security_configuration.rate_limit_requests,
        security_configuration.rate_limit_window_seconds,
    )
    service = CanonicalECLApiService(VersionedRepository(database))
    evidence_agent = GroundedEvidenceAgent(database)
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
    AuditPrincipal = Annotated[Principal, Depends(require(Permission.VIEW_AUDIT))]
    BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "api_version": "v1"}

    @application.post("/api/v1/auth/token", response_model=TokenResponse, tags=["security"])
    def login(request: LoginRequest, http_request: Request) -> TokenResponse:
        try:
            limiter.check(f"login:{request.username.casefold()}")
            token = auth.issue_token(request.username, request.password)
        except RateLimitExceeded as exc:
            audit.record(
                actor_id="anonymous",
                actor_role=None,
                action="AUTH_LOGIN_RATE_LIMITED",
                resource_type="session",
                resource_id=hashlib.sha256(request.username.encode()).hexdigest(),
                input_payload={"username": request.username},
                result_payload={"error_code": "RATE_LIMITED"},
                versions={"auth": "v1"},
                status="DENIED",
                client_ip=http_request.client.host if http_request.client else None,
            )
            raise HTTPException(status_code=429, detail="rate limit exceeded") from exc
        except AuthenticationError as exc:
            audit.record(
                actor_id="anonymous",
                actor_role=None,
                action="AUTH_LOGIN",
                resource_type="session",
                resource_id=hashlib.sha256(request.username.encode()).hexdigest(),
                input_payload={"username": request.username},
                result_payload={"authenticated": False},
                versions={"auth": "v1"},
                status="DENIED",
                client_ip=http_request.client.host if http_request.client else None,
            )
            raise HTTPException(status_code=401, detail="invalid credentials") from exc
        principal = auth.authenticate_token(token)
        audit.record(
            actor_id=principal.user_id,
            actor_role=principal.role.value,
            action="AUTH_LOGIN",
            resource_type="session",
            resource_id=principal.user_id,
            input_payload={"username": request.username},
            result_payload={"authenticated": True},
            versions={"auth": "v1"},
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        return TokenResponse(access_token=token)

    @application.post("/api/v1/auth/logout", status_code=204, tags=["security"])
    def logout(
        credentials: BearerCredentials,
        _principal: Annotated[Principal, Depends(current_principal)],
        http_request: Request,
    ) -> None:
        if credentials is None:
            raise HTTPException(status_code=401, detail="authentication required")
        audit.record(
            actor_id=_principal.user_id,
            actor_role=_principal.role.value,
            action="AUTH_LOGOUT",
            resource_type="session",
            resource_id=_principal.user_id,
            input_payload={},
            result_payload={"revoked": True},
            versions={"auth": "v1"},
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        auth.revoke(credentials.credentials)

    @application.post(
        "/api/v1/security/confirmations",
        response_model=ConfirmationResponse,
        tags=["security"],
    )
    def create_confirmation(
        request: ConfirmationRequest,
        principal: PortfolioPrincipal,
        http_request: Request,
    ) -> ConfirmationResponse:
        confirmation_id = confirmations.issue(
            principal.user_id, request.action, request.payload_hash
        )
        audit.record(
            actor_id=principal.user_id,
            actor_role=principal.role.value,
            action="CRITICAL_CONFIRMATION_CREATED",
            resource_type="confirmation",
            resource_id=confirmation_id,
            input_payload=request.model_dump(mode="json"),
            result_payload={"issued": True},
            versions={"security": "v1"},
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
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
        http_request: Request,
    ) -> ECLCalculationResponse:
        try:
            result = service.calculate(request)
        except ValueError as exc:
            audit.record(
                actor_id=_principal.user_id,
                actor_role=_principal.role.value,
                action="ECL_CALCULATE_INDIVIDUAL",
                resource_type="contract",
                resource_id=request.contract_id,
                input_payload=request.model_dump(mode="json"),
                result_payload={"error_code": "INPUT_INVALID"},
                versions={
                    "models": request.model_versions,
                    "scenario": request.scenario_version,
                    "configuration": request.configuration_version,
                    "code": request.code_commit,
                },
                status="FAILED",
                client_ip=http_request.client.host if http_request.client else None,
            )
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        audit.record(
            actor_id=_principal.user_id,
            actor_role=_principal.role.value,
            action="ECL_CALCULATE_INDIVIDUAL",
            resource_type="contract",
            resource_id=request.contract_id,
            execution_id=result.execution_id,
            input_payload=request.model_dump(mode="json"),
            result_payload=result.model_dump(mode="json"),
            versions={
                "models": request.model_versions,
                "scenario": request.scenario_version,
                "configuration": request.configuration_version,
                "code": request.code_commit,
            },
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        return result

    def process_portfolio(
        job_id: str, requests: list[ECLCalculationRequest], actor_id: str, actor_role: str
    ) -> None:
        jobs.running(job_id)
        try:
            results = [service.calculate(request).model_dump(mode="json") for request in requests]
            jobs.succeeded(job_id, results)
            audit.record(
                actor_id=actor_id,
                actor_role=actor_role,
                action="ECL_PORTFOLIO_COMPLETED",
                resource_type="job",
                resource_id=job_id,
                input_payload={"contracts": len(requests)},
                result_payload={"results": results},
                versions={"api": "v1"},
                status="SUCCEEDED",
            )
        except Exception:
            logger.exception("Portfolio job failed", extra={"job_id": job_id})
            jobs.failed(job_id, "CALCULATION_FAILED")
            audit.record(
                actor_id=actor_id,
                actor_role=actor_role,
                action="ECL_PORTFOLIO_COMPLETED",
                resource_type="job",
                resource_id=job_id,
                input_payload={"contracts": len(requests)},
                result_payload={"error_code": "CALCULATION_FAILED"},
                versions={"api": "v1"},
                status="FAILED",
            )

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
        http_request: Request,
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
            audit.record(
                actor_id=principal.user_id,
                actor_role=principal.role.value,
                action="CRITICAL_CONFIRMATION_CONSUMED",
                resource_type="confirmation",
                resource_id=confirmation_id,
                input_payload={"action": "ecl:calculate:portfolio", "payload_hash": request_hash},
                result_payload={"accepted": False},
                versions={"security": "v1"},
                status="DENIED",
                client_ip=http_request.client.host if http_request.client else None,
            )
            raise HTTPException(status_code=409, detail="critical confirmation invalid") from exc
        audit.record(
            actor_id=principal.user_id,
            actor_role=principal.role.value,
            action="CRITICAL_CONFIRMATION_CONSUMED",
            resource_type="confirmation",
            resource_id=confirmation_id,
            input_payload={"action": "ecl:calculate:portfolio", "payload_hash": request_hash},
            result_payload={"accepted": True},
            versions={"security": "v1"},
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        job_id = jobs.create(request_json)
        audit.record(
            actor_id=principal.user_id,
            actor_role=principal.role.value,
            action="ECL_PORTFOLIO_SUBMITTED",
            resource_type="job",
            resource_id=job_id,
            input_payload=request.model_dump(mode="json"),
            result_payload={"status": "PENDING"},
            versions={"api": "v1"},
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        background_tasks.add_task(
            process_portfolio,
            job_id,
            request.calculations,
            principal.user_id,
            principal.role.value,
        )
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
        http_request: Request,
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
            "SELECT contract_id, period, scenario_id, ecl_amount, payload_json, payload_hash "
            "FROM calculation_results WHERE execution_id = ? "
            "ORDER BY contract_id, scenario_id, period",
            (execution_id,),
        )
        execution["lineage"] = json.loads(execution.pop("lineage_json"))
        for result in results:
            result["payload"] = json.loads(result.pop("payload_json"))
        execution["results"] = results
        audit.record(
            actor_id=_principal.user_id,
            actor_role=_principal.role.value,
            action="ECL_EVIDENCE_READ",
            resource_type="execution",
            resource_id=execution_id,
            execution_id=execution_id,
            input_payload={"execution_id": execution_id},
            result_payload={"result_count": len(results)},
            versions={"api": "v1"},
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        return execution

    @application.get("/api/v1/validation/limitations", tags=["evidence"])
    def validation_limitations(
        _principal: ResultPrincipal,
        http_request: Request,
    ) -> dict[str, object]:
        source_path = (
            Path(__file__).resolve().parents[3] / "docs" / "validation" / "LIMITATION_REGISTER.md"
        )
        content = source_path.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        audit.record(
            actor_id=_principal.user_id,
            actor_role=_principal.role.value,
            action="VALIDATION_LIMITATIONS_READ",
            resource_type="document",
            resource_id="LIMITATION_REGISTER",
            input_payload={},
            result_payload={"source_hash": source_hash},
            versions={"api": "v1", "document": source_hash},
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        return {
            "status": "LIMITED",
            "source_path": "docs/validation/LIMITATION_REGISTER.md",
            "source_hash": source_hash,
            "content": content,
        }

    @application.post(
        "/api/v1/agent/query",
        response_model=AgentResponse,
        tags=["agent"],
    )
    def query_evidence_agent(
        request: AgentQuery,
        principal: ResultPrincipal,
        http_request: Request,
    ) -> AgentResponse:
        try:
            response = evidence_agent.answer(request)
        except ExecutionNotFoundError as exc:
            raise HTTPException(status_code=404, detail="execution evidence not found") from exc
        audit.record(
            actor_id=principal.user_id,
            actor_role=principal.role.value,
            action="EVIDENCE_AGENT_QUERY",
            resource_type="execution",
            resource_id=request.execution_id,
            execution_id=request.execution_id if response.guardrail_status != "REFUSED" else None,
            input_payload={
                "execution_id": request.execution_id,
                "question_hash": hashlib.sha256(request.question.encode("utf-8")).hexdigest(),
            },
            result_payload={
                "guardrail_status": response.guardrail_status,
                "citation_count": len(response.citations),
            },
            versions={"agent": "grounded-v1", "api": "v1"},
            status="DENIED" if response.guardrail_status == "REFUSED" else "SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        return response

    @application.get("/api/v1/audit/events", tags=["audit"])
    def audit_events(
        principal: AuditPrincipal,
        http_request: Request,
        limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    ) -> list[dict[str, Any]]:
        audit.record(
            actor_id=principal.user_id,
            actor_role=principal.role.value,
            action="AUDIT_EVENTS_READ",
            resource_type="audit_log",
            resource_id="global",
            input_payload={"limit": limit},
            result_payload={"authorized": True},
            versions={"audit": "v1"},
            status="SUCCEEDED",
            client_ip=http_request.client.host if http_request.client else None,
        )
        return audit.list_events(limit=limit)

    return application
