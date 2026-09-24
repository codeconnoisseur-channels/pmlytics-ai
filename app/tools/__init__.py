"""Pocket domain tool layer exposing typed tools and role-bound toolsets."""

from app.tools.analytics import (
    AllowedAnalyticsProperty,
    AnalyticsPropertyFilter,
    AnalyticsQueryIntent,
    FilterOperator,
    QueryAnalyticsInput,
    QueryAnalyticsOutput,
    QueryAnalyticsTool,
)
from app.tools.base import (
    AgentRole,
    BaseTool,
    ToolError,
    ToolPermissionError,
    ToolProvenance,
    ToolResult,
)
from app.tools.engineering import (
    GetIssueCommentsInput,
    GetIssueCommentsOutput,
    GetIssueCommentsTool,
    GetIssueInput,
    GetIssueOutput,
    GetIssueTool,
    GetLinkedIssuesInput,
    GetLinkedIssuesOutput,
    GetLinkedIssuesTool,
    SearchIssuesInput,
    SearchIssuesOutput,
    SearchIssuesTool,
)
from app.tools.registry import (
    ROLE_PERMISSION_MATRIX,
    RoleBoundToolset,
    ToolRegistry,
)
from app.tools.support import (
    GetTicketCommentsInput,
    GetTicketCommentsOutput,
    GetTicketCommentsTool,
    GetTicketInput,
    GetTicketOutput,
    GetTicketTool,
    SearchTicketsInput,
    SearchTicketsOutput,
    SearchTicketsTool,
)

__all__ = [
    # Base contracts & security
    "BaseTool",
    "ToolResult",
    "ToolProvenance",
    "ToolError",
    "ToolPermissionError",
    "AgentRole",
    "RoleBoundToolset",
    "ToolRegistry",
    "ROLE_PERMISSION_MATRIX",
    # Support tools (Research Agent)
    "SearchTicketsTool",
    "SearchTicketsInput",
    "SearchTicketsOutput",
    "GetTicketTool",
    "GetTicketInput",
    "GetTicketOutput",
    "GetTicketCommentsTool",
    "GetTicketCommentsInput",
    "GetTicketCommentsOutput",
    # Analytics tool (Analytics Agent)
    "QueryAnalyticsTool",
    "QueryAnalyticsInput",
    "QueryAnalyticsOutput",
    "AnalyticsPropertyFilter",
    "AnalyticsQueryIntent",
    "AllowedAnalyticsProperty",
    "FilterOperator",
    # Engineering tools (Engineering Agent)
    "SearchIssuesTool",
    "SearchIssuesInput",
    "SearchIssuesOutput",
    "GetIssueTool",
    "GetIssueInput",
    "GetIssueOutput",
    "GetIssueCommentsTool",
    "GetIssueCommentsInput",
    "GetIssueCommentsOutput",
    "GetLinkedIssuesTool",
    "GetLinkedIssuesInput",
    "GetLinkedIssuesOutput",
]
