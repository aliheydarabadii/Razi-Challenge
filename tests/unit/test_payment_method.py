from __future__ import annotations

from datetime import date

import pytest

from account_details_update.payment_method import PaymentMethod


def _payment_method(**overrides: str) -> PaymentMethod:
    kwargs: dict[str, str] = dict(
        cardholder_name="Test Candidate",
        card_number="4242424242424242",
        expiry_month="12",
        expiry_year="2030",
        cvc="123",
    )
    kwargs.update(overrides)
    return PaymentMethod(**kwargs)


def test_payment_method_stores_all_fields() -> None:
    payment = _payment_method()

    assert payment.cardholder_name == "Test Candidate"
    assert payment.card_number == "4242424242424242"


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
        _payment_method(expiry_year=str(date.today().year - 1))


def test_card_expired_earlier_this_year_is_rejected() -> None:
    today = date.today()
    if today.month == 1:
        pytest.skip("no elapsed months in January to test against")
    with pytest.raises(ValueError, match="card has already expired"):
        _payment_method(expiry_month=str(today.month - 1), expiry_year=str(today.year))
