"""HTTP API adapter package for the Razi REST API."""

__all__ = [
    "RaziApiError",
    "AuthenticationError",
    "MfaVerificationError",
    "ApiValidationError",
    "RateLimitError",
    "ServerError",
]

from .errors import (
    ApiValidationError,
    AuthenticationError,
    MfaVerificationError,
    RateLimitError,
    RaziApiError,
    ServerError,
)
