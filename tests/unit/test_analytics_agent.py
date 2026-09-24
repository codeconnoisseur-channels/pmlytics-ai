"""Unit tests verifying AnalyticsAgent behavior, analytical intent execution, and epistemic boundaries."""

from typing import Any, TypeVar
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.analytics import AnalyticsAgent, AnalyticsTask
from app.domain.analytics import AnalyticsQueryResult
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.investigation_scope import InvestigationScope
from app.domain.specialists import AnalyticsFinding, SpecialistResult
from app.integrations.llm.client import LLMMessage, LLMResponse, ToolCallRequest
from app.integrations.posthog.adapter import PostHogAdapter
from app.tools.registry import ToolRegistry
from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class ScriptedMockLLM:
    """Mock LLM for testing AnalyticsAgent flows."""

    def __init__(
        self,
        tool_responses: list[LLMResponse],
        structured_responses: list[Any] | None = None,
    ) -> None:
        self.tool_responses = list(tool_responses)
        self.structured_responses = list(structured_responses or [])
        self.call_count = 0
        self.history: list[list[LLMMessage]] = []

    async def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        self.call_count += 1
        self.history.append(messages)
        if self.tool_responses:
            return self.tool_responses.pop(0)
        return LLMResponse(content="Default response", tool_calls=[], model_used=model)

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        model: str,
        response_model: type[TModel],
        temperature: float = 0.0,
    ) -> TModel:
        self.call_count += 1
        self.history.append(messages)
        if self.structured_responses:
            return self.structured_responses.pop(0)  # type: ignore[no-any-return]
        raise ValueError("No scripted structured response available")


@pytest.mark.asyncio
async def test_analytics_agent_funnel_and_duration_flow() -> None:
    """Verify AnalyticsAgent queries funnel, then lifecycle duration, producing grounded findings."""
    mock_funnel_res = AnalyticsQueryResult(
        query_description="Funnel from initiated to completed",
        metric="conversion_rate",
        rows=[
            {"step": "transfer_started", "count": 1000, "conversion_rate": 1.0},
            {"step": "transfer_submitted", "count": 800, "conversion_rate": 0.8},
            {"step": "transfer_completed", "count": 200, "conversion_rate": 0.25},
        ],
        raw_count=3,
        dimensions=["step"],
    )
    mock_duration_res = AnalyticsQueryResult(
        query_description="Lifecycle duration from submitted to completed",
        metric="duration_ms",
        value=48500.0,
        rows=[
            {"avg_duration_ms": 15420.0, "p95_duration_ms": 48500.0},
        ],
        raw_count=1,
    )

    mock_posthog = MagicMock(spec=PostHogAdapter)
    mock_posthog.query_funnel = AsyncMock(return_value=mock_funnel_res)
    mock_posthog.query_lifecycle_duration = AsyncMock(return_value=mock_duration_res)

    reg = ToolRegistry.create_default(
        zendesk_adapter=MagicMock(),
        posthog_adapter=mock_posthog,
        jira_adapter=MagicMock(),
    )
    toolset = reg.get_toolset_for_role("analytics")

    ev1 = Evidence(
        ledger_entry_id="analytics:led_001",
        source_type="posthog",
        source_reference="query:funnel:transfer_started->transfer_submitted->transfer_completed",
        finding="Funnel drop-off between transfer_submitted and transfer_completed is 75%",
        support="transfer_completed count: 200 out of 800 submitted (25% conversion)",
        confidence=EvidenceConfidence.HIGH,
    )
    ev2 = Evidence(
        ledger_entry_id="analytics:led_002",
        source_type="posthog",
        source_reference="query:lifecycle_duration:transfer_submitted->transfer_completed",
        finding="p95 lifecycle duration between submission and completion is 48.5 seconds",
        support="p95_duration_ms: 48500.0",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = AnalyticsFinding(
        finding="Substantial drop-off and latency between transfer submission and completion",
        facts=[
            "200 of 800 submitted transfers reached completion (25% step conversion)",
            "p95 completion duration is 48.5 seconds",
        ],
        interpretations=["Users experience low completion rates alongside elevated tail latency"],
        hypotheses=[
            "Extended latency is associated with abandonment prior to completion confirmation"
        ],
        evidence=[ev1, ev2],
        confidence=EvidenceConfidence.HIGH,
        metric="funnel_step_conversion",
        value="25.0%",
        comparison="Baseline overall completion rate is 92%",
        segment="All users",
        time_period="Last 7 days",
    )
    synthesis_result = SpecialistResult[AnalyticsFinding](
        agent_role="analytics",
        findings=[finding],
        overall_facts=["25% conversion from submitted to completed", "p95 is 48.5s"],
        overall_interpretations=["Severe bottleneck at completion step"],
        overall_hypotheses=["Delay causes perceived failure"],
        contradictions=[],
        unanswered_questions=[],
        limitations=["Only analyzed completed transfers for duration"],
        tool_call_count=2,
        llm_call_count=3,
        investigation_complete=True,
    )

    tool_responses = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="c1",
                    function_name="query_analytics",
                    arguments={
                        "intent": "funnel",
                        "description": "Analyze conversion funnel",
                        "time_range_days": 14,
                        "steps": [
                            "transfer_started",
                            "transfer_submitted",
                            "transfer_completed",
                            "transfer_failed",
                        ],
                    },
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="c2",
                    function_name="query_analytics",
                    arguments={
                        "intent": "lifecycle_duration",
                        "description": "Analyze transfer duration",
                        "time_range_days": 14,
                        "start_event": "transfer_submitted",
                        "end_event": "transfer_completed",
                        "property_name": "duration_ms",
                    },
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(content="Done querying", tool_calls=[], model_used="openai/gpt-5.4"),
    ]

    llm = ScriptedMockLLM(
        tool_responses=tool_responses,
        structured_responses=[synthesis_result],
    )
    agent = AnalyticsAgent(
        toolset=toolset,
        llm_client=llm,
        model_name="openai/gpt-5.4",
    )

    task = AnalyticsTask(
        user_question="What is the transfer drop-off rate?",
        objective="Analyze transfer conversion drop-off and latency",
        scope=InvestigationScope(
            start_time="2026-08-05T00:00:00Z",
            end_time="2026-08-18T23:59:59Z",
        ),
    )
    res = await agent.execute(task)

    assert res.agent_role == "analytics"
    assert res.tool_call_count == 2
    assert res.llm_call_count == 4
    assert res.investigation_complete is True
    assert len(res.findings) == 1
    assert res.findings[0].metric == "funnel_step_conversion"
    assert res.findings[0].value == "25.0%"
    funnel_kwargs = mock_posthog.query_funnel.await_args.kwargs
    assert funnel_kwargs["time_range_days"] is None
    assert funnel_kwargs["steps"] == [
        "transfer_started",
        "transfer_submitted",
        "transfer_completed",
    ]
    assert funnel_kwargs["start_time"] == "2026-08-05T00:00:00+00:00"
    assert funnel_kwargs["end_time"] == "2026-08-18T23:59:59+00:00"
