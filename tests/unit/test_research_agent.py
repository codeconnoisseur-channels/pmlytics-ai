"""Unit tests verifying ResearchAgent behavior, progressive discovery, and comment semantics."""

from datetime import UTC, datetime
from typing import Any, TypeVar
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.research import ResearchAgent, ResearchTask
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.specialists import CustomerFinding, SpecialistResult
from app.domain.zendesk import ZendeskComment, ZendeskTicket
from app.integrations.llm.client import LLMMessage, LLMResponse, ToolCallRequest
from app.integrations.zendesk.adapter import ZendeskAdapter, ZendeskSearchResult
from app.tools.registry import ToolRegistry
from app.tools.support import SearchTicketsOutput
from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class ScriptedMockLLM:
    """Mock LLM for testing ResearchAgent flows."""

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
async def test_research_agent_progressive_discovery() -> None:
    """Verify progressive discovery: search_tickets -> get_ticket_comments -> grounded synthesis."""
    mock_ticket = ZendeskTicket(
        id=101,
        subject="Transfer pending for days",
        description="I transferred 100,000 NGN and it still shows pending",
        status="open",
        priority="high",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000501",
        tags=["delay", "high_value"],
    )
    mock_comments = [
        ZendeskComment(
            id=1,
            ticket_id=101,
            author_id="usr_000501",
            author_role="customer",
            body="I am still waiting for the money to arrive",
            public=True,
            created_at=datetime.now(UTC),
        ),
        ZendeskComment(
            id=2,
            ticket_id=101,
            author_id="usr_000999",
            author_role="agent",
            body="Internal note: Core banking transfer ID 98765 is marked as timed_out on switch",
            public=False,
            created_at=datetime.now(UTC),
        ),
    ]

    mock_zendesk = MagicMock(spec=ZendeskAdapter)
    mock_zendesk.search_tickets = AsyncMock(
        return_value=ZendeskSearchResult(tickets=[mock_ticket], count=1)
    )
    mock_zendesk.get_ticket_comments = AsyncMock(return_value=mock_comments)

    reg = ToolRegistry.create_default(
        zendesk_adapter=mock_zendesk,
        posthog_adapter=MagicMock(),
        jira_adapter=MagicMock(),
    )
    toolset = reg.get_toolset_for_role("research")

    ev1 = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="query:type:ticket status<solved transfer pending:page:1",
        finding="Search returned ticket 101 with pending transfer issue",
        support="ticket_id 101 in search results",
        confidence=EvidenceConfidence.HIGH,
    )
    ev2 = Evidence(
        ledger_entry_id="research:led_002",
        source_type="zendesk",
        source_reference="ticket_comments:101",
        finding="Customer public comment confirms ongoing delay; agent internal note confirms timeout on switch",
        support="Comment 1 public: 'I am still waiting'; Comment 2 private: 'timed_out on switch'",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Customers report prolonged pending status backed by backend switch timeouts",
        facts=[
            "Ticket 101 requester states transfer is pending",
            "Staff internal note states core banking transfer timed out on switch",
        ],
        interpretations=[
            "Customer uncertainty is grounded in an actual backend switch communication failure"
        ],
        hypotheses=["Switch timeouts lead to stalled transfers that leave the customer in limbo"],
        evidence=[ev1, ev2],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="pending_transfer_complaint",
        affected_users="High value transfer users",
        frequency_context="Observed in ticket 101",
    )
    synthesis_result = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        overall_facts=["Ticket 101 observed with customer complaint and internal diagnostic note"],
        overall_interpretations=["Delayed transfers stem from switch issues"],
        contradictions=[],
        unanswered_questions=[],
        limitations=["Only 1 ticket examined in this sample"],
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
                    function_name="search_tickets",
                    arguments={"query": "type:ticket status<solved transfer pending"},
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="c2",
                    function_name="get_ticket_comments",
                    arguments={"ticket_id": 101},
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(content="Done searching", tool_calls=[], model_used="openai/gpt-5.4"),
    ]

    llm = ScriptedMockLLM(
        tool_responses=tool_responses,
        structured_responses=[synthesis_result],
    )
    agent = ResearchAgent(
        toolset=toolset,
        llm_client=llm,
        model_name="openai/gpt-5.4",
    )

    task = ResearchTask(
        user_question="Why are customers reporting pending transfers?",
        objective="Investigate why users report delayed transfers",
    )
    res = await agent.execute(task)

    assert res.agent_role == "research"
    assert res.tool_call_count == 2
    assert res.llm_call_count == 4
    assert res.investigation_complete is True
    assert len(res.findings) == 1
    assert len(res.findings[0].evidence) == 2
    assert res.findings[0].evidence[0].ledger_entry_id == "research:led_001"
    assert res.findings[0].evidence[1].ledger_entry_id == "research:led_002"


@pytest.mark.asyncio
async def test_research_agent_zero_search_results_recorded_as_observed_fact() -> None:
    """Verify that zero tickets found is recorded in the ledger and can be cited as evidence of absence."""
    mock_zendesk = MagicMock(spec=ZendeskAdapter)
    mock_zendesk.search_tickets = AsyncMock(return_value=ZendeskSearchResult(tickets=[], count=0))

    reg = ToolRegistry.create_default(
        zendesk_adapter=mock_zendesk,
        posthog_adapter=MagicMock(),
        jira_adapter=MagicMock(),
    )
    toolset = reg.get_toolset_for_role("research")

    ev = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="query:type:ticket crypto withdrawal:page:1",
        finding="Zero customer tickets mention crypto withdrawal",
        support="search count: 0",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="No support ticket volume regarding crypto withdrawal",
        facts=["Search for 'type:ticket crypto withdrawal' returned 0 tickets"],
        interpretations=["Customers are not filing tickets about crypto withdrawal"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="zero_volume",
    )
    synthesis_result = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        overall_facts=["0 tickets returned"],
        overall_interpretations=["No reported issues"],
        tool_call_count=1,
        llm_call_count=2,
        investigation_complete=True,
    )

    tool_responses = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="c1",
                    function_name="search_tickets",
                    arguments={"query": "type:ticket crypto withdrawal"},
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(content="Done searching", tool_calls=[], model_used="openai/gpt-5.4"),
    ]

    llm = ScriptedMockLLM(
        tool_responses=tool_responses,
        structured_responses=[synthesis_result],
    )
    agent = ResearchAgent(
        toolset=toolset,
        llm_client=llm,
        model_name="openai/gpt-5.4",
    )

    task = ResearchTask(
        user_question="Are there customer complaints about crypto withdrawals?",
        objective="Check if customers complain about crypto withdrawals",
    )
    res = await agent.execute(task)

    assert res.investigation_complete is True
    assert len(agent.ledger.entries) == 1
    assert isinstance(agent.ledger.entries[0].typed_payload, SearchTicketsOutput)
    assert agent.ledger.entries[0].typed_payload.total_count == 0
