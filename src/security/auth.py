"""Persistent users, short-lived JWTs and revocable sessions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt  # type: ignore[import-untyped]

from ..infrastructure.database import DatabaseManager
from .passwords import hash_password, verify_password
from .rbac import Role
from .settings import SecuritySettings


class AuthenticationError(ValueError):
    """Raised for invalid credentials or invalid/revoked tokens."""


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    username: str
    role: Role


def _utc_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value).astimezone(UTC)
    raise AuthenticationError("invalid persisted timestamp")


class AuthService:
    def __init__(self, database: DatabaseManager, settings: SecuritySettings) -> None:
        self.database = database
        self.settings = settings

    @staticmethod
    def _jti_hash(jti: str) -> str:
        return hashlib.sha256(jti.encode()).hexdigest()

    def create_user(self, username: str, password: str, role: Role) -> Principal:
        user_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        self.database.execute(
            "INSERT INTO security_users "
            "(user_id, username, password_hash, role, active, token_version, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                username,
                hash_password(password, username=username),
                role.value,
                True,
                1,
                now,
            ),
        )
        return Principal(user_id, username, role)

    def issue_token(self, username: str, password: str) -> str:
        row = self.database.fetch_one(
            "SELECT user_id, username, password_hash, role, active, token_version "
            "FROM security_users WHERE username = ?",
            (username,),
        )
        if row is None or not row["active"] or not verify_password(password, row["password_hash"]):
            raise AuthenticationError("invalid credentials")
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=self.settings.access_token_minutes)
        jti = str(uuid4())
        claims = {
            "sub": row["user_id"],
            "username": row["username"],
            "role": row["role"],
            "token_version": row["token_version"],
            "jti": jti,
            "type": "access",
            "iss": self.settings.issuer,
            "aud": self.settings.audience,
            "iat": now,
            "nbf": now,
            "exp": expires,
        }
        token = str(jwt.encode(claims, self.settings.jwt_secret, algorithm="HS256"))
        self.database.execute(
            "INSERT INTO security_sessions "
            "(jti_hash, user_id, token_version, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                self._jti_hash(jti),
                row["user_id"],
                row["token_version"],
                expires.isoformat(),
                now.isoformat(),
            ),
        )
        return token

    def authenticate_token(self, token: str) -> Principal:
        try:
            claims = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=["HS256"],
                issuer=self.settings.issuer,
                audience=self.settings.audience,
                options={"require_exp": True, "require_iat": True, "require_sub": True},
            )
            if claims.get("type") != "access":
                raise AuthenticationError("invalid token type")
            role = Role(claims["role"])
        except (JWTError, KeyError, ValueError) as exc:
            raise AuthenticationError("invalid token") from exc
        row = self.database.fetch_one(
            "SELECT s.revoked_at, s.expires_at, u.username, u.role, u.active, u.token_version "
            "FROM security_sessions s JOIN security_users u ON u.user_id = s.user_id "
            "WHERE s.jti_hash = ? AND s.user_id = ?",
            (self._jti_hash(claims["jti"]), claims["sub"]),
        )
        if (
            row is None
            or row["revoked_at"] is not None
            or not row["active"]
            or int(row["token_version"]) != int(claims["token_version"])
            or _utc_timestamp(row["expires_at"]) <= datetime.now(UTC)
            or row["role"] != role.value
        ):
            raise AuthenticationError("inactive session")
        return Principal(claims["sub"], row["username"], role)

    def revoke(self, token: str) -> None:
        try:
            claims = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=["HS256"],
                issuer=self.settings.issuer,
                audience=self.settings.audience,
            )
            jti = claims["jti"]
        except (JWTError, KeyError) as exc:
            raise AuthenticationError("invalid token") from exc
        self.database.execute(
            "UPDATE security_sessions SET revoked_at = ? WHERE jti_hash = ?",
            (datetime.now(UTC).isoformat(), self._jti_hash(jti)),
        )
