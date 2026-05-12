"""Banking update request and response schemas."""

from __future__ import annotations

from ._base import ApiRequest, ApiResponse


class BankingUpdateRequest(ApiRequest):
    routing_number: str
    account_number: str


class BankingUpdateResponse(ApiResponse):
    routing_masked: str
    account_masked: str
    token: str
