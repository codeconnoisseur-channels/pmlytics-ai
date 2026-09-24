"""Deterministic end-to-end integration test exercising Phase 6 agent with Phase 5 domain tools and mock backend."""

from typing import Any, TypeVar

import pytest
from app.agents.research import ResearchAgent, ResearchTask
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.specialists import CustomerFinding, SpecialistResult
from app.integrations.llm.client import LLMMessage, LLMResponse, ToolCallRequest
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.integrations.zendesk.client import ZendeskClient
from app.tools.registry import ToolRegistry
from pydantic import BaseModel
from seed.zendesk.minimal_loader import load_minimal_tickets

TModel = TypeVar("TModel", bound=BaseModel)


class ScriptedE2EMockLLM:
    """Deterministic scripted mock LLM for testing end-to-end agent-to-tool integration."""

    def __init__(
        self,
        tool_responses: list[LLMResponse],
        structured_responses: list[Any],
    ) -> None:
        self.tool_responses = list(tool_responses)
        self.structured_responses = list(structured_responses)
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
        return LLMResponse(content="Done querying", tool_calls=[], model_used=model)

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
async def test_specialist_e2e_research_agent_flow(mock_zendesk_server: str) -> None:
    """Verify full chain: LLM -> RoleBoundToolset -> SearchTicketsTool -> ZendeskAdapter -> Mock Zendesk -> EvidenceLedger -> Synthesis."""
    # 1. Seed minimal tickets in live Zendesk mock server
    client = ZendeskClient(
        base_url=mock_zendesk_server,
        username="mock@pocket.test",
        api_key="mock-zendesk-token-pocket",
        timeout_seconds=5.0,
    )
    await load_minimal_tickets(client)

    # 2. Build actual Phase 5 Adapter and Registry
    zendesk_adapter = ZendeskAdapter(client=client)
    from unittest.mock import MagicMock

    registry = ToolRegistry.create_default(
        zendesk_adapter=zendesk_adapter,
        posthog_adapter=MagicMock(),
        jira_adapter=MagicMock(),
    )
    toolset = registry.get_toolset_for_role("research")

    # 3. Setup scripted LLM
    expected_ref = "query:transfer:page:1"
    ev = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference=expected_ref,
        finding="Customer tickets describe delayed bank transfers",
        support="Tickets returned with delay keywords from Zendesk mock",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Delay complaints verified in Zendesk support tickets",
        facts=["Search query 'transfer' returned matching customer tickets"],
        interpretations=["Customers experience uncertainty during delayed transfers"],
        hypotheses=["Webhook callback timeouts may be contributing"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="transfer_delay_tickets",
    )
    synthesis = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        overall_facts=["Delay tickets identified in Zendesk mock"],
        overall_interpretations=["Customer uncertainty around pending transfers"],
        overall_hypotheses=["Delayed callbacks contribute to confusion"],
        contradictions=[],
        unanswered_questions=[],
        limitations=[],
        tool_call_count=1,
        llm_call_count=2,
        investigation_complete=True,
    )

    tool_responses = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_search_1",
                    function_name="search_tickets",
                    arguments={"query": "transfer", "page": 1},
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(content="Done searching", tool_calls=[], model_used="openai/gpt-5.4"),
    ]

    mock_llm = ScriptedE2EMockLLM(
        tool_responses=tool_responses,
        structured_responses=[synthesis],
    )

    agent = ResearchAgent(
        toolset=toolset,
        llm_client=mock_llm,
        model_name="openai/gpt-5.4",
        tool_call_budget=10,
        llm_call_budget=15,
    )

    task = ResearchTask(
        user_question="Are customers complaining about transfer delays?",
        objective="Search Zendesk for transfer delay complaints",
        specific_questions=["What is the volume and nature of delay tickets?"],
    )

    # 4. Execute specialist end-to-end
    result = await agent.execute(task)

    # 5. Assert end-to-end invariants
    assert result.agent_role == "research"
    assert result.investigation_complete is True
    assert result.tool_call_count == 1
    assert result.llm_call_count == 3  # 1 tool call + 1 exit + 1 synthesis

    # Verify ledger recorded real data from mock API with correct provenance
    assert len(agent.ledger.entries) == 1
    ledger_entry = agent.ledger.entries[0]
    assert ledger_entry.ledger_entry_id == "research:led_001"
    assert ledger_entry.source_type == "zendesk"
    assert ledger_entry.source_reference == expected_ref
    assert "Customer-support search returned" in ledger_entry.data_summary
    assert ledger_entry.typed_payload.total_count > 0

    # Verify provenance survived from tool execution to final SpecialistResult
    assert len(result.findings) == 1
    res_ev = result.findings[0].evidence[0]
    assert res_ev.ledger_entry_id == "research:led_001"
    assert res_ev.source_type == "zendesk"
    assert res_ev.source_reference == expected_ref
