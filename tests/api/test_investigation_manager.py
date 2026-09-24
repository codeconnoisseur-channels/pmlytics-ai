"""Tests for in-memory InvestigationManager and lifecycle state transitions."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.ledger import EvidenceLedgerEntry
from app.api.manager import InvestigationManager
from app.domain.critic import CriticReview
from app.domain.evidence import Evidence
from app.domain.recommendation import ProductRecommendation
from app.domain.zendesk import ZendeskTicket
from app.orchestration.state import InvestigationState


@pytest.mark.asyncio
async def test_investigation_manager_lifecycle_mapping() -> None:
    """Verify that LangGraph node transitions update the presentation status."""
    mock_service = MagicMock()

    # Stub investigate to hang until we trigger it
    async def fake_investigate(user_query, investigation_id, context, tracer):
        # Simulate node events via tracer
        tracer._notify_listeners("start", "planner", {})
        await asyncio.sleep(0.01)
        tracer._notify_listeners("start", "research", {})
        await asyncio.sleep(0.01)
        tracer._notify_listeners("start", "pm_synthesis", {})
        await asyncio.sleep(0.01)
        tracer._notify_listeners("start", "critic", {})
        await asyncio.sleep(0.01)

        rec = ProductRecommendation(
            problem_statement="Problem statement of sufficient length",
            why_it_matters="Why it matters of sufficient length",
            affected_users="Target user population segment",
            factual_observations=["Factual observation 1"],
            inferences=["Inference deduction 1"],
            hypotheses=["Hypothesis theory 1"],
            evidence=[
                Evidence(
                    ledger_entry_id="led_1",
                    source_type="zendesk",
                    source_reference="ref",
                    finding="find",
                    support="sup",
                    confidence="high",
                )
            ],
            recommendation="Concrete recommended action statement",
            recommendation_type="technical_remediation",
            confidence="high",
            success_metrics=["Metric 1"],
            risks=["Risk 1"],
        )
        now = datetime.now(UTC)
        ticket = ZendeskTicket(
            id=1,
            requester_id="usr_000001",
            subject="Transfer failed",
            description="My transfer failed",
            status="open",
            priority="high",
            channel="web",
            created_at=now,
            updated_at=now,
        )
        return InvestigationState(
            investigation_id=investigation_id,
            user_query=user_query,
            status="completed",
            recommendation=rec,
            evidence_ledger_entries={
                "led_1": EvidenceLedgerEntry(
                    ledger_entry_id="led_1",
                    source_type="zendesk",
                    source_reference="ref",
                    data_summary="Customer reported a transfer failure",
                    retrieved_at=now,
                    typed_payload=ticket,
                )
            },
            critic_reviews=[
                CriticReview(
                    decision="PASS",
                    overall_assessment="The recommendation is supported.",
                    issues=[],
                    required_changes=[],
                )
            ],
        )

    mock_service.investigate = AsyncMock(side_effect=fake_investigate)
    manager = InvestigationManager(service=mock_service)

    record = manager.create_investigation(user_query="Why are transactions failing?")
    assert record.status == "pending"

    # Wait for task completion
    await record.task

    assert record.status == "completed"
    assert record.final_state is not None
    assert record.final_state.recommendation is not None


@pytest.mark.asyncio
async def test_investigation_manager_handles_background_failure_cleanly() -> None:
    """When the underlying graph fails, the manager transitions to 'failed' and never raises unhandled errors."""
    mock_service = MagicMock()
    mock_service.investigate = AsyncMock(side_effect=RuntimeError("Simulated LLM Gateway Outage"))
    manager = InvestigationManager(service=mock_service)

    record = manager.create_investigation(user_query="Test failure handling")
    await record.task

    assert record.status == "failed"
    assert record.error == "The investigation could not be completed. Please try again."
    assert "Simulated LLM Gateway Outage" not in str(record.error)
    assert record.completed_at is not None


@pytest.mark.asyncio
async def test_sse_subscription_yields_immediate_snapshot() -> None:
    """Subscribing to an investigation returns an initial snapshot event immediately."""
    mock_service = MagicMock()
    mock_service.investigate = AsyncMock(return_value=MagicMock(recommendation=None))
    manager = InvestigationManager(service=mock_service)

    record = manager.create_investigation(user_query="Test snapshot")

    events = []
    async for ev in manager.subscribe(record.investigation_id):
        events.append(ev)
        break  # Just check first snapshot event

    assert len(events) >= 1
    assert events[0]["event"] == "snapshot"
    assert events[0]["investigation_id"] == record.investigation_id
    assert "status" in events[0]
