"""Unit tests for Baseline A (Single Agent) and Baseline B (Specialist + PM without Critic)."""

from datetime import UTC, datetime
from typing import Any, Literal
from unittest.mock import AsyncMock

import pytest
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.domain.zendesk import ZendeskTicket
from app.integrations.llm.client import LLMClient
from app.tools.base import BaseTool, ToolError
from evaluations.baselines.single_agent import SingleAgentAction, SingleAgentBaseline
from evaluations.baselines.specialist_no_critic import create_specialist_no_critic_graph


class MockTool(BaseTool):
    """Mock tool for testing single agent execution."""

    name: str = "search_tickets"
    description: str = "Mock search tickets tool"

    def _get_source_type(self) -> Literal["zendesk", "posthog", "jira"]:
        return "zendesk"

    async def _execute(self, input_data: Any) -> tuple[Any, str]:
        ticket = ZendeskTicket(
            id=101,
            requester_id="usr_abc123",
            subject="Transfer delayed for hours",
            description="Transfer delayed for hours",
            status="open",
            priority="normal",
            channel="email",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return ticket, "ticket_id:101"

    def _map_error(self, exc: Exception) -> ToolError:
        return ToolError(error_type="upstream_error", message=str(exc))


@pytest.mark.asyncio
async def test_baseline_a_single_agent_execution_and_synthesis() -> None:
    """Verify Baseline A calls tools, populates ledger, and synthesizes a recommendation."""
    mock_llm = AsyncMock(spec=LLMClient)
    mock_tool = MockTool()

    agent = SingleAgentBaseline(
        llm_client=mock_llm,
        tools=[mock_tool],
        model_name="openai/gpt-5.4",
    )

    action_call = SingleAgentAction(
        action_type="tool_call",
        rationale="Query Zendesk for transfer delay tickets",
        tool_name="search_tickets",
        tool_input={"query": "transfers"},
    )
    action_stop = SingleAgentAction(
        action_type="finish",
        rationale="Enough evidence retrieved, synthesize recommendation",
    )
    rec = ProductRecommendation(
        problem_statement="Problem statement explaining customer issues.",
        why_it_matters="Impact statement explaining why it matters.",
        affected_users="Segment A users",
        factual_observations=["Fact 1 observed"],
        inferences=["Inference 1 deduced"],
        hypotheses=["Hypothesis 1 proposed"],
        evidence=[
            Evidence(
                ledger_entry_id="single_agent:led_001",
                source_type="zendesk",
                source_reference="ticket_id:101",
                finding="Customer reported delayed transfer",
                support="Transfer delayed for hours",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        recommendation="Recommended product action to fix the bug.",
        recommendation_type="technical_remediation",
        success_metrics=["Metric 1"],
        risks=["Risk 1"],
        confidence="high",
        open_questions=[],
    )

    # First call: action_call, Second call: action_stop, Third call: rec
    mock_llm.complete_structured.side_effect = [action_call, action_stop, rec]

    state = await agent.execute(
        user_query="Why are transfers failing?",
        investigation_id="inv_base_a",
        mode="mode1_matched",
    )

    assert state.investigation_id == "inv_base_a"
    assert state.recommendation is not None
    assert len(state.evidence_ledger_entries) == 1
    assert "single_agent:led_001" in state.evidence_ledger_entries


def test_baseline_b_graph_topology_bypasses_critic() -> None:
    """Verify Baseline B graph includes specialists and PM synthesis, but explicitly excludes Critic."""
    mock_llm = AsyncMock(spec=LLMClient)
    mock_research = AsyncMock()
    mock_analytics = AsyncMock()
    mock_engineering = AsyncMock()

    graph = create_specialist_no_critic_graph(
        llm_client=mock_llm,
        research_agent=mock_research,
        analytics_agent=mock_analytics,
        engineering_agent=mock_engineering,
    )

    # Verify nodes
    node_names = set(graph.nodes.keys())
    assert "planner" in node_names
    assert "research" in node_names
    assert "analytics" in node_names
    assert "engineering" in node_names
    assert "assessment" in node_names
    assert "pm_synthesis" in node_names
    assert "finalize" in node_names
    assert "critic" not in node_names
    assert "pm_revision" not in node_names
