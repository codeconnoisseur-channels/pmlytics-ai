"""Tests for API request and response schemas."""

from datetime import UTC, datetime

import pytest
from app.api.schemas import (
    EvidenceLedgerItemSchema,
    HealthResponse,
    InvestigationCreateRequest,
    StructuredFindingSchema,
)
from pydantic import ValidationError


def test_short_valid_query_is_accepted() -> None:
    """A concise valid product question must not be rejected merely because it is short."""
    req = InvestigationCreateRequest(user_query="Churn?")
    assert req.user_query == "Churn?"

    req2 = InvestigationCreateRequest(user_query="Latency up?")
    assert req2.user_query == "Latency up?"


def test_whitespace_and_empty_query_is_rejected() -> None:
    """Empty or whitespace-only queries must raise validation errors."""
    with pytest.raises(ValidationError):
        InvestigationCreateRequest(user_query="")

    with pytest.raises(ValidationError):
        InvestigationCreateRequest(user_query="   \n\t  ")


def test_overlong_query_is_rejected() -> None:
    """Queries exceeding the 2000 character maximum must be rejected."""
    long_query = "A" * 2001
    with pytest.raises(ValidationError) as exc_info:
        InvestigationCreateRequest(user_query=long_query)
    assert "exceeds the maximum allowed length" in str(exc_info.value)


def test_structured_evidence_schema_serialization() -> None:
    """Validate that structured findings and evidence ledger schemas preserve typed fields."""
    now = datetime.now(UTC)
    ledger_item = EvidenceLedgerItemSchema(
        ledger_entry_id="led_zendesk_101",
        source_type="zendesk",
        source_reference="ticket_101",
        finding="Customer reported indefinite pending state",
        support_excerpt="Transfer has been stuck in pending for 2 hours",
        confidence="high",
        retrieved_at=now,
    )
    assert ledger_item.source_type == "zendesk"
    assert ledger_item.confidence == "high"

    finding = StructuredFindingSchema(
        statement="17 tickets cite transfer delay error",
        epistemic_type="fact",
        evidence_ids=["led_zendesk_101"],
    )
    assert finding.epistemic_type == "fact"
    assert "led_zendesk_101" in finding.evidence_ids


def test_health_response_contains_no_secrets() -> None:
    """Health response model should never contain raw API keys or tokens."""
    health = HealthResponse(
        status="ok",
        process="healthy",
        investigation_service_initialized=True,
        active_investigations_count=0,
        dependencies={
            "openrouter_configured": True,
            "posthog_configured": True,
            "zendesk_mock_configured": True,
            "jira_mock_configured": True,
            "langsmith_tracing_enabled": False,
        },
    )
    serialized = health.model_dump_json()
    assert "sk-or-v1" not in serialized
    assert "phc_" not in serialized
    assert "api_key" not in serialized
