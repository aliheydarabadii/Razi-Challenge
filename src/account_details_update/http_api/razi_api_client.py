"""Low-level Razi REST API client."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import KW_ONLY, InitVar, dataclass, field
from typing import TypeVar

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
from .schemas.authentication import (
    MfaVerifyRequest,
    MfaVerifyResponse,
    TokenRequest,
    TokenResponse,
)
from .schemas.banking import BankingUpdateRequest, BankingUpdateResponse
from .schemas.payment import PaymentUpdateRequest, PaymentUpdateResponse

_logger = structlog.get_logger()

# Errors that are transient and worth retrying.
# AuthenticationError, MfaVerificationError, and ApiValidationError are not
# retried — they indicate a caller problem that won't resolve on its own.
_RETRYABLE = (RateLimitError, ServerError, httpx.TransportError)

# Seconds before an individual HTTP call is abandoned.
_DEFAULT_TIMEOUT = 30.0

_T = TypeVar("_T")


@dataclass(slots=True)
class RaziApiClient:
    """HTTP client for the Razi REST API.

    Auth flow: POST /auth/token → POST /auth/mfa/verify → bearer token.

    Retry behaviour: RateLimitError (429), ServerError (5xx), and
    httpx.TransportError are retried with exponential backoff up to 5
    attempts. Authentication and validation errors are not retried.
    """

    base_url: str
    username: str
    password: str
    mfa_code: str

    _: KW_ONLY

    timeout: float = _DEFAULT_TIMEOUT
    max_retries: int = 5
    retry_max_wait: int = 30
    _http_client: InitVar[httpx.Client | None] = None
    _retrying: InitVar[Retrying | None] = None

    _owns_http: bool = field(default=False, init=False)
    _http: httpx.Client = field(init=False)
    _retry_policy: Retrying = field(init=False)

    # ── Public API ───────────────────────────────────────────────────────────

    def request_token(self) -> TokenResponse:
        """Step 1 of auth — POST /auth/token."""
        return self._with_retry(self._post_token)

    def verify_mfa(self, token_response: TokenResponse) -> str:
        """Step 2 of auth — POST /auth/mfa/verify. Returns the bearer token."""
        return self._with_retry(lambda: self._post_mfa_verify(token_response))

    def update_banking(
        self,
        bearer_token: str,
        banking_details: BankingDetails,
    ) -> BankingUpdateResponse:
        """PUT /account/banking — returns masked confirmation."""
        return self._with_retry(
            lambda: self._put_banking(bearer_token, banking_details)
        )

    def update_payment(
        self,
        bearer_token: str,
        payment_method: PaymentMethod,
    ) -> PaymentUpdateResponse:
        """PUT /account/payment — returns masked card confirmation."""
        return self._with_retry(lambda: self._put_payment(bearer_token, payment_method))

    # ── Private helpers ───────────────────────────────────────────────────────

    def _with_retry(self, call: Callable[[], _T]) -> _T:
        return self._retry_policy(call)

    def _post_token(self) -> TokenResponse:
        _logger.info("request_token")
        payload = TokenRequest(email=self.username, password=self.password)
        response = self._http.post(
            f"{self.base_url}/auth/token",
            json=payload.model_dump(),
        )
        self._raise_for_status(response)
        result = TokenResponse.model_validate(response.json())
        _logger.info("token_obtained", mfa_required=result.mfa_required)
        return result

    def _post_mfa_verify(self, token_response: TokenResponse) -> str:
        _logger.info("verify_mfa")
        payload = MfaVerifyRequest(
            mfa_token=token_response.mfa_token,
            code=self.mfa_code,
        )
        response = self._http.post(
            f"{self.base_url}/auth/mfa/verify",
            json=payload.model_dump(),
        )
        self._raise_for_status(response, unauthorized_error=MfaVerificationError)
        access_token = MfaVerifyResponse.model_validate(response.json()).access_token
        _logger.info("mfa_verified")
        return access_token

    def _put_banking(
        self,
        bearer_token: str,
        banking_details: BankingDetails,
    ) -> BankingUpdateResponse:
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

    def _put_payment(
        self,
        bearer_token: str,
        payment_method: PaymentMethod,
    ) -> PaymentUpdateResponse:
        _logger.info("update_payment")
        payload = PaymentUpdateRequest(
            cardholder_name=payment_method.cardholder_name,
            card_number=payment_method.card_number,
            exp_month=payment_method.expiry_month,
            exp_year=payment_method.expiry_year,
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
            "payment_updated", card_brand=result.card_brand, last4=result.last4
        )
        return result

    def _raise_for_status(
        self,
        response: httpx.Response,
        *,
        unauthorized_error: type[RaziApiError] = AuthenticationError,
    ) -> None:
        if response.is_success:
            return
        status = response.status_code
        detail = self._extract_detail(response)
        if status == 401:
            raise unauthorized_error(detail)
        if status == 422:
            raise ApiValidationError(detail)
        if status == 429:
            raise RateLimitError(detail)
        if status >= 500:
            raise ServerError(f"HTTP {status}: {detail}")
        raise RaziApiError(f"HTTP {status}: {detail}")

    @staticmethod
    def _extract_detail(response: httpx.Response) -> str:
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get("error") or data.get("message") or response.text
        except ValueError:
            pass
        return response.text

    # ── Protocol / initialisation (boilerplate) ───────────────────────────────

    def __post_init__(
        self,
        _http_client: httpx.Client | None,
        _retrying: Retrying | None,
    ) -> None:
        self.base_url = self.base_url.rstrip("/")
        self._owns_http = _http_client is None
        self._http = _http_client or httpx.Client(timeout=self.timeout)
        self._retry_policy = (
            _retrying
            if _retrying is not None
            else _default_retrying(self.max_retries, self.retry_max_wait)
        )

    def __enter__(self) -> RaziApiClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        if self._owns_http:
            self._http.close()


def _default_retrying(max_retries: int, retry_max_wait: int) -> Retrying:
    return Retrying(
        retry=retry_if_exception_type(_RETRYABLE),
        wait=wait_exponential(multiplier=1, min=1, max=retry_max_wait),
        stop=stop_after_attempt(max_retries),
        reraise=True,
        before_sleep=before_sleep_log(_logger, logging.WARNING),
    )
