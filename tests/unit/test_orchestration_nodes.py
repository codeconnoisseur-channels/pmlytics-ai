"""Unit tests for planner, assessment, and finalize nodes."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.ledger import EvidenceLedgerEntry
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.plan import InvestigationPlan
from app.domain.specialists import CustomerFinding
from app.domain.zendesk import ZendeskTicket
from app.integrations.llm.client import LLMClient
from app.orchestration.nodes.assessment import AssessmentNode
from app.orchestration.nodes.finalize import finalize_investigation_node
from app.orchestration.nodes.planner import PlannerNode
from app.orchestration.state import (
    EvidenceAssessment,
    InvestigationState,
)


def _make_sample_ticket() -> ZendeskTicket:
    return ZendeskTicket(
        id=101,
        subject="Ticket 101",
        description="Desc 101",
        status="open",
        priority="normal",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000001",
        tags=[],
    )


@pytest.mark.asyncio
async def test_planner_node_bounded_repair_loop() -> None:
    """Verify that PlannerNode executes at most 1 initial call + 2 repairs (3 total)."""
    mock_llm = MagicMock(spec=LLMClient)
    # Always raise schema validation error
    mock_llm.complete_structured = AsyncMock(side_effect=ValueError("Invalid plan schema"))

    planner = PlannerNode(llm_client=mock_llm)
    state = InvestigationState(investigation_id="inv_test", user_query="Why are transfers delayed?")

    result = await planner(state)

    # Must call exactly 3 times (1 initial + 2 repairs)
    assert mock_llm.complete_structured.call_count == 3
    assert result["budget_usage"].planner_llm_calls == 3
    # Fallback plan emitted
    assert isinstance(result["plan"], InvestigationPlan)
    assert len(result["tool_errors"]) == 1
    assert result["tool_errors"][0].error_type == "upstream_error"


@pytest.mark.asyncio
async def test_assessment_node_bounded_repair_loop() -> None:
    """Verify that AssessmentNode executes at most 1 call in Standard mode, and 3 calls in Deep mode."""
    from unittest.mock import patch

    state = InvestigationState(investigation_id="inv_test", user_query="Why are transfers delayed?")

    # 1. Standard mode: exactly 1 call (no retries), deterministic fallback
    mock_llm_std = MagicMock(spec=LLMClient)
    mock_llm_std.complete_structured = AsyncMock(
        side_effect=ValueError("Invalid assessment schema")
    )
    assessment_node_std = AssessmentNode(llm_client=mock_llm_std)

    with patch("app.orchestration.nodes.assessment.get_settings") as mock_settings:
        mock_settings.return_value.investigation_profile = "standard"
        result_std = await assessment_node_std(state)
        assert mock_llm_std.complete_structured.call_count == 1
        assert result_std["budget_usage"].assessment_llm_calls == 1
        assert result_std["sufficient_for_synthesis"] is False
        assert result_std["assessment"].has_blocking_gaps is True

    # 2. Deep mode: 1 initial call + 2 repairs (3 calls total)
    mock_llm_deep = MagicMock(spec=LLMClient)
    mock_llm_deep.complete_structured = AsyncMock(
        side_effect=ValueError("Invalid assessment schema")
    )
    assessment_node_deep = AssessmentNode(llm_client=mock_llm_deep)

    with patch("app.orchestration.nodes.assessment.get_settings") as mock_settings:
        mock_settings.return_value.investigation_profile = "deep"
        result_deep = await assessment_node_deep(state)
        assert mock_llm_deep.complete_structured.call_count == 3
        assert result_deep["budget_usage"].assessment_llm_calls == 3
        assert result_deep["sufficient_for_synthesis"] is False
        assert result_deep["assessment"].has_blocking_gaps is True


def test_finalize_node_deterministic_statuses() -> None:
    """Verify deterministic status assignment across permutations."""
    # 1. Zero evidence -> "failed"
    state_empty = InvestigationState(investigation_id="1", user_query="q")
    res_empty = finalize_investigation_node(state_empty)
    assert res_empty["status"] == "failed"
    assert res_empty["sufficient_for_synthesis"] is False

    # Create dummy verified evidence
    entry = EvidenceLedgerEntry(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="ref:1",
        retrieved_at=datetime.now(UTC),
        data_summary="Summary",
        typed_payload=_make_sample_ticket(),
    )
    ev = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="ref:1",
        finding="Finding",
        support="Support",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Finding description",
        facts=["Fact"],
        interpretations=["Interp"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="delay_complaint",
    )

    # 2. Evidence present, sufficient=True, zero errors, zero blocking gaps, valid rec, Critic PASS -> "completed"
    from app.domain.critic import CriticReview
    from app.domain.recommendation import (
        ProductRecommendation,
    )

    valid_rec = ProductRecommendation(
        problem_statement="Problem statement describing the issue in detail.",
        why_it_matters="Why it matters to users and product business metrics.",
        affected_users="Mobile checkout users",
        factual_observations=["Fact 1 observed in support tickets"],
        inferences=["Interp 1 inferred from facts"],
        hypotheses=["Hypo 1 plausible explanation"],
        evidence=[ev],
        recommendation="Deploy client-side polling fallback immediately.",
        recommendation_type="prioritise",
        risks=["Minor increase in server traffic"],
        success_metrics=["Tickets drop by 50% within 48 hours"],
        confidence="high",
    )
    pass_review = CriticReview(
        decision="PASS",
        issues=[],
        overall_assessment="All claims are corroborated and causality is appropriately restrained.",
        required_changes=[],
    )

    assessment_good = EvidenceAssessment(
        sufficient_for_synthesis=True,
        has_blocking_gaps=False,
    )
    state_completed = InvestigationState(
        investigation_id="2",
        user_query="q",
        evidence_ledger_entries={"research:led_001": entry},
        customer_findings=[finding],
        assessment=assessment_good,
        sufficient_for_synthesis=True,
        specialist_completions={"research": True},
        recommendation=valid_rec,
        critic_reviews=[pass_review],
    )
    res_completed = finalize_investigation_node(state_completed)
    assert res_completed["status"] == "completed"
    assert res_completed["sufficient_for_synthesis"] is True

    # 3. Evidence present, but has blocking gaps -> "partial"
    assessment_gaps = EvidenceAssessment(
        sufficient_for_synthesis=False,
        has_blocking_gaps=True,
        identified_gaps=["Gap 1"],
    )
    state_partial = InvestigationState(
        investigation_id="3",
        user_query="q",
        evidence_ledger_entries={"research:led_001": entry},
        customer_findings=[finding],
        assessment=assessment_gaps,
        sufficient_for_synthesis=False,
    )
    res_partial = finalize_investigation_node(state_partial)
    assert res_partial["status"] == "partial"
    assert res_partial["sufficient_for_synthesis"] is False


def test_finalize_investigation_node_incomplete_specialist_yields_partial() -> None:
    """Verify that a specialist returning investigation_complete=False forces 'partial' status

    even when assessment claims sufficiency and there are no tool errors.
    """
    entry = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ref:1",
        retrieved_at=datetime.now(UTC),
        data_summary="Summary",
        typed_payload=_make_sample_ticket(),
    )
    ev = Evidence(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ref:1",
        finding="Finding",
        support="Support",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Finding description",
        facts=["Fact"],
        interpretations=["Interp"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="delay_complaint",
    )

    assessment_good = EvidenceAssessment(
        sufficient_for_synthesis=True,
        has_blocking_gaps=False,
    )

    # Specialist legitimately returned investigation_complete=False (e.g. budget exhaustion)
    state_incomplete_specialist = InvestigationState(
        investigation_id="4",
        user_query="q",
        evidence_ledger_entries={"research:r0:led_001": entry},
        customer_findings=[finding],
        assessment=assessment_good,
        sufficient_for_synthesis=True,
        tool_errors=[],  # Zero tool errors!
        specialist_completions={"research": False},  # Incomplete specialist!
    )

    res = finalize_investigation_node(state_incomplete_specialist)
    assert res["status"] == "partial"
    assert res["sufficient_for_synthesis"] is False


def test_finalize_investigation_node_missing_assigned_specialist_yields_partial() -> None:
    """Verify that an assigned specialist that never recorded completion forces 'partial' status."""
    from app.domain.plan import InvestigationPlan, InvestigationTask

    entry = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ref:1",
        retrieved_at=datetime.now(UTC),
        data_summary="Summary",
        typed_payload=_make_sample_ticket(),
    )
    ev = Evidence(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ref:1",
        finding="Finding",
        support="Support",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Finding description",
        facts=["Fact"],
        interpretations=["Interp"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="delay_complaint",
    )

    plan = InvestigationPlan(
        question_type="diagnostic",
        objectives=["Investigate issue"],
        tasks=[
            InvestigationTask(
                specialist="research",
                objective="Search customer tickets",
                priority="required",
            ),
            InvestigationTask(
                specialist="engineering",
                objective="Inspect technical bugs",
                priority="required",
            ),
        ],
        required_sources=["zendesk", "jira"],
        success_condition="Evidence from both",
    )

    assessment_good = EvidenceAssessment(
        sufficient_for_synthesis=True,
        has_blocking_gaps=False,
    )

    # Only research recorded completion; engineering is missing from completions
    state_missing_specialist = InvestigationState(
        investigation_id="5",
        user_query="q",
        plan=plan,
        evidence_ledger_entries={"research:r0:led_001": entry},
        customer_findings=[finding],
        assessment=assessment_good,
        sufficient_for_synthesis=True,
        tool_errors=[],
        specialist_completions={"research": True},  # engineering missing!
    )

    res = finalize_investigation_node(state_missing_specialist)
    assert res["status"] == "partial"
    assert res["sufficient_for_synthesis"] is False
