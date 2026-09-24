"""Engineering domain tools wrapping JiraAdapter for the Engineering Agent."""

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.domain.jira import JiraComment, JiraIssue, JiraIssueLink
from app.integrations.jira.adapter import JiraAdapter
from app.integrations.jira.exceptions import (
    JiraAuthError,
    JiraError,
    JiraNotFoundError,
    JiraTimeoutError,
)
from app.tools.base import BaseTool, ToolError

# -----------------------------------------------------------------------------
# Input & Output Contracts
# -----------------------------------------------------------------------------


class SearchIssuesInput(BaseModel):
    """Input parameters for searching Jira issues using JQL."""

    jql: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="JQL search query string (e.g. 'project = PAY AND status = \"In Progress\"')",
    )
    max_results: int = Field(
        default=50, ge=1, le=100, description="Maximum number of issues to return"
    )
    next_page_token: str | None = Field(
        default=None, description="Cursor token for fetching subsequent pages"
    )


class SearchIssuesOutput(BaseModel):
    """Output envelope containing matching Jira issues."""

    issues: list[JiraIssue]
    next_page_token: str | None
    total_returned: int


class GetIssueInput(BaseModel):
    """Input parameters for retrieving a specific Jira issue."""

    issue_key: str = Field(
        ...,
        pattern=r"^[A-Z]+-\d+$",
        description="Standard Jira issue key (e.g. 'PAY-117', 'CORE-82')",
    )


class GetIssueOutput(BaseModel):
    """Output envelope containing the requested Jira issue."""

    issue: JiraIssue


class GetIssueCommentsInput(BaseModel):
    """Input parameters for retrieving comments on a Jira issue."""

    issue_key: str = Field(
        ...,
        pattern=r"^[A-Z]+-\d+$",
        description="Standard Jira issue key (e.g. 'PAY-117', 'CORE-82')",
    )


class GetIssueCommentsOutput(BaseModel):
    """Output envelope containing comments on a Jira issue."""

    issue_key: str
    comments: list[JiraComment]


class GetLinkedIssuesInput(BaseModel):
    """Input parameters for retrieving linked issues for a Jira issue."""

    issue_key: str = Field(
        ...,
        pattern=r"^[A-Z]+-\d+$",
        description="Standard Jira issue key (e.g. 'PAY-117', 'CORE-82')",
    )


class GetLinkedIssuesOutput(BaseModel):
    """Output envelope containing linked issues for a Jira issue."""

    issue_key: str
    linked_issues: list[JiraIssueLink]


# -----------------------------------------------------------------------------
# Domain Tools
# -----------------------------------------------------------------------------


def _map_jira_error(exc: Exception) -> ToolError:
    """Normalize Jira integration exceptions into structured ToolError."""
    if isinstance(exc, JiraNotFoundError):
        return ToolError(
            error_type="not_found",
            message=str(exc),
            attempted_source="jira",
        )
    if isinstance(exc, JiraTimeoutError):
        return ToolError(
            error_type="timeout",
            message=str(exc),
            attempted_source="jira",
        )
    if isinstance(exc, JiraAuthError):
        return ToolError(
            error_type="authentication_error",
            message=str(exc),
            attempted_source="jira",
        )
    if isinstance(exc, ValidationError):
        return ToolError(
            error_type="invalid_input",
            message=f"Validation error: {exc}",
            attempted_source="jira",
        )
    if isinstance(exc, JiraError):
        return ToolError(
            error_type="upstream_error",
            message=str(exc),
            attempted_source="jira",
        )
    return ToolError(
        error_type="upstream_error",
        message=f"Unexpected error: {exc}",
        attempted_source="jira",
    )


class SearchIssuesTool(BaseTool):
    """Domain tool for searching issues in Jira."""

    name: str = "search_issues"
    description: str = (
        "Search Jira issues using JQL syntax. Returns matching issues and pagination cursor."
    )

    def __init__(self, adapter: JiraAdapter) -> None:
        self._adapter = adapter

    def _get_source_type(self) -> Literal["jira"]:
        return "jira"

    def _map_error(self, exc: Exception) -> ToolError:
        return _map_jira_error(exc)

    async def _execute(self, input_data: Any) -> tuple[SearchIssuesOutput, str]:
        if not isinstance(input_data, SearchIssuesInput):
            input_data = SearchIssuesInput.model_validate(input_data)

        search_res = await self._adapter.search_issues(
            jql=input_data.jql,
            max_results=input_data.max_results,
            next_page_token=input_data.next_page_token,
        )
        output = SearchIssuesOutput(
            issues=search_res.issues,
            next_page_token=search_res.next_page_token,
            total_returned=len(search_res.issues),
        )
        # A search result is an evidence group, but the compact source
        # reference must be a stable Jira key. Models are instructed to cite
        # issue keys; a variable "+N issues" suffix broke provenance checks.
        source_ref = search_res.issues[0].key if search_res.issues else "Jira: No matching issues"
        return output, source_ref


class GetIssueTool(BaseTool):
    """Domain tool for retrieving a single Jira issue by issue key."""

    name: str = "get_issue"
    description: str = (
        "Retrieve a single Jira issue by its uppercase project-number key (e.g. 'PAY-117')."
    )

    def __init__(self, adapter: JiraAdapter) -> None:
        self._adapter = adapter

    def _get_source_type(self) -> Literal["jira"]:
        return "jira"

    def _map_error(self, exc: Exception) -> ToolError:
        return _map_jira_error(exc)

    async def _execute(self, input_data: Any) -> tuple[GetIssueOutput, str]:
        if not isinstance(input_data, GetIssueInput):
            input_data = GetIssueInput.model_validate(input_data)

        issue = await self._adapter.get_issue(input_data.issue_key)
        output = GetIssueOutput(issue=issue)
        source_ref = input_data.issue_key
        return output, source_ref


class GetIssueCommentsTool(BaseTool):
    """Domain tool for retrieving comments on a Jira issue."""

    name: str = "get_issue_comments"
    description: str = "Retrieve diagnostic engineering comments, incident notes, and deployment records for an issue."

    def __init__(self, adapter: JiraAdapter) -> None:
        self._adapter = adapter

    def _get_source_type(self) -> Literal["jira"]:
        return "jira"

    def _map_error(self, exc: Exception) -> ToolError:
        return _map_jira_error(exc)

    async def _execute(self, input_data: Any) -> tuple[GetIssueCommentsOutput, str]:
        if not isinstance(input_data, GetIssueCommentsInput):
            input_data = GetIssueCommentsInput.model_validate(input_data)

        comments = await self._adapter.get_issue_comments(input_data.issue_key)
        output = GetIssueCommentsOutput(issue_key=input_data.issue_key, comments=comments)
        source_ref = f"{input_data.issue_key} (Comments)"
        return output, source_ref


class GetLinkedIssuesTool(BaseTool):
    """Domain tool for inspecting issue dependencies, duplicates, and blockers."""

    name: str = "get_linked_issues"
    description: str = "Inspect related, blocker, or parent-child issue links for an issue key."

    def __init__(self, adapter: JiraAdapter) -> None:
        self._adapter = adapter

    def _get_source_type(self) -> Literal["jira"]:
        return "jira"

    def _map_error(self, exc: Exception) -> ToolError:
        return _map_jira_error(exc)

    async def _execute(self, input_data: Any) -> tuple[GetLinkedIssuesOutput, str]:
        if not isinstance(input_data, GetLinkedIssuesInput):
            input_data = GetLinkedIssuesInput.model_validate(input_data)

        links = await self._adapter.get_linked_issues(input_data.issue_key)
        output = GetLinkedIssuesOutput(issue_key=input_data.issue_key, linked_issues=links)
        source_ref = f"{input_data.issue_key} (Linked issues)"
        return output, source_ref
