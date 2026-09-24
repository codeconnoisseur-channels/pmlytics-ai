"""Unit tests for Engineering domain tools (Jira)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.domain.jira import (
    JiraComment,
    JiraIssue,
    JiraIssueLink,
)
from app.integrations.jira.adapter import JiraAdapter, JiraSearchResult
from app.integrations.jira.exceptions import JiraAuthError, JiraNotFoundError, JiraTimeoutError
from app.tools.engineering import (
    GetIssueCommentsInput,
    GetIssueCommentsTool,
    GetIssueInput,
    GetIssueTool,
    GetLinkedIssuesInput,
    GetLinkedIssuesTool,
    SearchIssuesInput,
    SearchIssuesTool,
)
from pydantic import ValidationError


@pytest.fixture
def mock_jira_adapter() -> MagicMock:
    return MagicMock(spec=JiraAdapter)


@pytest.fixture
def sample_issue() -> JiraIssue:
    return JiraIssue(
        id=10001,
        key="PAY-117",
        summary="Delayed transfer callbacks from partner banks",
        description="Bank callbacks taking hours",
        issue_type="Bug",
        status="In Progress",
        priority="High",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        components=["Payments", "Webhooks"],
    )


@pytest.fixture
def sample_comment() -> JiraComment:
    return JiraComment(
        id="20001",
        issue_key="PAY-117",
        author="eng_alice",
        body="Partner confirmed queue backlog on their gateway",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_link() -> JiraIssueLink:
    return JiraIssueLink(
        id="30001",
        inward_key="PAY-117",
        outward_key="CORE-82",
        relationship="relates to",
    )


# -----------------------------------------------------------------------------
# 1. Regex & Input Validation Tests
# -----------------------------------------------------------------------------


def test_jira_issue_key_regex_validation() -> None:
    """Verify issue_key enforces ^[A-Z]+-\\d+$ regex pattern."""
    # Valid
    assert GetIssueInput(issue_key="PAY-117").issue_key == "PAY-117"
    assert GetIssueInput(issue_key="CORE-82").issue_key == "CORE-82"
    assert GetIssueInput(issue_key="BILL-1").issue_key == "BILL-1"

    # Invalid lowercase
    with pytest.raises(ValidationError):
        GetIssueInput(issue_key="pay-117")

    # Invalid underscore
    with pytest.raises(ValidationError):
        GetIssueInput(issue_key="PAY_117")

    # Invalid no numbers
    with pytest.raises(ValidationError):
        GetIssueInput(issue_key="PAY-")

    # Invalid arbitrary text
    with pytest.raises(ValidationError):
        GetIssueInput(issue_key="some_random_query")


# -----------------------------------------------------------------------------
# 2. Tool Execution & Provenance Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_issues_tool_success(
    mock_jira_adapter: MagicMock,
    sample_issue: JiraIssue,
) -> None:
    """Verify search_issues returns matching Jira issues and records provenance."""
    tool = SearchIssuesTool(mock_jira_adapter)
    mock_jira_adapter.search_issues = AsyncMock(
        return_value=JiraSearchResult(issues=[sample_issue], total=1, next_page_token="token_abc")
    )

    inp = SearchIssuesInput(jql="project = PAY", max_results=25)
    res = await tool.run(inp)

    assert res.success is True
    assert res.error is None
    assert res.provenance is not None
    assert res.provenance.source_type == "jira"
    assert res.provenance.source_reference == "PAY-117"
    assert res.data is not None
    assert res.data.total_returned == 1
    assert res.data.next_page_token == "token_abc"
    assert res.data.issues[0].key == "PAY-117"


@pytest.mark.asyncio
async def test_get_issue_tool_success(
    mock_jira_adapter: MagicMock,
    sample_issue: JiraIssue,
) -> None:
    """Verify get_issue retrieves single issue and records provenance."""
    tool = GetIssueTool(mock_jira_adapter)
    mock_jira_adapter.get_issue = AsyncMock(return_value=sample_issue)

    inp = GetIssueInput(issue_key="PAY-117")
    res = await tool.run(inp)

    assert res.success is True
    assert res.data is not None
    assert res.data.issue.key == "PAY-117"
    assert res.provenance is not None
    assert res.provenance.source_type == "jira"
    assert res.provenance.source_reference == "PAY-117"


@pytest.mark.asyncio
async def test_get_issue_comments_tool_success(
    mock_jira_adapter: MagicMock,
    sample_comment: JiraComment,
) -> None:
    """Verify get_issue_comments retrieves comments on Jira issue."""
    tool = GetIssueCommentsTool(mock_jira_adapter)
    mock_jira_adapter.get_issue_comments = AsyncMock(return_value=[sample_comment])

    inp = GetIssueCommentsInput(issue_key="PAY-117")
    res = await tool.run(inp)

    assert res.success is True
    assert res.data is not None
    assert res.data.issue_key == "PAY-117"
    assert len(res.data.comments) == 1
    assert res.provenance is not None
    assert res.provenance.source_reference == "PAY-117 (Comments)"


@pytest.mark.asyncio
async def test_get_linked_issues_tool_success(
    mock_jira_adapter: MagicMock,
    sample_link: JiraIssueLink,
) -> None:
    """Verify get_linked_issues retrieves linked issues on Jira issue."""
    tool = GetLinkedIssuesTool(mock_jira_adapter)
    mock_jira_adapter.get_linked_issues = AsyncMock(return_value=[sample_link])

    inp = GetLinkedIssuesInput(issue_key="PAY-117")
    res = await tool.run(inp)

    assert res.success is True
    assert res.data is not None
    assert res.data.issue_key == "PAY-117"
    assert len(res.data.linked_issues) == 1
    assert res.provenance is not None
    assert res.provenance.source_reference == "PAY-117 (Linked issues)"


# -----------------------------------------------------------------------------
# 3. Error Handling Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_issue_not_found(mock_jira_adapter: MagicMock) -> None:
    """Verify JiraNotFoundError maps to not_found with attempted_source=jira and provenance=None."""
    tool = GetIssueTool(mock_jira_adapter)
    mock_jira_adapter.get_issue = AsyncMock(
        side_effect=JiraNotFoundError("Issue NONEXIST-99 not found")
    )

    inp = GetIssueInput(issue_key="NONEXIST-99")
    res = await tool.run(inp)

    assert res.success is False
    assert res.data is None
    assert res.provenance is None
    assert res.error is not None
    assert res.error.error_type == "not_found"
    assert res.error.attempted_source == "jira"


@pytest.mark.asyncio
async def test_jira_timeout_error(mock_jira_adapter: MagicMock) -> None:
    """Verify JiraTimeoutError maps to timeout with attempted_source=jira."""
    tool = SearchIssuesTool(mock_jira_adapter)
    mock_jira_adapter.search_issues = AsyncMock(side_effect=JiraTimeoutError("Jira timed out"))

    inp = SearchIssuesInput(jql="project = PAY")
    res = await tool.run(inp)

    assert res.success is False
    assert res.data is None
    assert res.provenance is None
    assert res.error is not None
    assert res.error.error_type == "timeout"
    assert res.error.attempted_source == "jira"


@pytest.mark.asyncio
async def test_jira_auth_error(mock_jira_adapter: MagicMock) -> None:
    """Verify JiraAuthError maps to authentication_error with attempted_source=jira."""
    tool = SearchIssuesTool(mock_jira_adapter)
    mock_jira_adapter.search_issues = AsyncMock(side_effect=JiraAuthError("401 Unauthorized"))

    inp = SearchIssuesInput(jql="project = PAY")
    res = await tool.run(inp)

    assert res.success is False
    assert res.data is None
    assert res.provenance is None
    assert res.error is not None
    assert res.error.error_type == "authentication_error"
    assert res.error.attempted_source == "jira"
