"""Live integration tests for domain tools against Mock Zendesk, MockServer Jira, and PostHog."""

import ast
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from app.config.settings import Settings
from app.integrations.jira.adapter import JiraAdapter
from app.integrations.jira.client import JiraClient
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.client import PostHogClient
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.integrations.zendesk.client import ZendeskClient
from app.tools.analytics import (
    AnalyticsPropertyFilter,
    AnalyticsQueryIntent,
    QueryAnalyticsInput,
    QueryAnalyticsTool,
)
from app.tools.engineering import (
    GetIssueCommentsInput,
    GetIssueInput,
    GetLinkedIssuesInput,
    SearchIssuesInput,
)
from app.tools.registry import ToolRegistry
from app.tools.support import (
    GetTicketCommentsInput,
    GetTicketInput,
    SearchTicketsInput,
)

# -----------------------------------------------------------------------------
# 1. Live Support Tools Integration (Mock Zendesk)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_live_support_tools(mock_zendesk_server: str) -> None:
    """Test Support domain tools against live running Mock Zendesk server."""
    from seed.zendesk.minimal_loader import load_minimal_tickets

    client = ZendeskClient(
        base_url=mock_zendesk_server,
        username="mock@pocket.test",
        api_key="mock-zendesk-token-pocket",
        timeout_seconds=5.0,
    )
    await load_minimal_tickets(client)

    adapter = ZendeskAdapter(client)
    mock_posthog = MagicMock(spec=PostHogAdapter)
    mock_jira = MagicMock(spec=JiraAdapter)
    toolset = ToolRegistry.create_default(adapter, mock_posthog, mock_jira).get_toolset_for_role(
        "research"
    )

    # 1. search_tickets
    search_res = await toolset.invoke_tool(
        "search_tickets",
        SearchTicketsInput(query="transfer", page=1, limit=5),
    )
    assert search_res.success is True
    assert search_res.provenance is not None
    assert search_res.provenance.source_type == "zendesk"
    assert search_res.data is not None
    assert search_res.data.total_count >= 1

    first_ticket_id = search_res.data.tickets[0].id

    # 2. get_ticket
    get_res = await toolset.invoke_tool(
        "get_ticket",
        GetTicketInput(ticket_id=first_ticket_id),
    )
    assert get_res.success is True
    assert get_res.data is not None
    assert get_res.data.ticket.id == first_ticket_id
    assert get_res.provenance is not None
    assert get_res.provenance.source_reference == f"ticket_id:{first_ticket_id}"

    # 3. get_ticket_comments
    comm_res = await toolset.invoke_tool(
        "get_ticket_comments",
        GetTicketCommentsInput(ticket_id=first_ticket_id),
    )
    assert comm_res.success is True
    assert comm_res.data is not None
    assert comm_res.data.ticket_id == first_ticket_id
    assert len(comm_res.data.comments) >= 1


# -----------------------------------------------------------------------------
# 2. Live Engineering Tools Integration (MockServer Jira)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_live_engineering_tools(mock_jira_server: str) -> None:
    """Test Engineering domain tools against live running MockServer Jira."""
    client = JiraClient(
        base_url=mock_jira_server,
        username="mock-jira@pocket.test",
        api_token="mock-jira-token-pocket",
        timeout_seconds=5.0,
    )
    adapter = JiraAdapter(client)

    mock_zendesk = MagicMock(spec=ZendeskAdapter)
    mock_posthog = MagicMock(spec=PostHogAdapter)
    toolset = ToolRegistry.create_default(mock_zendesk, mock_posthog, adapter).get_toolset_for_role(
        "engineering"
    )

    # 1. get_issue: PAY-117
    issue_res = await toolset.invoke_tool(
        "get_issue",
        GetIssueInput(issue_key="PAY-117"),
    )
    assert issue_res.success is True
    assert issue_res.data is not None
    assert issue_res.data.issue.key == "PAY-117"
    assert issue_res.provenance is not None
    assert issue_res.provenance.source_type == "jira"
    assert issue_res.provenance.source_reference == "issue_key:PAY-117"

    # 2. get_issue_comments: PAY-117
    comm_res = await toolset.invoke_tool(
        "get_issue_comments",
        GetIssueCommentsInput(issue_key="PAY-117"),
    )
    assert comm_res.success is True
    assert comm_res.data is not None
    assert len(comm_res.data.comments) >= 2

    # 3. get_linked_issues: PAY-117
    link_res = await toolset.invoke_tool(
        "get_linked_issues",
        GetLinkedIssuesInput(issue_key="PAY-117"),
    )
    assert link_res.success is True
    assert link_res.data is not None
    assert len(link_res.data.linked_issues) >= 1

    # 4. search_issues
    search_res = await toolset.invoke_tool(
        "search_issues",
        SearchIssuesInput(jql='project = PAY AND status = "In Progress"', max_results=10),
    )
    assert search_res.success is True
    assert search_res.data is not None
    assert search_res.data.total_returned >= 1


# -----------------------------------------------------------------------------
# 3. Live Analytics Tool Integration (Live PostHog Cloud)
# -----------------------------------------------------------------------------

settings = Settings()
LIVE_API_KEY = os.getenv("POSTHOG_API_KEY") or settings.posthog_api_key
LIVE_PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID") or settings.posthog_project_id
LIVE_HOST = os.getenv("POSTHOG_HOST") or settings.posthog_host

skip_if_no_posthog = pytest.mark.skipif(
    not LIVE_API_KEY or not LIVE_PROJECT_ID,
    reason="Live PostHog credentials not configured in environment or .env",
)


@skip_if_no_posthog
@pytest.mark.asyncio
async def test_live_analytics_tool_scenario_c() -> None:
    """Verify live QueryAnalyticsTool against live PostHog Cloud for Scenario C (amount_ngn >= 50000)."""
    client = PostHogClient(
        host=LIVE_HOST,
        project_id=LIVE_PROJECT_ID,
        api_key=LIVE_API_KEY,
        timeout_seconds=35.0,
    )
    adapter = PostHogAdapter(client)
    tool = QueryAnalyticsTool(adapter)

    inp = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.EVENT_COUNT,
        description="High-value wallet funding started events",
        events=["wallet_funding_started"],
        filters=[
            AnalyticsPropertyFilter(
                property_name="amount_ngn",
                operator="gte",
                value=50000,
            )
        ],
    )

    res = await tool.run(inp)

    assert res.success is True
    assert res.error is None
    assert res.provenance is not None
    assert res.provenance.source_type == "posthog"
    assert res.data is not None
    assert res.data.result.raw_count >= 1


@skip_if_no_posthog
@pytest.mark.asyncio
async def test_live_analytics_tool_lifecycle_duration() -> None:
    """Verify live QueryAnalyticsTool with explicit start_event and end_event pair against PostHog Cloud."""
    client = PostHogClient(
        host=LIVE_HOST,
        project_id=LIVE_PROJECT_ID,
        api_key=LIVE_API_KEY,
        timeout_seconds=35.0,
    )
    adapter = PostHogAdapter(client)
    tool = QueryAnalyticsTool(adapter)

    inp = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.LIFECYCLE_DURATION,
        description="Transfer latency from submission to completion by bank",
        start_event="transfer_submitted",
        end_event="transfer_completed",
        breakdown_by="destination_bank",
        start_time="2026-08-10T00:00:00Z",
        end_time="2026-08-15T23:59:59Z",
    )

    res = await tool.run(inp)

    assert res.success is True
    assert res.error is None
    assert res.provenance is not None
    assert res.provenance.source_type == "posthog"
    assert (
        res.provenance.source_reference
        == "query:lifecycle_duration:transfer_submitted->transfer_completed"
    )
    assert res.data is not None
    assert len(res.data.result.rows) >= 1


# -----------------------------------------------------------------------------
# 4. Strict Boundary Isolation AST Test
# -----------------------------------------------------------------------------


def test_tools_boundary_isolation() -> None:
    """Verify app/tools/ does not import from seed/ or evaluations/."""
    tools_dir = Path("app/tools")
    assert tools_dir.exists() and tools_dir.is_dir()

    forbidden_prefixes = ("seed", "evaluations")

    for py_file in tools_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in forbidden_prefixes:
                        assert not alias.name.startswith(forbidden), (
                            f"Violation in {py_file}: imports {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                for forbidden in forbidden_prefixes:
                    assert not node.module.startswith(forbidden), (
                        f"Violation in {py_file}: imports from {node.module}"
                    )
