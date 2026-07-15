"""Fail-closed security configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


class SecurityConfigurationError(ValueError):
    """Raised when mandatory authentication controls are not configured."""


@dataclass(frozen=True, slots=True)
class SecuritySettings:
    jwt_secret: str
    issuer: str = "risco-bancario"
    audience: str = "risco-bancario-api"
    access_token_minutes: int = 15
    confirmation_minutes: int = 5
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60

    def __post_init__(self) -> None:
        if len(self.jwt_secret.encode()) < 32:
            raise SecurityConfigurationError("JWT secret must contain at least 32 bytes")
        if self.access_token_minutes <= 0 or self.confirmation_minutes <= 0:
            raise SecurityConfigurationError("token and confirmation lifetimes must be positive")
        if self.rate_limit_requests <= 0 or self.rate_limit_window_seconds <= 0:
            raise SecurityConfigurationError("rate-limit settings must be positive")

    @classmethod
    def from_env(cls) -> SecuritySettings:
        secret = os.getenv("JWT_SECRET")
        if not secret:
            raise SecurityConfigurationError("JWT_SECRET is required")
        return cls(
            jwt_secret=secret,
            issuer=os.getenv("JWT_ISSUER", "risco-bancario"),
            audience=os.getenv("JWT_AUDIENCE", "risco-bancario-api"),
            access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "15")),
            confirmation_minutes=int(os.getenv("CONFIRMATION_MINUTES", "5")),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "30")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        )
