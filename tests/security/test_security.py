from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.database import DatabaseManager, DatabaseSettings
from src.interfaces.api.app import create_app
from src.security.auth import AuthenticationError, AuthService
from src.security.confirmations import ConfirmationError, ConfirmationService
from src.security.passwords import PasswordPolicyError, hash_password, verify_password
from src.security.rate_limit import RateLimiter, RateLimitExceeded
from src.security.rbac import Permission, Role, is_allowed
from src.security.settings import SecurityConfigurationError, SecuritySettings

SECRET = "test-secret-that-is-at-least-32-bytes-long"


@pytest.fixture
def database(tmp_path: Path) -> DatabaseManager:
    manager = DatabaseManager(
        DatabaseSettings(backend="sqlite", sqlite_path=tmp_path / "security.sqlite3")
    )
    manager.apply_migrations()
    return manager


def test_rbac_separates_calculation_approval_export_and_audit() -> None:
    assert is_allowed(Role.ANALYST, Permission.CALCULATE_INDIVIDUAL)
    assert not is_allowed(Role.ANALYST, Permission.CALCULATE_PORTFOLIO)
    assert not is_allowed(Role.ANALYST, Permission.APPROVE_SCENARIO)
    assert is_allowed(Role.MANAGER, Permission.APPROVE_SCENARIO)
    assert is_allowed(Role.MANAGER, Permission.EXPORT_REGULATORY)
    assert not is_allowed(Role.MANAGER, Permission.VIEW_AUDIT)
    assert is_allowed(Role.AUDITOR, Permission.VIEW_AUDIT)
    assert not is_allowed(Role.AUDITOR, Permission.CALCULATE_INDIVIDUAL)
    assert not is_allowed(Role.ADMIN, Permission.CALCULATE_INDIVIDUAL)


def test_security_configuration_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(SecurityConfigurationError, match="JWT_SECRET"):
        SecuritySettings.from_env()
    with pytest.raises(SecurityConfigurationError, match="32 bytes"):
        SecuritySettings(jwt_secret="too-short")


def test_password_policy_and_bcrypt_verification() -> None:
    with pytest.raises(PasswordPolicyError):
        hash_password("weak")
    with pytest.raises(PasswordPolicyError, match="username"):
        hash_password("Analyst!Pass123", username="analyst")

    password_hash = hash_password("Strong!Pass123")
    assert password_hash.startswith("$2")
    assert verify_password("Strong!Pass123", password_hash)
    assert not verify_password("Wrong!Pass123", password_hash)


def test_jwt_session_is_persisted_and_revocable(database: DatabaseManager) -> None:
    auth = AuthService(database, SecuritySettings(jwt_secret=SECRET))
    principal = auth.create_user("analyst", "Strong!Pass123", Role.ANALYST)
    token = auth.issue_token("analyst", "Strong!Pass123")

    authenticated = auth.authenticate_token(token)
    assert authenticated == principal
    assert database.fetch_one("SELECT jti_hash FROM security_sessions") is not None

    auth.revoke(token)
    with pytest.raises(AuthenticationError, match="inactive session"):
        auth.authenticate_token(token)
    with pytest.raises(AuthenticationError, match="credentials"):
        auth.issue_token("analyst", "Wrong!Pass123")


def test_confirmation_is_bound_to_user_action_payload_and_single_use(
    database: DatabaseManager,
) -> None:
    settings = SecuritySettings(jwt_secret=SECRET)
    confirmation = ConfirmationService(database, settings)
    auth = AuthService(database, settings)
    user = auth.create_user("manager", "Strong!Pass123", Role.MANAGER)
    identifier = confirmation.issue(user.user_id, "regulatory:export", "a" * 64)

    with pytest.raises(ConfirmationError):
        confirmation.consume(identifier, user.user_id, "regulatory:export", "b" * 64)
    confirmation.consume(identifier, user.user_id, "regulatory:export", "a" * 64)
    with pytest.raises(ConfirmationError, match="consumed"):
        confirmation.consume(identifier, user.user_id, "regulatory:export", "a" * 64)


def test_rate_limiter_releases_key_after_window() -> None:
    now = [0.0]
    limiter = RateLimiter(2, 10, clock=lambda: now[0])
    limiter.check("user")
    limiter.check("user")
    with pytest.raises(RateLimitExceeded):
        limiter.check("user")
    now[0] = 10.1
    limiter.check("user")


def test_api_requires_token_and_logout_revokes_session(tmp_path: Path) -> None:
    app = create_app(
        DatabaseSettings(sqlite_path=tmp_path / "api-security.sqlite3"),
        SecuritySettings(jwt_secret=SECRET),
    )
    app.state.auth_service.create_user("auditor", "Strong!Pass123", Role.AUDITOR)
    with TestClient(app) as api:
        assert api.get("/api/v1/ecl/executions/missing").status_code == 401
        login = api.post(
            "/api/v1/auth/token",
            json={"username": "auditor", "password": "Strong!Pass123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert api.get("/api/v1/ecl/executions/missing", headers=headers).status_code == 404
        assert api.post("/api/v1/auth/logout", headers=headers).status_code == 204
        assert api.get("/api/v1/ecl/executions/missing", headers=headers).status_code == 401


def test_api_enforces_role_and_login_rate_limit(tmp_path: Path) -> None:
    app = create_app(
        DatabaseSettings(sqlite_path=tmp_path / "api-rate.sqlite3"),
        SecuritySettings(jwt_secret=SECRET, rate_limit_requests=1),
    )
    app.state.auth_service.create_user("analyst", "Strong!Pass123", Role.ANALYST)
    with TestClient(app) as api:
        first = api.post(
            "/api/v1/auth/token",
            json={"username": "analyst", "password": "Strong!Pass123"},
        )
        second = api.post(
            "/api/v1/auth/token",
            json={"username": "analyst", "password": "Strong!Pass123"},
        )
        headers = {"Authorization": f"Bearer {first.json()['access_token']}"}
        forbidden = api.post(
            "/api/v1/security/confirmations",
            json={"action": "ecl:calculate:portfolio", "payload_hash": "a" * 64},
            headers=headers,
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert forbidden.status_code == 403


def test_only_auditor_can_read_hash_chained_api_events(tmp_path: Path) -> None:
    app = create_app(
        DatabaseSettings(sqlite_path=tmp_path / "api-audit.sqlite3"),
        SecuritySettings(jwt_secret=SECRET),
    )
    app.state.auth_service.create_user("auditor", "Strong!Pass123", Role.AUDITOR)
    app.state.auth_service.create_user("manager", "Strong!Pass123", Role.MANAGER)
    with TestClient(app) as api:
        auditor_token = api.post(
            "/api/v1/auth/token",
            json={"username": "auditor", "password": "Strong!Pass123"},
        ).json()["access_token"]
        manager_token = api.post(
            "/api/v1/auth/token",
            json={"username": "manager", "password": "Strong!Pass123"},
        ).json()["access_token"]
        auditor_response = api.get(
            "/api/v1/audit/events",
            headers={"Authorization": f"Bearer {auditor_token}"},
        )
        manager_response = api.get(
            "/api/v1/audit/events",
            headers={"Authorization": f"Bearer {manager_token}"},
        )

    assert auditor_response.status_code == 200
    assert {event["action"] for event in auditor_response.json()} >= {
        "AUTH_LOGIN",
        "AUDIT_EVENTS_READ",
    }
    assert manager_response.status_code == 403
