"""Analytics event domain model and controlled event taxonomy."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

EventName = Literal[
    # Account
    "signup_completed",
    "login_completed",
    # Transfers
    "transfer_started",
    "transfer_recipient_selected",
    "transfer_reviewed",
    "transfer_submitted",
    "transfer_processing",
    "transfer_completed",
    "transfer_failed",
    "transfer_cancelled",
    # KYC
    "kyc_started",
    "kyc_document_submitted",
    "kyc_completed",
    "kyc_failed",
    # Wallet
    "wallet_funding_started",
    "wallet_funding_submitted",
    "wallet_funding_completed",
    "wallet_funding_failed",
    # Bill Payments
    "bill_payment_started",
    "bill_payment_submitted",
    "bill_payment_completed",
    "bill_payment_failed",
]


class AnalyticsEventProperties(BaseModel):
    """Standard container for analytics event properties."""

    app_version: str
    user_type: str | None = None
    transaction_id: str | None = None
    amount_ngn: int | None = None
    destination_bank: str | None = None
    source_bank: str | None = None
    primary_bank: str | None = None
    category: str | None = None
    duration_ms: int | None = None
    failure_code: str | None = None
    document_type: str | None = None


class AnalyticsEvent(BaseModel):
    """Operational entity representing a PostHog product analytics event."""

    distinct_id: str = Field(..., pattern=r"^usr_[a-z0-9]{6}$")
    event: EventName
    timestamp: datetime
    properties: dict[str, Any] = Field(default_factory=dict)


class AnalyticsQueryResult(BaseModel):
    """Normalized result of an analytics query."""

    query_description: str
    metric: str
    value: str | float | int | None = None
    dimensions: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    time_range: str | None = None
    limitations: list[str] = Field(default_factory=list)
    raw_count: int = 0
