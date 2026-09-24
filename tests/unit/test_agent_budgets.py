"""Unit tests verifying strict hard dual budget enforcement (tool calls vs LLM calls)."""

from datetime import UTC, datetime
from typing import Any, TypeVar
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.research import ResearchAgent, ResearchTask
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.specialists import CustomerFinding, SpecialistResult
from app.domain.zendesk import ZendeskTicket
from app.integrations.llm.client import LLMMessage, LLMResponse, ToolCallRequest
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.tools.registry import RoleBoundToolset, ToolRegistry
from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class ScriptedMockLLM:
    """Mock LLM client that returns scripted responses and records call count."""

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


@pytest.fixture
def mock_toolset() -> RoleBoundToolset:
    """Create a research toolset with a mock Zendesk adapter."""
    mock_adapter = MagicMock(spec=ZendeskAdapter)
    ticket = ZendeskTicket(
        id=1,
        subject="Delay complaint",
        description="Transfer took 2 hours",
        status="solved",
        priority="high",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000001",
        tags=[],
    )
    mock_adapter.get_ticket = AsyncMock(return_value=ticket)
    mock_adapter.search_tickets = AsyncMock(return_value=([ticket], 1))
    mock_adapter.get_ticket_comments = AsyncMock(return_value=[])

    reg = ToolRegistry.create_default(
        zendesk_adapter=mock_adapter,
        posthog_adapter=MagicMock(),
        jira_adapter=MagicMock(),
    )
    return reg.get_toolset_for_role("research")


@pytest.mark.asyncio
async def test_tool_budget_stops_loop_even_if_llm_requests_more(
    mock_toolset: RoleBoundToolset,
) -> None:
    """Verify tool loop halts when tool_call_budget (10) is reached, even if LLM keeps requesting tools."""
    infinite_tool_responses = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id=f"call_{i}_a",
                    function_name="get_ticket",
                    arguments={"ticket_id": 1},
                ),
                ToolCallRequest(
                    id=f"call_{i}_b",
                    function_name="get_ticket",
                    arguments={"ticket_id": 1},
                ),
            ],
            model_used="openai/gpt-5.4",
        )
        for i in range(20)
    ]

    ev = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="ticket_id:1",
        finding="Delay observed",
        support="ticket.description",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Delay reported",
        facts=["Fact 1"],
        interpretations=["Interp 1"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="delay",
    )
    synthesis_result = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        overall_facts=["Fact 1"],
        overall_interpretations=["Interp 1"],
        tool_call_count=10,
        llm_call_count=6,
        investigation_complete=True,
    )

    llm = ScriptedMockLLM(
        tool_responses=infinite_tool_responses,
        structured_responses=[synthesis_result],
    )
    agent = ResearchAgent(
        toolset=mock_toolset,
        llm_client=llm,
        model_name="openai/gpt-5.4",
        tool_call_budget=10,
        llm_call_budget=15,
    )

    task = ResearchTask(
        user_question="Why are customers reporting delays?",
        objective="Investigate delay complaints",
    )
    res = await agent.execute(task)

    # Tool calls must not exceed 10
    assert res.tool_call_count == 10
    assert agent.tool_call_count == 10
    assert res.llm_call_count == 6
    assert agent.llm_call_count == 6


@pytest.mark.asyncio
async def test_llm_budget_stops_tool_loop_to_reserve_synthesis(
    mock_toolset: RoleBoundToolset,
) -> None:
    """Verify tool loop halts when llm_call_count >= llm_call_budget - 1 to guarantee 1 call for synthesis."""
    responses = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id=f"c_{i}",
                    function_name="get_ticket",
                    arguments={"ticket_id": 1},
                )
            ],
            model_used="openai/gpt-5.4",
        )
        for i in range(10)
    ]
    ev = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="ticket_id:1",
        finding="Delay observed",
        support="ticket.description",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Delay reported",
        facts=["Fact 1"],
        interpretations=["Interp 1"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="delay",
    )
    synthesis_result = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        overall_facts=["Fact 1"],
        overall_interpretations=["Interp 1"],
        tool_call_count=4,
        llm_call_count=5,
        investigation_complete=True,
    )

    llm = ScriptedMockLLM(
        tool_responses=responses,
        structured_responses=[synthesis_result],
    )
    agent = ResearchAgent(
        toolset=mock_toolset,
        llm_client=llm,
        model_name="openai/gpt-5.4",
        tool_call_budget=10,
        llm_call_budget=5,  # 4 for tools, 1 for synthesis
    )

    task = ResearchTask(
        user_question="Why are customers reporting delays?",
        objective="Investigate delay complaints",
    )
    res = await agent.execute(task)

    assert agent.llm_call_count == 5
    assert res.llm_call_count == 5
    assert agent.tool_call_count == 4


@pytest.mark.asyncio
async def test_zero_llm_deterministic_fallback_on_budget_exhaustion(
    mock_toolset: RoleBoundToolset,
) -> None:
    """Verify deterministic fallback triggers with zero LLM calls if budget is already exhausted at synthesis time."""
    responses = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="c_1",
                    function_name="get_ticket",
                    arguments={"ticket_id": 1},
                )
            ],
            model_used="openai/gpt-5.4",
        ),
    ]

    llm = ScriptedMockLLM(tool_responses=responses)
    agent = ResearchAgent(
        toolset=mock_toolset,
        llm_client=llm,
        model_name="openai/gpt-5.4",
        tool_call_budget=10,
        llm_call_budget=0,  # Zero budget triggers fallback immediately
    )

    task = ResearchTask(
        user_question="Why are customers reporting delays?",
        objective="Investigate delay complaints",
    )
    res = await agent.execute(task)

    assert agent.llm_call_count == 0
    assert res.llm_call_count == 0
    assert res.investigation_complete is False
    assert any("budget" in lim.lower() for lim in res.limitations)
