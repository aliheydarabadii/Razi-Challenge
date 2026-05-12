"""Payment update request and response schemas."""

from __future__ import annotations

from ._base import ApiRequest, ApiResponse


class PaymentUpdateRequest(ApiRequest):
    cardholder_name: str
    card_number: str
    exp_month: int
    exp_year: int
    cvc: str


class PaymentUpdateResponse(ApiResponse):
    card_brand: str
    last4: str
    exp_month: int
    exp_year: int
    token: str
