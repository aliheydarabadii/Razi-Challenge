from __future__ import annotations

from datetime import date

import pytest

from account_details_update.payment_method import PaymentMethod

_REFERENCE = date(2026, 5, 1)


def _payment_method(**overrides: object) -> PaymentMethod:
    kwargs: dict[str, object] = dict(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        expiry_month=12,
        expiry_year=2030,
        cvc="123",
        reference_date=_REFERENCE,
    )
    kwargs.update(overrides)
    return PaymentMethod(**kwargs)  # type: ignore[arg-type]


def test_payment_method_accepts_valid_card_details() -> None:
    payment = _payment_method()

    assert payment.cardholder_name == "Test Candidate"
    assert payment.card_number == "4242424242424242"
    assert payment.expiry_month == 12
    assert payment.expiry_year == 2030
    assert payment.cvc == "123"


def test_cardholder_name_is_required() -> None:
    with pytest.raises(ValueError, match="cardholder_name is required"):
        _payment_method(cardholder_name="")


def test_card_number_must_contain_only_digits() -> None:
    with pytest.raises(ValueError, match="card_number must contain only digits"):
        _payment_method(card_number="424242424242424X")


def test_card_number_must_be_between_13_and_19_digits() -> None:
    with pytest.raises(ValueError, match="card_number must be 13 to 19 digits"):
        _payment_method(card_number="424242424242")


def test_cvc_must_be_3_or_4_digits() -> None:
    with pytest.raises(ValueError, match="cvc must be 3 or 4 digits"):
        _payment_method(cvc="12")


def test_card_number_must_pass_luhn_check() -> None:
    with pytest.raises(ValueError, match="Luhn"):
        _payment_method(card_number="4242424242424241")  # last digit off by one


def test_card_expired_in_a_previous_year_is_rejected() -> None:
    with pytest.raises(ValueError, match="card has already expired"):
        _payment_method(expiry_year=2025, reference_date=date(2026, 1, 1))


def test_card_expired_earlier_this_year_is_rejected() -> None:
    with pytest.raises(ValueError, match="card has already expired"):
        _payment_method(
            expiry_month=1, expiry_year=2026, reference_date=date(2026, 5, 1)
        )
