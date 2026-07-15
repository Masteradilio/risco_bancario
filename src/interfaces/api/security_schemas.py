"""Authentication and critical-confirmation API contracts."""

from pydantic import Field

from .schemas import StrictModel


class LoginRequest(StrictModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(StrictModel):
    access_token: str
    token_type: str = "bearer"


class ConfirmationRequest(StrictModel):
    action: str = Field(min_length=1, max_length=100)
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class ConfirmationResponse(StrictModel):
    confirmation_id: str
    expires_in_seconds: int
