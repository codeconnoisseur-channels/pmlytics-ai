"""Unit tests verifying EngineeringAgent behavior, Jira tools usage, and active vs historical classification."""

from datetime import UTC, datetime
from typing import Any, TypeVar
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.engineering import EngineeringAgent, EngineeringTask
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.jira import (
    JiraComment,
    JiraIssue,
    JiraIssueLink,
)
from app.domain.specialists import EngineeringFinding, SpecialistResult
from app.integrations.jira.adapter import JiraAdapter, JiraSearchResult
from app.integrations.llm.client import LLMMessage, LLMResponse, ToolCallRequest
from app.tools.registry import ToolRegistry
from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class ScriptedMockLLM:
    """Mock LLM for testing EngineeringAgent flows."""

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
async def test_engineering_agent_search_and_linked_issues_flow() -> None:
    """Verify EngineeringAgent searches issues, follows linked issues, and distinguishes active vs historical context."""
    issue_pay117 = JiraIssue(
        id=117,
        key="PAY-117",
        summary="Intermittent webhook timeout on core banking gateway",
        description="Bank switch callback webhook times out after 30 seconds under heavy load.",
        issue_type="Bug",
        status="In Progress",
        priority="High",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        components=["Payments", "Webhooks"],
    )

    mock_search = JiraSearchResult(
        total=1,
        issues=[issue_pay117],
    )
    mock_links = [
        JiraIssueLink(
            id="link_001",
            inward_key="PAY-117",
            outward_key="PAY-104",
            relationship="relates to",
        )
    ]
    mock_comments = [
        JiraComment(
            id="c_101",
            issue_key="PAY-117",
            author="lead_engineer",
            body="Confirmed that when switch takes >30s, worker drops connection and state remains pending.",
            created_at=datetime.now(UTC),
        )
    ]

    mock_jira = MagicMock(spec=JiraAdapter)
    mock_jira.search_issues = AsyncMock(return_value=mock_search)
    mock_jira.get_linked_issues = AsyncMock(return_value=mock_links)
    mock_jira.get_issue_comments = AsyncMock(return_value=mock_comments)

    reg = ToolRegistry.create_default(
        zendesk_adapter=MagicMock(),
        posthog_adapter=MagicMock(),
        jira_adapter=mock_jira,
    )
    toolset = reg.get_toolset_for_role("engineering")

    ev1 = Evidence(
        ledger_entry_id="engineering:led_001",
        source_type="jira",
        source_reference="PAY-117",
        finding="Active bug PAY-117 is In Progress regarding webhook timeouts",
        support="PAY-117 status: In Progress, priority: High",
        confidence=EvidenceConfidence.HIGH,
    )
    ev2 = Evidence(
        ledger_entry_id="engineering:led_002",
        source_type="jira",
        source_reference="PAY-117 (Linked issues)",
        finding="PAY-117 relates to historical story PAY-104 (Done)",
        support="Linked issue PAY-104 status: Done",
        confidence=EvidenceConfidence.HIGH,
    )
    ev3 = Evidence(
        ledger_entry_id="engineering:led_003",
        source_type="jira",
        source_reference="PAY-117 (Comments)",
        finding="Engineer note confirms connection drop after 30s leaves state pending",
        support="Comment c_101: 'worker drops connection and state remains pending'",
        confidence=EvidenceConfidence.HIGH,
    )

    finding = EngineeringFinding(
        finding="Unresolved defect PAY-117 directly accounts for transfers remaining pending",
        facts=[
            "PAY-117 is an active High-priority bug in 'In Progress' status",
            "Lead engineer comment confirms 30s timeout drops connection and leaves state pending",
        ],
        interpretations=[
            "The delayed pending state seen by users corresponds to this active webhook timeout defect"
        ],
        hypotheses=[
            "Fixing the timeout handling in PAY-117 will eliminate prolonged pending state"
        ],
        evidence=[ev1, ev2, ev3],
        confidence=EvidenceConfidence.HIGH,
        issue_status="In Progress",
        technical_context="Core banking callback exceeds 30s timeout, causing worker disconnection",
        relationship_to_problem="Direct technical mechanism explaining pending transfers",
        is_active_incident=True,
    )
    synthesis_result = SpecialistResult[EngineeringFinding](
        agent_role="engineering",
        findings=[finding],
        overall_facts=["PAY-117 active bug in progress", "PAY-104 historical story done"],
        overall_interpretations=["Active bug explains observed product delay"],
        overall_hypotheses=["Resolving PAY-117 will fix user delay complaints"],
        contradictions=[],
        unanswered_questions=[],
        limitations=["Did not inspect worker log files directly"],
        tool_call_count=3,
        llm_call_count=4,
        investigation_complete=True,
    )

    tool_responses = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="c1",
                    function_name="search_issues",
                    arguments={"jql": "text ~ 'webhook timeout' order by created DESC"},
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="c2",
                    function_name="get_linked_issues",
                    arguments={"issue_key": "PAY-117"},
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="c3",
                    function_name="get_issue_comments",
                    arguments={"issue_key": "PAY-117"},
                )
            ],
            model_used="openai/gpt-5.4",
        ),
        LLMResponse(content="Done querying Jira", tool_calls=[], model_used="openai/gpt-5.4"),
    ]

    llm = ScriptedMockLLM(
        tool_responses=tool_responses,
        structured_responses=[synthesis_result],
    )
    agent = EngineeringAgent(
        toolset=toolset,
        llm_client=llm,
        model_name="openai/gpt-5.4",
    )

    task = EngineeringTask(
        user_question="Are there active bugs causing transfer delays?",
        objective="Investigate technical causes of transfer delay",
    )
    res = await agent.execute(task)

    assert res.agent_role == "engineering"
    assert res.tool_call_count == 3
    assert res.llm_call_count == 5
    assert res.investigation_complete is True
    assert len(res.findings) == 1
    assert res.findings[0].is_active_incident is True
    assert res.findings[0].issue_status == "In Progress"
