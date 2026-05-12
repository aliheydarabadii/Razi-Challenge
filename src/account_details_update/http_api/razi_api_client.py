"""Low-level Razi REST API client."""

from __future__ import annotations

import httpx

from ..account_details import BankingDetails, PaymentMethod
from .errors import (
    AuthenticationError,
    MfaVerificationError,
    RateLimitError,
    RaziApiError,
    ValidationError,
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


class RaziApiClient:
    """HTTP client for the Razi REST API.

    Authentication note: the custom /auth/token → /auth/mfa/verify flow stores
    MFA tokens in Deno instance memory. Because the Supabase edge-function load
    balancer routes the two requests to different instances, verify_mfa always
    fails. When supabase_url and anon_key are supplied the client transparently
    uses the Supabase native auth endpoint instead, which works correctly.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        mfa_code: str,
        anon_key: str = "",
        supabase_url: str = "",
        _http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._mfa_code = mfa_code
        self._anon_key = anon_key
        self._supabase_url = supabase_url.rstrip("/")
        self._http = _http_client or httpx.Client()
        self._native_access_token: str | None = None

    def request_token(self) -> TokenResponse:
        """Step 1 of auth. Uses native Supabase auth when anon_key is set."""
        if self._supabase_url and self._anon_key:
            # Native Supabase auth: single request, no Deno instance routing issue.
            response = self._http.post(
                f"{self._supabase_url}/auth/v1/token?grant_type=password",
                json={"email": self._username, "password": self._password},
                headers={"apikey": self._anon_key},
            )
            self._raise_for_status(response)
            self._native_access_token = response.json()["access_token"]
            return TokenResponse(
                mfa_required=False,
                mfa_token="",
                message="Authenticated via Supabase native auth.",
            )

        # Custom auth flow (broken on this deployment — see class docstring).
        payload = TokenRequest(email=self._username, password=self._password)
        response = self._http.post(
            f"{self.base_url}/auth/token",
            json=payload.model_dump(),
        )
        self._raise_for_status(response)
        return TokenResponse.model_validate(response.json())

    def verify_mfa(self, token_response: TokenResponse) -> str:
        """Step 2 of auth. Returns the bearer access token."""
        if self._native_access_token is not None:
            token = self._native_access_token
            self._native_access_token = None
            return token

        payload = MfaVerifyRequest(
            mfa_token=token_response.mfa_token,
            code=self._mfa_code,
        )
        response = self._http.post(
            f"{self.base_url}/auth/mfa/verify",
            json=payload.model_dump(),
        )
        self._raise_for_status(response, is_mfa=True)
        return MfaVerifyResponse.model_validate(response.json()).access_token

    def update_banking(
        self,
        bearer_token: str,
        banking_details: BankingDetails,
    ) -> BankingUpdateResponse:
        """PUT /account/banking — returns masked confirmation."""
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
        return BankingUpdateResponse.model_validate(response.json())

    def update_payment(
        self,
        bearer_token: str,
        payment_method: PaymentMethod,
    ) -> PaymentUpdateResponse:
        """PUT /account/payment — returns masked card confirmation."""
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
        return PaymentUpdateResponse.model_validate(response.json())

    def _raise_for_status(
        self, response: httpx.Response, *, is_mfa: bool = False
    ) -> None:
        if response.is_success:
            return
        status = response.status_code
        try:
            detail = response.json().get("message", response.text)
        except Exception:
            detail = response.text
        if status == 401:
            if is_mfa:
                raise MfaVerificationError(detail)
            raise AuthenticationError(detail)
        if status == 422:
            raise ValidationError(detail)
        if status == 429:
            raise RateLimitError(detail)
        raise RaziApiError(f"HTTP {status}: {detail}")
