"""Lightweight PII and payment card validation for synthetic data."""

import re

# Regex matching standard 13-19 digit credit card numbers
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# Regex matching 10-digit raw numeric sequences formatted as account numbers (e.g. account: 0123456789)
ACCOUNT_NUMBER_REGEX = re.compile(
    r"\b(?:acct|account|acc|nuban)[\s:#_-]*([0-9]{10})\b", re.IGNORECASE
)

# Allowed synthetic email domains
ALLOWED_EMAIL_DOMAINS = ("@example.com", "@pocket.test", "@synthetic.test")


class PIIValidationError(ValueError):
    """Raised when real PII, raw credit card numbers, or real email domains are detected."""


def validate_text_for_pii(text: str) -> None:
    """Scan string content for credit card patterns, account numbers, or non-synthetic emails."""
    # 1. Check for credit card number patterns
    for match in CREDIT_CARD_REGEX.finditer(text):
        digits_only = re.sub(r"\D", "", match.group(0))
        # Ensure it's not a common unix timestamp or date string (e.g., 10 digits or 14 digits YYYYMMDDHHMMSS)
        if len(digits_only) in (13, 15, 16, 19):
            raise PIIValidationError(
                f"Potential raw credit card number pattern detected in text: {digits_only[:4]}...{digits_only[-4:]}"
            )

    # 2. Check for explicit 10-digit account numbers
    if ACCOUNT_NUMBER_REGEX.search(text):
        raise PIIValidationError(
            "Explicit 10-digit raw bank account number pattern detected in text."
        )

    # 3. Check for non-synthetic emails
    email_matches = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    for email in email_matches:
        if not any(email.lower().endswith(domain) for domain in ALLOWED_EMAIL_DOMAINS):
            raise PIIValidationError(
                f"Real or unapproved email domain detected: {email}. Must use one of {ALLOWED_EMAIL_DOMAINS}."
            )


def validate_identifier_format(identifier: str, expected_prefix: str) -> None:
    """Ensure identifiers follow strict synthetic prefixes (e.g. usr_, txn_)."""
    pattern = rf"^{expected_prefix}_[a-z0-9]{{6}}$"
    if not re.match(pattern, identifier):
        raise PIIValidationError(
            f"Identifier '{identifier}' does not match synthetic pattern '{pattern}'"
        )
