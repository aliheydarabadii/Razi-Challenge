"""Low-level Razi REST API client."""

from __future__ import annotations

import logging

import httpx
import structlog
from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..banking_details import BankingDetails
from ..payment_method import PaymentMethod
from .errors import (
    ApiValidationError,
    AuthenticationError,
    MfaVerificationError,
    RateLimitError,
    RaziApiError,
    ServerError,
)
from .schemas import (
    BankingUpdateRequest,
    BankingUpdateResponse,
    MfaVerifyRequest,
    MfaVerifyResponse,
    PaymentUpdateRequest,
    PaymentUpdateResponse,
    TokenRequest,
    TokenResponse,
)

_logger = structlog.get_logger()

# Errors that are transient and worth retrying.
# AuthenticationError, MfaVerificationError, and ApiValidationError are not
# retried — they indicate a caller problem that won't resolve on its own.
_RETRYABLE = (RateLimitError, ServerError, httpx.TransportError)

# Seconds before an individual HTTP call is abandoned.
_DEFAULT_TIMEOUT = 30.0


def _default_retrying() -> Retrying:
    return Retrying(
        retry=retry_if_exception_type(_RETRYABLE),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
        before_sleep=before_sleep_log(_logger, logging.WARNING),
    )


class RaziApiClient:
    """HTTP client for the Razi REST API.

    Authentication note: the custom /auth/token → /auth/mfa/verify flow stores
    MFA tokens in Deno instance memory. Because the Supabase edge-function load
    balancer routes the two requests to different instances, verify_mfa always
    fails. When supabase_url and anon_key are supplied the client transparently
    uses the Supabase native auth endpoint instead, which works correctly.

    Retry behaviour: RateLimitError (429), ServerError (5xx), and network-level
    httpx.TransportError are retried with exponential backoff up to 5 attempts.
    Authentication and validation errors are not retried.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        mfa_code: str,
        anon_key: str = "",
        supabase_url: str = "",
        timeout: float = _DEFAULT_TIMEOUT,
        _http_client: httpx.Client | None = None,
        _retrying: Retrying | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._mfa_code = mfa_code
        self._anon_key = anon_key
        self._supabase_url = supabase_url.rstrip("/")
        self._owns_http = _http_client is None
        self._http = _http_client or httpx.Client(timeout=timeout)
        self._native_access_token: str | None = None
        self._retrying = _retrying if _retrying is not None else _default_retrying()

    def close(self) -> None:
        """Close the underlying HTTP client if it was created by this instance."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> RaziApiClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        self.close()

    def request_token(self) -> TokenResponse:
        """Step 1 of auth. Uses native Supabase auth when anon_key is set."""

        def _call() -> TokenResponse:
            if self._supabase_url and self._anon_key:
                _logger.info("request_token", auth_method="supabase_native")
                response = self._http.post(
                    f"{self._supabase_url}/auth/v1/token?grant_type=password",
                    json={"email": self._username, "password": self._password},
                    headers={"apikey": self._anon_key},
                )
                self._raise_for_status(response)
                self._native_access_token = response.json()["access_token"]
                _logger.info("token_obtained", auth_method="supabase_native")
                return TokenResponse(
                    mfa_required=False,
                    mfa_token="",
                    message="Authenticated via Supabase native auth.",
                )
            # Custom auth flow (broken on this deployment — see class docstring).
            _logger.info("request_token", auth_method="custom")
            payload = TokenRequest(email=self._username, password=self._password)
            response = self._http.post(
                f"{self.base_url}/auth/token",
                json=payload.model_dump(),
            )
            self._raise_for_status(response)
            result = TokenResponse.model_validate(response.json())
            _logger.info(
                "token_obtained",
                auth_method="custom",
                mfa_required=result.mfa_required,
            )
            return result

        return self._retrying(_call)

    def verify_mfa(self, token_response: TokenResponse) -> str:
        """Step 2 of auth. Returns the bearer access token.

        When the native auth path is active, this consumes the token cached by
        request_token() and makes no HTTP call. A subsequent call without a
        preceding request_token() falls through to the custom MFA flow.
        """

        def _call() -> str:
            if self._native_access_token is not None:
                _logger.info("verify_mfa", auth_method="supabase_native")
                token = self._native_access_token
                self._native_access_token = None
                _logger.info("mfa_verified", auth_method="supabase_native")
                return token
            _logger.info("verify_mfa", auth_method="custom")
            payload = MfaVerifyRequest(
                mfa_token=token_response.mfa_token,
                code=self._mfa_code,
            )
            response = self._http.post(
                f"{self.base_url}/auth/mfa/verify",
                json=payload.model_dump(),
            )
            self._raise_for_status(response, is_mfa=True)
            access_token = MfaVerifyResponse.model_validate(
                response.json()
            ).access_token
            _logger.info("mfa_verified", auth_method="custom")
            return access_token

        return self._retrying(_call)

    def update_banking(
        self,
        bearer_token: str,
        banking_details: BankingDetails,
    ) -> BankingUpdateResponse:
        """PUT /account/banking — returns masked confirmation."""

        def _call() -> BankingUpdateResponse:
            _logger.info("update_banking")
            payload = BankingUpdateRequest(
                routing_number=banking_details.routing_number,
                account_number=banking_details.account_number,
            )
            response = self._http.put(
                f"{self.base_url}/account/banking",
                json=payload.model_dump(),
                headers={"Authorization": f"Bearer {bearer_token}"},
            )
            self._raise_for_status(response)
            result = BankingUpdateResponse.model_validate(response.json())
            _logger.info(
                "banking_updated",
                routing_masked=result.routing_masked,
                account_masked=result.account_masked,
            )
            return result

        return self._retrying(_call)

    def update_payment(
        self,
        bearer_token: str,
        payment_method: PaymentMethod,
    ) -> PaymentUpdateResponse:
        """PUT /account/payment — returns masked card confirmation."""

        def _call() -> PaymentUpdateResponse:
            _logger.info("update_payment")
            payload = PaymentUpdateRequest(
                cardholder_name=payment_method.cardholder_name,
                card_number=payment_method.card_number,
                exp_month=int(payment_method.expiry_month),
                exp_year=int(payment_method.expiry_year),
                cvc=payment_method.cvc,
            )
            response = self._http.put(
                f"{self.base_url}/account/payment",
                json=payload.model_dump(),
                headers={"Authorization": f"Bearer {bearer_token}"},
            )
            self._raise_for_status(response)
            result = PaymentUpdateResponse.model_validate(response.json())
            _logger.info(
                "payment_updated",
                card_brand=result.card_brand,
                last4=result.last4,
            )
            return result

        return self._retrying(_call)

    def _raise_for_status(
        self, response: httpx.Response, *, is_mfa: bool = False
    ) -> None:
        if response.is_success:
            return
        status = response.status_code
        try:
            data = response.json()
            if isinstance(data, dict):
                detail = data.get("error") or data.get("message") or response.text
            else:
                detail = response.text
        except ValueError:
            detail = response.text
        if status == 401:
            if is_mfa:
                raise MfaVerificationError(detail)
            raise AuthenticationError(detail)
        if status == 422:
            raise ApiValidationError(detail)
        if status == 429:
            raise RateLimitError(detail)
        if status >= 500:
            raise ServerError(f"HTTP {status}: {detail}")
        raise RaziApiError(f"HTTP {status}: {detail}")
