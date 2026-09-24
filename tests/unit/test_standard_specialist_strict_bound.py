"""Unit tests verifying bounded specialist execution in Standard mode.

Tests prove:
1. Sufficient evidence path terminates after 2 specialist calls
2. Empty/partial tool result path cannot exceed 2 calls
3. Malformed intermediate content cannot trigger a third Standard specialist call
4. Tool execution remains bounded by existing role-specific limits
5. The production Standard budget permits one schema-repair call only when needed
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.research import ResearchAgent, ResearchTask
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.specialists import CustomerFinding, SpecialistResult
from app.domain.zendesk import ZendeskTicket
from app.integrations.llm.client import LLMResponse, ToolCallRequest
from app.integrations.zendesk.adapter import ZendeskSearchResult
from app.tools.base import ToolProvenance, ToolResult


@pytest.fixture
def mock_tools():
    toolset = MagicMock()
    toolset.role = "research"
    tool = MagicMock()
    tool.name = "search_tickets"
    tool.description = "Search customer support tickets"
    toolset.tools = [tool]
    return toolset


@pytest.mark.asyncio
async def test_sufficient_evidence_path_terminates_after_two_calls(mock_tools: MagicMock) -> None:
    """Test 1: Sufficient evidence path executes Turn 1 retrieval -> Turn 2 synthesis = 2 calls."""
    mock_llm = AsyncMock()

    # Call 1: Emits tool call
    mock_llm.complete.return_value = LLMResponse(
        model_used="openai/gpt-4.1-mini",
        content=None,
        tool_calls=[
            ToolCallRequest(id="c1", function_name="search_tickets", arguments={"query": "test"})
        ],
    )

    # Tool invocation result
    now = datetime.now(UTC)
    mock_ticket = ZendeskTicket(
        id=1,
        requester_id="usr_abc123",
        subject="Test ticket",
        description="Test description",
        status="open",
        priority="normal",
        channel="web",
        created_at=now,
        updated_at=now,
    )
    mock_tools.invoke_tool = AsyncMock(
        return_value=ToolResult(
            success=True,
            provenance=ToolProvenance(source_type="zendesk", source_reference="ticket:1"),
            data=ZendeskSearchResult(tickets=[mock_ticket], count=1),
            execution_duration_ms=5.0,
        )
    )

    # Call 2: Returns valid CustomerFinding in synthesis
    mock_finding = CustomerFinding(
        finding="Customer reported test issue",
        facts=["Customer reported test issue in ticket 1"],
        observed_pattern="Single test ticket",
        interpretations=["Test interpretation"],
        evidence=[
            Evidence(
                ledger_entry_id="research:r0:led_001",
                source_type="zendesk",
                source_reference="ticket:1",
                finding="Test ticket finding",
                support="Test description",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
    )

    agent = ResearchAgent(
        toolset=mock_tools,
        llm_client=mock_llm,
        tool_call_budget=10,
        llm_call_budget=2,  # Standard profile bound
    )

    mock_llm.complete_structured.return_value = SpecialistResult(
        agent_role="research",
        findings=[mock_finding],
        limitations=[],
        tool_call_count=1,
        llm_call_count=2,
        investigation_complete=True,
    )

    task = ResearchTask(
        user_question="Why test?",
        objective="Investigate test",
        specific_questions=["What is the test?"],
    )

    res = await agent.execute(task, round_index=0)
    assert agent.llm_call_count == 2
    assert len(res.findings) == 1
    assert mock_llm.complete.call_count == 1
    assert mock_llm.complete_structured.call_count == 1


@pytest.mark.asyncio
async def test_empty_or_partial_tool_result_path_cannot_exceed_two_calls(
    mock_tools: MagicMock,
) -> None:
    """Test 2: When tool returns empty/partial results, specialist still terminates after 2 calls."""
    mock_llm = AsyncMock()

    # Call 1: Emits tool call
    mock_llm.complete.return_value = LLMResponse(
        model_used="openai/gpt-4.1-mini",
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="c1", function_name="search_tickets", arguments={"query": "nonexistent"}
            )
        ],
    )

    # Tool returns empty
    mock_tools.invoke_tool = AsyncMock(
        return_value=ToolResult(
            success=True,
            provenance=ToolProvenance(source_type="zendesk", source_reference="search:empty"),
            data=ZendeskSearchResult(tickets=[], count=0),
            execution_duration_ms=5.0,
        )
    )

    agent = ResearchAgent(
        toolset=mock_tools,
        llm_client=mock_llm,
        tool_call_budget=10,
        llm_call_budget=2,
    )

    mock_llm.complete_structured.return_value = SpecialistResult(
        agent_role="research",
        findings=[],
        limitations=["No tickets found"],
        tool_call_count=1,
        llm_call_count=2,
        investigation_complete=False,
    )

    task = ResearchTask(
        user_question="Why empty?",
        objective="Investigate empty",
        specific_questions=["What?"],
    )

    await agent.execute(task, round_index=0)
    assert agent.llm_call_count == 2
    assert mock_llm.complete.call_count == 1
    assert mock_llm.complete_structured.call_count == 1


@pytest.mark.asyncio
async def test_malformed_intermediate_content_cannot_trigger_third_call(
    mock_tools: MagicMock,
) -> None:
    """Test 3: Malformed intermediate content or failed synthesis cannot trigger a 3rd call in Standard mode."""
    mock_llm = AsyncMock()

    # Call 1: Emits tool call
    mock_llm.complete.return_value = LLMResponse(
        model_used="openai/gpt-4.1-mini",
        content="Malformed text and tool calls",
        tool_calls=[
            ToolCallRequest(id="c1", function_name="search_tickets", arguments={"query": "test"})
        ],
    )

    mock_tools.invoke_tool = AsyncMock(
        return_value=ToolResult(
            success=True,
            provenance=ToolProvenance(source_type="zendesk", source_reference="ticket:1"),
            data=ZendeskSearchResult(tickets=[], count=0),
            execution_duration_ms=5.0,
        )
    )

    # Synthesis raises an error / fails validation
    mock_llm.complete_structured.side_effect = RuntimeError("Malformed JSON output from model")

    agent = ResearchAgent(
        toolset=mock_tools,
        llm_client=mock_llm,
        tool_call_budget=10,
        llm_call_budget=2,
    )

    task = ResearchTask(
        user_question="Why fail?",
        objective="Investigate fail",
        specific_questions=["What?"],
    )

    res = await agent.execute(task, round_index=0)
    # Must fail safe without exceeding 2 calls!
    assert agent.llm_call_count == 2
    assert res.investigation_complete is False
    assert mock_llm.complete.call_count == 1
    assert mock_llm.complete_structured.call_count == 1


@pytest.mark.asyncio
async def test_tool_execution_remains_bounded_by_role_limits(mock_tools: MagicMock) -> None:
    """Test 4: Specialist tool execution halts when tool budget is exhausted during Turn 1."""
    mock_llm = AsyncMock()

    # Model requests 5 tool calls, but budget is only 2
    mock_llm.complete.return_value = LLMResponse(
        model_used="openai/gpt-4.1-mini",
        content=None,
        tool_calls=[
            ToolCallRequest(
                id=f"c{i}", function_name="search_tickets", arguments={"query": f"q{i}"}
            )
            for i in range(5)
        ],
    )

    mock_tools.invoke_tool = AsyncMock(
        return_value=ToolResult(
            success=True,
            provenance=ToolProvenance(source_type="zendesk", source_reference="test"),
            data=ZendeskSearchResult(tickets=[], count=0),
            execution_duration_ms=5.0,
        )
    )

    agent = ResearchAgent(
        toolset=mock_tools,
        llm_client=mock_llm,
        tool_call_budget=2,  # Bound to 2 tools
        llm_call_budget=2,
    )

    mock_llm.complete_structured.return_value = SpecialistResult(
        agent_role="research",
        findings=[],
        limitations=["Tool budget reached"],
        tool_call_count=2,
        llm_call_count=2,
        investigation_complete=True,
    )

    task = ResearchTask(
        user_question="Why bound?",
        objective="Investigate bound",
        specific_questions=["What?"],
    )

    await agent.execute(task, round_index=0)
    assert agent.tool_call_count == 2
    assert mock_tools.invoke_tool.call_count == 2
    assert agent.llm_call_count == 2


@pytest.mark.asyncio
async def test_standard_repair_budget_recovers_one_invalid_synthesis(
    mock_tools: MagicMock,
) -> None:
    """A paid run gets one bounded repair instead of exposing a fallback report."""
    mock_llm = AsyncMock()
    mock_llm.complete.return_value = LLMResponse(
        model_used="openai/gpt-4.1-mini",
        content=None,
        tool_calls=[
            ToolCallRequest(id="c1", function_name="search_tickets", arguments={"query": "test"})
        ],
    )
    now = datetime.now(UTC)
    ticket = ZendeskTicket(
        id=1,
        requester_id="usr_abc123",
        subject="Test ticket",
        description="Test description",
        status="open",
        priority="normal",
        channel="web",
        created_at=now,
        updated_at=now,
    )
    mock_tools.invoke_tool = AsyncMock(
        return_value=ToolResult(
            success=True,
            provenance=ToolProvenance(source_type="zendesk", source_reference="ticket:1"),
            data=ZendeskSearchResult(tickets=[ticket], count=1),
            execution_duration_ms=5.0,
        )
    )
    finding = CustomerFinding(
        finding="Customer reported a test issue",
        facts=["Customer reported a test issue in ticket 1"],
        observed_pattern="Single test ticket",
        interpretations=["The issue affected the tested journey"],
        evidence=[
            Evidence(
                ledger_entry_id="research:r0:led_001",
                source_type="zendesk",
                source_reference="ticket:1",
                finding="Test ticket finding",
                support="Test description",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
    )
    repaired = SpecialistResult(
        agent_role="research",
        findings=[finding],
        limitations=[],
        tool_call_count=1,
        llm_call_count=3,
        investigation_complete=True,
    )
    mock_llm.complete_structured.side_effect = [
        RuntimeError("Malformed JSON output from model"),
        repaired,
    ]
    agent = ResearchAgent(
        toolset=mock_tools,
        llm_client=mock_llm,
        tool_call_budget=10,
        llm_call_budget=3,
    )

    result = await agent.execute(
        ResearchTask(
            user_question="Why fail?",
            objective="Investigate failure",
            specific_questions=["What happened?"],
        ),
        round_index=0,
        llm_budget_override=3,
    )

    assert result.investigation_complete is True
    assert agent.llm_call_count == 3
    assert mock_llm.complete.call_count == 1
    assert mock_llm.complete_structured.call_count == 2
