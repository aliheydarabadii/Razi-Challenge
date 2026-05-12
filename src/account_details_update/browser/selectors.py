"""Selector constants used by the Playwright adapter."""

# Login page — verified against https://marketplace.dev-challenge.com/login
EMAIL_INPUT = "#email"
PASSWORD_INPUT = "#password"
LOGIN_BUTTON = "button[type='submit']"

# MFA page — verified
MFA_CODE_INPUT = "[data-input-otp='true']"
MFA_VERIFY_BUTTON = "button[type='submit']"

# Account page (/app/account) — verified against challenge site HTML
BANK_ROUTING_INPUT = "#bank-routing"
BANK_ACCOUNT_INPUT = "#bank-account"
BANK_SAVE_BUTTON = "#bank-save"
CARDHOLDER_NAME_INPUT = "#card-holder"
CARD_NUMBER_INPUT = "#card-number"
CARD_EXPIRY_MONTH_INPUT = "#card-exp-month"
CARD_EXPIRY_YEAR_INPUT = "#card-exp-year"
CARD_CVC_INPUT = "#card-cvc"
CARD_SAVE_BUTTON = "#card-save"

# Post-save confirmation elements — verified against challenge site HTML
BANK_CONFIRMATION = "#bank-confirmation"
CARD_CONFIRMATION = "#card-confirmation"
