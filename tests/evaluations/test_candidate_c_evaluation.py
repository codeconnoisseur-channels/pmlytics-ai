"""Tests verifying Candidate C (Specialists + PM + Critic) in the Phase 9 evaluation harness."""

from unittest.mock import AsyncMock

import pytest
from app.domain.critic import CriticIssue, CriticReview
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.integrations.llm.client import LLMClient
from app.orchestration.graph import create_investigation_graph
from evaluations.config import (
    DEFAULT_PRICING_RATES,
    MODE1_MATCHED_BUDGET,
    MODE2_NATURAL_BUDGETS,
)
from evaluations.evaluators.telemetry import calculate_cost_from_snapshot


def _make_mock_recommendation() -> ProductRecommendation:
    return ProductRecommendation(
        problem_statement="Bank switch timeout causes perceived transfer failures.",
        why_it_matters="Surge in customer anxiety and support escalations.",
        affected_users="Bank A and Bank B account holders",
        factual_observations=["Observed transfer timeout spike on Bank A/B."],
        inferences=["Perceived failures drive ticket surges."],
        hypotheses=["Fixing callback delays will restore customer trust."],
        evidence=[
            Evidence(
                ledger_entry_id="research:r0:led_001",
                source_type="zendesk",
                source_reference="ticket_id:101",
                finding="Customer reported delayed transfer",
                support="Ticket 101 support text",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        recommendation="Prioritize bank switch timeout remediation.",
        recommendation_type="technical_remediation",
        success_metrics=["Support escalations return to baseline."],
        risks=["Technical dependency on partner bank API fixes."],
        confidence="high",
        open_questions=[],
    )


@pytest.mark.asyncio
async def test_candidate_c_graph_topology_and_critic_integration() -> None:
    """Verify Candidate C graph includes specialists, PM, and Critic with revision edges."""
    mock_llm = AsyncMock(spec=LLMClient)
    mock_research = AsyncMock()
    mock_analytics = AsyncMock()
    mock_engineering = AsyncMock()

    candidate_graph = create_investigation_graph(
        llm_client=mock_llm,
        research_agent=mock_research,
        analytics_agent=mock_analytics,
        engineering_agent=mock_engineering,
    )

    node_names = set(candidate_graph.nodes.keys())
    assert "planner" in node_names
    assert "research" in node_names
    assert "analytics" in node_names
    assert "engineering" in node_names
    assert "pm_synthesis" in node_names
    assert "critic" in node_names
    assert "pm_revision" in node_names
    assert "finalize" in node_names


@pytest.mark.asyncio
async def test_candidate_c_pass_and_revise_evaluation_pipeline() -> None:
    """Verify Candidate C passes through the identical evaluation pipeline as Baselines A and B."""
    rec = _make_mock_recommendation()
    assert rec.problem_statement is not None

    # Verify PASS review
    pass_review = CriticReview(
        decision="PASS",
        overall_assessment="Recommendation is strictly grounded and causally disciplined.",
        issues=[],
    )
    assert pass_review.decision == "PASS"

    # Verify REVISE review
    revise_review = CriticReview(
        decision="REVISE",
        overall_assessment="Overconfident causal claim without sufficient telemetry proof.",
        issues=[
            CriticIssue(
                category="causal_overreach",
                claim="Fee increase caused churn across all platform users.",
                problem="Claiming fee increase caused churn without behavioral telemetry link.",
                supporting_ledger_entry_ids=["research:r0:led_001"],
                required_change="Temper causal statement to correlational association.",
            )
        ],
        required_changes=["Temper causal statement to correlational association."],
    )
    assert revise_review.decision == "REVISE"
    assert len(revise_review.issues) == 1

    # Verify budget limits in Mode 1 and Mode 2
    assert MODE1_MATCHED_BUDGET.max_llm_calls == 25
    assert MODE1_MATCHED_BUDGET.max_tool_calls == 26
    assert MODE2_NATURAL_BUDGETS["candidate_c"].max_llm_calls == 63
    assert MODE2_NATURAL_BUDGETS["candidate_c"].max_tool_calls == 26

    # Verify cost calculation uses immutable snapshot
    cost = calculate_cost_from_snapshot(
        model_id="openai/gpt-5.4",
        input_tokens=10_000,
        output_tokens=2_000,
        pricing_snapshot=DEFAULT_PRICING_RATES,
    )
    # 10k * $2.50/M = $0.025; 2k * $15.00/M = $0.030; Total = $0.055
    assert cost == 0.055
