"""Authentication request and response schemas."""

from __future__ import annotations

from ._base import ApiRequest, ApiResponse


class TokenRequest(ApiRequest):
    email: str
    password: str


class TokenResponse(ApiResponse):
    mfa_required: bool
    mfa_token: str
    message: str


class MfaVerifyRequest(ApiRequest):
    mfa_token: str
    code: str


class MfaVerifyResponse(ApiResponse):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
