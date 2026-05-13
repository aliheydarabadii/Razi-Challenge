from __future__ import annotations

import pytest
from pydantic import ValidationError

from account_details_update.http_api.schemas.authentication import (
    TokenRequest,
    TokenResponse,
)


def test_response_ignores_unknown_fields() -> None:
    response = TokenResponse.model_validate(
        {
            "mfa_required": True,
            "mfa_token": "mfa_abc",
            "message": "ok",
            "future_field": "ignored",
        }
    )

    assert not hasattr(response, "future_field")


def test_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TokenRequest(
            email="candidate@dev-challenge.com",
            password="Password123!",
            unexpected="field",
        )
