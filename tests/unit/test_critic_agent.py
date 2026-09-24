"""Unit tests for CriticAgent adversarial evaluation and bounded repair loop."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.critic import CriticAgent
from app.domain.critic import CriticIssue, CriticReview
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.domain.specialists import CustomerFinding
from app.domain.zendesk import ZendeskTicket
from app.integrations.llm.client import LLMClient
from app.orchestration.state import EvidenceLedgerEntry, InvestigationState


def _make_sample_state_and_rec() -> tuple[InvestigationState, ProductRecommendation]:
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
        investigation_id="inv_critic_test",
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
async def test_critic_agent_review_pass() -> None:
    mock_llm = MagicMock(spec=LLMClient)
    state, rec = _make_sample_state_and_rec()
    expected_review = CriticReview(
        decision="PASS",
        issues=[],
        overall_assessment="All claims are verified and grounded in authoritative ledger evidence.",
        required_changes=[],
    )
    mock_llm.complete_structured = AsyncMock(return_value=expected_review)

    agent = CriticAgent(llm_client=mock_llm, model_name="openai/gpt-5.4")
    review, calls_made = await agent.review(state, rec)

    assert review.decision == "PASS"
    assert len(review.issues) == 0
    assert calls_made == 1


@pytest.mark.asyncio
async def test_critic_agent_review_revise_with_provenance() -> None:
    mock_llm = MagicMock(spec=LLMClient)
    state, rec = _make_sample_state_and_rec()
    expected_review = CriticReview(
        decision="REVISE",
        issues=[
            CriticIssue(
                category="causal_overreach",
                claim="Client-side polling would eliminate all user confusion",
                problem="Causal claim is absolute without experimental verification.",
                supporting_ledger_entry_ids=["research:r0:led_001"],
                required_change="Temper causal phrasing to 'expected to reduce'.",
            )
        ],
        overall_assessment="Overly absolute causal claim requires softening.",
        required_changes=["Temper causal claim in recommendation."],
    )
    mock_llm.complete_structured = AsyncMock(return_value=expected_review)

    agent = CriticAgent(llm_client=mock_llm, model_name="openai/gpt-5.4")
    review, calls_made = await agent.review(state, rec)

    assert review.decision == "REVISE"
    assert len(review.issues) == 1
    assert review.issues[0].supporting_ledger_entry_ids == ["research:r0:led_001"]
    assert calls_made == 1


@pytest.mark.asyncio
async def test_critic_agent_bounded_repair_loop_on_invalid_ledger_id() -> None:
    """Verify CriticAgent catches unretrieved ledger reference in repair loop and repairs it."""
    mock_llm = MagicMock(spec=LLMClient)
    state, rec = _make_sample_state_and_rec()

    invalid_review = CriticReview(
        decision="REVISE",
        issues=[
            CriticIssue(
                category="unsupported_claim",
                claim="Claim",
                problem="Problem description in detail",
                supporting_ledger_entry_ids=["fake:r0:led_999"],  # Unretrieved!
                required_change="Fix the claim citation",
            )
        ],
        overall_assessment="Assessment",
        required_changes=["Change"],
    )
    valid_review = CriticReview(
        decision="REVISE",
        issues=[
            CriticIssue(
                category="unsupported_claim",
                claim="Claim",
                problem="Problem description in detail",
                supporting_ledger_entry_ids=["research:r0:led_001"],  # Validated!
                required_change="Fix the claim citation",
            )
        ],
        overall_assessment="Assessment",
        required_changes=["Change"],
    )
    mock_llm.complete_structured = AsyncMock(side_effect=[invalid_review, valid_review])

    agent = CriticAgent(llm_client=mock_llm, model_name="openai/gpt-5.4")
    review, calls_made = await agent.review(state, rec)

    assert review == valid_review
    assert calls_made == 2
