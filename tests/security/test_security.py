from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from src.infrastructure.database import DatabaseManager, DatabaseSettings
from src.interfaces.api.app import create_app
from src.security.auth import AuthenticationError, AuthService
from src.security.auth import _utc_timestamp as auth_timestamp
from src.security.confirmations import (
    ConfirmationError,
    ConfirmationService,
)
from src.security.confirmations import (
    _utc_timestamp as confirmation_timestamp,
)
from src.security.passwords import (
    PasswordPolicyError,
    hash_password,
    validate_password,
    verify_password,
)
from src.security.rate_limit import RateLimiter, RateLimitExceeded
from src.security.rbac import Permission, Role, is_allowed
from src.security.retention import RetentionPolicy
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
    with pytest.raises(SecurityConfigurationError, match="lifetimes"):
        SecuritySettings(jwt_secret=SECRET, access_token_minutes=0)
    with pytest.raises(SecurityConfigurationError, match="rate-limit"):
        SecuritySettings(jwt_secret=SECRET, rate_limit_requests=0)

    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("JWT_ISSUER", "test-issuer")
    settings = SecuritySettings.from_env()
    assert settings.issuer == "test-issuer"


def test_password_policy_and_bcrypt_verification() -> None:
    with pytest.raises(PasswordPolicyError):
        hash_password("weak")
    with pytest.raises(PasswordPolicyError, match="username"):
        hash_password("Analyst!Pass123", username="analyst")

    password_hash = hash_password("Strong!Pass123")
    assert password_hash.startswith("$2")
    assert verify_password("Strong!Pass123", password_hash)
    assert not verify_password("Wrong!Pass123", password_hash)
    assert not verify_password("Strong!Pass123", "not-a-bcrypt-hash")


@pytest.mark.parametrize(
    "password,reason",
    [
        ("a" * 129 + "A1!", "length"),
        ("lowercase!123", "uppercase"),
        ("UPPERCASE!123", "lowercase"),
        ("NoDigitsHere!", "digit"),
        ("NoSpecial1234", "special"),
    ],
)
def test_password_policy_reports_each_missing_character_class(password: str, reason: str) -> None:
    with pytest.raises(PasswordPolicyError, match=reason):
        validate_password(password)


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


def test_authentication_rejects_wrong_token_type_and_malformed_revoke(
    database: DatabaseManager,
) -> None:
    auth = AuthService(database, SecuritySettings(jwt_secret=SECRET))
    auth.create_user("analyst", "Strong!Pass123", Role.ANALYST)
    token = auth.issue_token("analyst", "Strong!Pass123")
    claims = jwt.decode(token, options={"verify_signature": False})
    claims["type"] = "refresh"
    wrong_type = jwt.encode(claims, SECRET, algorithm="HS256")

    with pytest.raises(AuthenticationError, match="invalid token"):
        auth.authenticate_token(wrong_type)
    with pytest.raises(AuthenticationError, match="invalid token"):
        auth.revoke("malformed")


def test_persisted_security_timestamps_accept_datetime_and_reject_other_types() -> None:
    value = datetime.now(UTC)
    assert auth_timestamp(value) == value
    assert confirmation_timestamp(value) == value
    with pytest.raises(AuthenticationError, match="persisted timestamp"):
        auth_timestamp(123)
    with pytest.raises(ConfirmationError, match="persisted timestamp"):
        confirmation_timestamp(123)


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


def test_confirmation_rejects_bad_hash_and_detects_concurrent_consumption(
    database: DatabaseManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ConfirmationService(database, SecuritySettings(jwt_secret=SECRET))
    with pytest.raises(ConfirmationError, match="lowercase SHA-256"):
        service.issue("user", "action", "A" * 64)

    monkeypatch.setattr(
        database,
        "fetch_one",
        lambda *_args, **_kwargs: {
            "user_id": "user",
            "action": "action",
            "payload_hash": "a" * 64,
            "expires_at": datetime.now(UTC) + timedelta(minutes=1),
            "consumed_at": None,
        },
    )
    monkeypatch.setattr(database, "execute", lambda *_args, **_kwargs: 0)
    with pytest.raises(ConfirmationError, match="already consumed"):
        service.consume("confirmation", "user", "action", "a" * 64)


def test_retention_policy_rejects_non_positive_period_or_blank_version() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        RetentionPolicy(0, 1, 1, 1, "v1")
    with pytest.raises(ValueError, match="must be positive"):
        RetentionPolicy(1, 1, 1, 1, "")


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
