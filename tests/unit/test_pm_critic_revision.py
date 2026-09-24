"""Unit tests for bounded PM-Critic revision loop and terminal status invariants."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.domain.critic import CriticIssue, CriticReview
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.domain.specialists import CustomerFinding
from app.domain.zendesk import ZendeskTicket
from app.integrations.llm.client import LLMClient
from app.orchestration.graph import create_investigation_graph
from app.orchestration.state import (
    EvidenceAssessment,
    EvidenceLedgerEntry,
    InvestigationState,
)


@pytest.fixture(autouse=True)
def configure_deep_profile_for_multi_revision_tests(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("INVESTIGATION_PROFILE", "deep")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _make_sample_state() -> tuple[
    InvestigationState, ProductRecommendation, Evidence, EvidenceLedgerEntry, CustomerFinding
]:
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
        investigation_id="inv_loop_test",
        user_query="Why are transfers delayed?",
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
    return state, rec, ev, entry, finding


@pytest.mark.asyncio
async def test_critic_revision_loop_passes_on_revision_1() -> None:
    """Verify PM -> Critic REVISE -> PM revision -> Critic PASS terminates as completed."""
    from app.domain.plan import InvestigationPlan, InvestigationTask

    mock_llm = MagicMock(spec=LLMClient)
    state, initial_rec, ev, entry, finding = _make_sample_state()
    state.max_revisions = 1

    plan = InvestigationPlan(
        question_type="diagnostic",
        objectives=["Investigate why transfers delay"],
        tasks=[
            InvestigationTask(
                specialist="research", objective="Search tickets", priority="required"
            )
        ],
        required_sources=["zendesk"],
        success_condition="Evidence gathered from Zendesk",
    )
    assessment = EvidenceAssessment(
        sufficient_for_synthesis=True,
        has_blocking_gaps=False,
        identified_gaps=[],
    )

    critic_revise = CriticReview(
        decision="REVISE",
        issues=[
            CriticIssue(
                category="causal_overreach",
                claim="Client-side polling fallback will eliminate all delays",
                problem="Causal statement is absolute without experimental proof.",
                supporting_ledger_entry_ids=["research:r0:led_001"],
                required_change="Temper to 'is expected to mitigate perceived delay'.",
            )
        ],
        overall_assessment="Causal claim requires softening.",
        required_changes=["Temper causal claim in recommendation."],
    )

    revised_rec = initial_rec.model_copy(
        update={
            "recommendation": "Implement client-side polling fallback to mitigate perceived delay."
        }
    )

    critic_pass = CriticReview(
        decision="PASS",
        issues=[],
        overall_assessment="All claims verified and causality softened.",
        required_changes=[],
    )

    mock_llm.complete_structured = AsyncMock(
        side_effect=[
            plan,
            assessment,
            initial_rec,  # pm_synthesis
            critic_revise,  # critic (round 0)
            revised_rec,  # pm_revision (round 1)
            critic_pass,  # critic (round 1)
        ]
    )

    research_agent = MagicMock()
    research_agent.tool_call_count = 1
    research_agent.llm_call_count = 1
    research_agent.ledger.entries = [entry]
    from app.domain.specialists import SpecialistResult

    research_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="research",
            findings=[finding],
            overall_facts=["Fact 1"],
            overall_interpretations=["Interp 1"],
            tool_call_count=1,
            llm_call_count=1,
            investigation_complete=True,
        )
    )
    analytics_agent = MagicMock()
    engineering_agent = MagicMock()

    graph = create_investigation_graph(
        llm_client=mock_llm,
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
    )

    final_dict = await graph.ainvoke(state)
    final_state = InvestigationState.model_validate(final_dict)

    assert final_state.status == "completed"
    assert final_state.revision_count == 1
    assert final_state.max_revisions == 1
    assert len(final_state.critic_reviews) == 2
    assert final_state.recommendation is not None
    assert "mitigate perceived delay" in final_state.recommendation.recommendation


@pytest.mark.asyncio
async def test_critic_revision_loop_exhaustion_terminates_partial_with_immutable_rec() -> None:
    """Verify PM -> Critic REVISE -> PM revision 1 -> Critic REVISE -> PM revision 2 -> Critic REVISE -> terminates as partial.

    Also proves that state.recommendation receives unresolved Critic issues in open_questions
    via immutable copy without in-place mutation.
    """
    from app.domain.plan import InvestigationPlan, InvestigationTask

    mock_llm = MagicMock(spec=LLMClient)
    state, initial_rec, ev, entry, finding = _make_sample_state()

    plan = InvestigationPlan(
        question_type="diagnostic",
        objectives=["Investigate why transfers delay"],
        tasks=[
            InvestigationTask(
                specialist="research", objective="Search tickets", priority="required"
            )
        ],
        required_sources=["zendesk"],
        success_condition="Evidence gathered from Zendesk",
    )
    assessment = EvidenceAssessment(
        sufficient_for_synthesis=True,
        has_blocking_gaps=False,
        identified_gaps=[],
    )

    unresolved_issue = CriticIssue(
        category="causal_overreach",
        claim="Persistent ungrounded claim",
        problem="Persistent ungrounded causal claim remaining unaddressed.",
        supporting_ledger_entry_ids=["research:r0:led_001"],
        required_change="Tone down causal claim completely.",
    )
    critic_revise_1 = CriticReview(
        decision="REVISE",
        issues=[unresolved_issue],
        overall_assessment="Issue remains.",
        required_changes=["Tone down causal claim."],
    )
    critic_revise_2 = CriticReview(
        decision="REVISE",
        issues=[unresolved_issue],
        overall_assessment="Issue remains after revision 1.",
        required_changes=["Tone down causal claim."],
    )
    critic_revise_3 = CriticReview(
        decision="REVISE",
        issues=[unresolved_issue],
        overall_assessment="Issue remains after revision 2.",
        required_changes=["Tone down causal claim."],
    )

    mock_llm.complete_structured = AsyncMock(
        side_effect=[
            plan,
            assessment,
            initial_rec,  # pm_synthesis
            critic_revise_1,  # critic (0)
            initial_rec,  # pm_revision (1)
            critic_revise_2,  # critic (1)
            initial_rec,  # pm_revision (2)
            critic_revise_3,  # critic (2)
        ]
    )

    research_agent = MagicMock()
    research_agent.tool_call_count = 1
    research_agent.llm_call_count = 1
    research_agent.ledger.entries = [entry]
    from app.domain.specialists import SpecialistResult

    research_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="research",
            findings=[finding],
            overall_facts=["Fact 1"],
            overall_interpretations=["Interp 1"],
            tool_call_count=1,
            llm_call_count=1,
            investigation_complete=True,
        )
    )
    analytics_agent = MagicMock()
    engineering_agent = MagicMock()

    graph = create_investigation_graph(
        llm_client=mock_llm,
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
    )

    final_dict = await graph.ainvoke(state)
    final_state = InvestigationState.model_validate(final_dict)

    # 1. Hard bound enforced: max 2 revisions
    assert final_state.revision_count == 2
    # 2. Status terminates as partial due to unresolved material Critic issues
    assert final_state.status == "partial"
    # 3. Unresolved issues added to open_questions
    assert final_state.recommendation is not None
    assert any(
        "Unresolved Critic Issue - causal_overreach" in q
        for q in final_state.recommendation.open_questions
    )
    # 4. Immutability preserved: original initial_rec was NOT mutated in place
    assert not any("Unresolved Critic Issue" in q for q in initial_rec.open_questions)


@pytest.mark.asyncio
async def test_phase7_insufficient_for_synthesis_critic_pass_remains_partial() -> None:
    """CRITICAL INVARIANT TEST:

    Phase 7 sufficient_for_synthesis=False
    + all specialists complete
    + no tool errors
    + PM valid
    + Critic PASS
    -> final status MUST remain 'partial'.
    """
    from app.domain.plan import InvestigationPlan, InvestigationTask

    mock_llm = MagicMock(spec=LLMClient)
    state, rec, ev, entry, finding = _make_sample_state()

    plan = InvestigationPlan(
        question_type="diagnostic",
        objectives=["Investigate why transfers delay"],
        tasks=[
            InvestigationTask(
                specialist="research", objective="Search tickets", priority="required"
            )
        ],
        required_sources=["zendesk"],
        success_condition="Evidence gathered from Zendesk",
    )
    # Phase 7 assessment explicitly marks sufficient_for_synthesis = False
    assessment_insufficient = EvidenceAssessment(
        sufficient_for_synthesis=False,
        has_blocking_gaps=False,  # No follow-up triggered, but evidence remains partial
        identified_gaps=["Evidence sample lacks multi-region coverage"],
    )

    critic_pass = CriticReview(
        decision="PASS",
        issues=[],
        overall_assessment="Recommendation is sound for the available sample.",
        required_changes=[],
    )

    mock_llm.complete_structured = AsyncMock(
        side_effect=[
            plan,
            assessment_insufficient,
            rec,  # pm_synthesis
            critic_pass,  # critic
        ]
    )

    research_agent = MagicMock()
    research_agent.tool_call_count = 1
    research_agent.llm_call_count = 1
    research_agent.ledger.entries = [entry]
    from app.domain.specialists import SpecialistResult

    research_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="research",
            findings=[finding],
            overall_facts=["Fact 1"],
            overall_interpretations=["Interp 1"],
            tool_call_count=1,
            llm_call_count=1,
            investigation_complete=True,
        )
    )
    analytics_agent = MagicMock()
    engineering_agent = MagicMock()

    graph = create_investigation_graph(
        llm_client=mock_llm,
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
    )

    final_dict = await graph.ainvoke(state)
    final_state = InvestigationState.model_validate(final_dict)

    # Invariant assertion: Critic PASS does NOT upgrade partial evidence package into completed!
    assert final_state.status == "partial"
    assert final_state.sufficient_for_synthesis is False
