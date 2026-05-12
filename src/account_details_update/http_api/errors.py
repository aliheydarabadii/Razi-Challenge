"""API-specific exception types."""


class RaziApiError(Exception):
    """Base exception for Razi API adapter errors."""


class AuthenticationError(RaziApiError):
    """Raised when API authentication fails."""


class MfaVerificationError(RaziApiError):
    """Raised when API MFA verification fails."""


class ApiValidationError(RaziApiError):
    """Raised when the API rejects request validation."""


class RateLimitError(RaziApiError):
    """Raised when the API rate limit is exceeded."""


class ServerError(RaziApiError):
    """Raised on 5xx responses — transient, eligible for retry."""
