"""Unit tests for PMAgent synthesis and bounded repair loop."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.pm import PMAgent
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.domain.specialists import CustomerFinding
from app.domain.zendesk import ZendeskTicket
from app.integrations.llm.client import LLMClient
from app.orchestration.state import EvidenceLedgerEntry, InvestigationState


def _make_sample_state() -> tuple[InvestigationState, ProductRecommendation]:
    now = datetime.now(UTC)
    ticket = ZendeskTicket(
        id=101,
        subject="Transfer delayed",
        description="Desc",
        status="open",
        priority="normal",
        channel="web",
        created_at=now,
        updated_at=now,
        requester_id="usr_000001",
        tags=[],
    )
    entry = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        retrieved_at=now,
        data_summary="Customer complains of transfer delay",
        typed_payload=ticket,
    )
    ev = Evidence(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer complains of transfer delay",
        support="Ticket 101",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Customer complains of transfer delay",
        facts=["Ticket 101 filed"],
        interpretations=["Transfer latency spike observed"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="transfer_delay",
    )
    state = InvestigationState(
        investigation_id="inv_pm_test",
        user_query="Why are transfers delayed?",
        evidence_ledger_entries={"research:r0:led_001": entry},
        customer_findings=[finding],
    )
    rec = ProductRecommendation(
        problem_statement="Customers experience transaction delays during peak hours.",
        why_it_matters="Degrades user trust and increases support ticket burden.",
        affected_users="Mobile wallet transfer users",
        factual_observations=["Customer complains of transfer delay in Ticket 101"],
        inferences=["Users experience transaction latency spikes"],
        hypotheses=["Client-side polling fallback would alleviate confusion"],
        evidence=[ev],
        recommendation="Implement client-side polling fallback.",
        recommendation_type="prioritise",
        risks=["Increased server polling traffic"],
        success_metrics=["Transfer tickets drop by 50%"],
        confidence="high",
    )
    return state, rec


@pytest.mark.asyncio
async def test_pm_agent_synthesize_success_first_attempt() -> None:
    mock_llm = MagicMock(spec=LLMClient)
    state, expected_rec = _make_sample_state()
    mock_llm.complete_structured = AsyncMock(return_value=expected_rec)

    agent = PMAgent(llm_client=mock_llm, model_name="openai/gpt-5.4")
    rec, calls_made = await agent.synthesize(state)

    assert rec == expected_rec
    assert calls_made == 1


@pytest.mark.asyncio
async def test_pm_agent_synthesize_bounded_repair_loop() -> None:
    """Verify PMAgent attempts repair up to 2 times (3 calls total) and succeeds on 2nd attempt."""
    mock_llm = MagicMock(spec=LLMClient)
    state, expected_rec = _make_sample_state()
    mock_llm.complete_structured = AsyncMock(
        side_effect=[ValueError("Missing required field 'why_it_matters'"), expected_rec]
    )

    agent = PMAgent(llm_client=mock_llm, model_name="openai/gpt-5.4")
    rec, calls_made = await agent.synthesize(state)

    assert rec == expected_rec
    assert calls_made == 2


@pytest.mark.asyncio
async def test_pm_agent_synthesize_failure_exhaustion_returns_none() -> None:
    """Verify PMAgent returns None (safe fallback without hallucinating dummy metrics) when budget exhausted."""
    mock_llm = MagicMock(spec=LLMClient)
    state, _ = _make_sample_state()
    mock_llm.complete_structured = AsyncMock(
        side_effect=[
            ValueError("Attempt 1 failure"),
            ValueError("Attempt 2 failure"),
            ValueError("Attempt 3 failure"),
        ]
    )

    agent = PMAgent(llm_client=mock_llm, model_name="openai/gpt-5.4")
    rec, calls_made = await agent.synthesize(state)

    assert rec is None
    assert calls_made == 3
