"""Unit tests verifying role-based permission matrix and RoleBoundToolset enforcement."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.integrations.jira.adapter import JiraAdapter
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.tools.base import AgentRole, ToolPermissionError
from app.tools.registry import ToolRegistry
from pydantic import BaseModel

ALL_EIGHT_TOOLS = {
    "search_tickets",
    "get_ticket",
    "get_ticket_comments",
    "query_analytics",
    "search_issues",
    "get_issue",
    "get_issue_comments",
    "get_linked_issues",
}


class DummyInput(BaseModel):
    dummy_field: str = "test"


@pytest.fixture
def mock_registry() -> ToolRegistry:
    """Create a ToolRegistry with mocked adapters for all 8 tools."""
    mock_zendesk = MagicMock(spec=ZendeskAdapter)
    mock_posthog = MagicMock(spec=PostHogAdapter)
    mock_jira = MagicMock(spec=JiraAdapter)
    return ToolRegistry.create_default(
        zendesk_adapter=mock_zendesk,
        posthog_adapter=mock_posthog,
        jira_adapter=mock_jira,
    )


def test_registry_contains_all_eight_tools(mock_registry: ToolRegistry) -> None:
    """Assert all 8 approved domain tools are registered."""
    tools = mock_registry.get_all_tools()
    tool_names = {t.name for t in tools}
    assert tool_names == ALL_EIGHT_TOOLS
    assert len(tools) == 8


@pytest.mark.parametrize(
    ("role", "expected_allowed"),
    [
        (
            "research",
            {"search_tickets", "get_ticket", "get_ticket_comments"},
        ),
        (
            "analytics",
            {"query_analytics"},
        ),
        (
            "engineering",
            {"search_issues", "get_issue", "get_issue_comments", "get_linked_issues"},
        ),
        ("pm", set()),
        ("critic", set()),
    ],
)
def test_role_bound_toolset_allowed_and_forbidden_matrix(
    mock_registry: ToolRegistry,
    role: AgentRole,
    expected_allowed: set[str],
) -> None:
    """Verify that RoleBoundToolset strictly exposes only allowed tools and forbids all others."""
    toolset = mock_registry.get_toolset_for_role(role)
    assert toolset.role == role

    # 1. Verify authorized tools
    active_tool_names = {t.name for t in toolset.tools}
    assert active_tool_names == expected_allowed

    for tool_name in expected_allowed:
        tool = toolset.get_tool(tool_name)
        assert tool.name == tool_name

    # 2. Verify forbidden tools
    forbidden_tools = ALL_EIGHT_TOOLS - expected_allowed
    for forbidden in forbidden_tools:
        with pytest.raises(ToolPermissionError) as exc_info:
            toolset.get_tool(forbidden)
        assert f"Role '{role}' is not authorized to access tool '{forbidden}'" in str(
            exc_info.value
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "forbidden_tool"),
    [
        ("research", "query_analytics"),
        ("research", "search_issues"),
        ("analytics", "search_tickets"),
        ("analytics", "get_issue"),
        ("engineering", "search_tickets"),
        ("engineering", "query_analytics"),
        ("pm", "search_tickets"),
        ("pm", "query_analytics"),
        ("pm", "search_issues"),
        ("critic", "search_tickets"),
        ("critic", "query_analytics"),
        ("critic", "search_issues"),
    ],
)
async def test_invoke_tool_forbidden_blocked_with_no_provenance(
    mock_registry: ToolRegistry,
    role: AgentRole,
    forbidden_tool: str,
) -> None:
    """Verify invoke_tool blocks forbidden tool execution with permission_denied, attempted_source=None, provenance=None."""
    toolset = mock_registry.get_toolset_for_role(role)

    result = await toolset.invoke_tool(forbidden_tool, DummyInput())

    assert result.success is False
    assert result.data is None
    assert result.provenance is None
    assert result.error is not None
    assert result.error.error_type == "permission_denied"
    assert result.error.attempted_source is None
    assert result.error.details.get("role") == role
    assert result.error.details.get("requested_tool") == forbidden_tool


@pytest.mark.asyncio
async def test_invoke_tool_authorized_success(mock_registry: ToolRegistry) -> None:
    """Verify authorized tool invocation proceeds through the tool instance."""
    toolset = mock_registry.get_toolset_for_role("research")
    tool = toolset.get_tool("get_ticket")

    # Mock _execute on the tool
    mock_ticket = MagicMock()
    mock_ticket.ticket_id = 42
    tool._execute = AsyncMock(return_value=(mock_ticket, "ticket_id:42"))  # type: ignore[method-assign]

    from app.tools.support import GetTicketInput

    result = await toolset.invoke_tool("get_ticket", GetTicketInput(ticket_id=42))

    assert result.success is True
    assert result.error is None
    assert result.provenance is not None
    assert result.provenance.source_type == "zendesk"
    assert result.provenance.source_reference == "ticket_id:42"
