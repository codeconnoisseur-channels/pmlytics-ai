"""Role-bound toolset and tool registry enforcing agent security boundaries."""

import logging
from typing import Any

from pydantic import BaseModel

from app.integrations.jira.adapter import JiraAdapter
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.tools.analytics import QueryAnalyticsTool
from app.tools.base import AgentRole, BaseTool, ToolError, ToolPermissionError, ToolResult
from app.tools.engineering import (
    GetIssueCommentsTool,
    GetIssueTool,
    GetLinkedIssuesTool,
    SearchIssuesTool,
)
from app.tools.support import GetTicketCommentsTool, GetTicketTool, SearchTicketsTool

logger = logging.getLogger(__name__)

# Locked permissions matrix mapping each logical role to allowed tool names
ROLE_PERMISSION_MATRIX: dict[AgentRole, set[str]] = {
    "research": {
        "search_tickets",
        "get_ticket",
        "get_ticket_comments",
    },
    "analytics": {
        "query_analytics",
    },
    "engineering": {
        "search_issues",
        "get_issue",
        "get_issue_comments",
        "get_linked_issues",
    },
    "pm": set(),
    "critic": set(),
}


class RoleBoundToolset:
    """Authoritative security boundary encapsulating tools permitted for an agent role.

    Provides resolution and invocation guards guaranteeing that agents cannot
    access or execute forbidden tools.
    """

    def __init__(self, role: AgentRole, tools: dict[str, BaseTool]) -> None:
        self._role = role
        self._tools = tools

    @property
    def role(self) -> AgentRole:
        """Return the agent role bound to this toolset."""
        return self._role

    @property
    def tools(self) -> list[BaseTool]:
        """Return the authorized list of tools for this role."""
        return list(self._tools.values())

    def get_tool(self, tool_name: str) -> BaseTool:
        """Resolve a tool by name.

        Raises:
            ToolPermissionError: If the tool is not authorized for this role.
        """
        if tool_name not in self._tools:
            raise ToolPermissionError(
                f"Role '{self._role}' is not authorized to access tool '{tool_name}'."
            )
        return self._tools[tool_name]

    async def invoke_tool(self, tool_name: str, input_data: BaseModel) -> ToolResult[Any]:
        """Invoke a tool by name, strictly blocking unauthorized execution.

        Returns a structured permission_denied ToolResult with attempted_source=None
        and provenance=None if unauthorized.
        """
        if tool_name not in self._tools:
            logger.warning(
                "Blocked unauthorized invocation attempt: role='%s' attempted to invoke '%s'",
                self._role,
                tool_name,
            )
            return ToolResult(
                success=False,
                data=None,
                error=ToolError(
                    error_type="permission_denied",
                    message=f"Role '{self._role}' is not authorized to access tool '{tool_name}'.",
                    attempted_source=None,
                    details={"role": self._role, "requested_tool": tool_name},
                ),
                provenance=None,
                execution_duration_ms=0.0,
            )

        tool = self._tools[tool_name]
        return await tool.run(input_data)


class ToolRegistry:
    """Central repository of domain tools responsible for creating RoleBoundToolsets."""

    def __init__(self) -> None:
        self._registered_tools: dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Register a domain tool instance in the registry."""
        self._registered_tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> BaseTool:
        """Retrieve a registered tool by name."""
        if tool_name not in self._registered_tools:
            raise KeyError(f"Tool '{tool_name}' is not registered.")
        return self._registered_tools[tool_name]

    def get_all_tools(self) -> list[BaseTool]:
        """Return all registered tools."""
        return list(self._registered_tools.values())

    def get_toolset_for_role(self, role: AgentRole) -> RoleBoundToolset:
        """Construct a RoleBoundToolset exposing exclusively the tools permitted for the role."""
        allowed_names = ROLE_PERMISSION_MATRIX.get(role, set())
        allowed_tools: dict[str, BaseTool] = {
            name: self._registered_tools[name]
            for name in allowed_names
            if name in self._registered_tools
        }
        return RoleBoundToolset(role=role, tools=allowed_tools)

    @classmethod
    def create_default(
        cls,
        zendesk_adapter: ZendeskAdapter,
        posthog_adapter: PostHogAdapter,
        jira_adapter: JiraAdapter,
    ) -> "ToolRegistry":
        """Instantiate a registry populated with the approved 8 domain tools."""
        registry = cls()

        # Support tools (Research Agent)
        registry.register_tool(SearchTicketsTool(zendesk_adapter))
        registry.register_tool(GetTicketTool(zendesk_adapter))
        registry.register_tool(GetTicketCommentsTool(zendesk_adapter))

        # Analytics tool (Analytics Agent)
        registry.register_tool(QueryAnalyticsTool(posthog_adapter))

        # Engineering tools (Engineering Agent)
        registry.register_tool(SearchIssuesTool(jira_adapter))
        registry.register_tool(GetIssueTool(jira_adapter))
        registry.register_tool(GetIssueCommentsTool(jira_adapter))
        registry.register_tool(GetLinkedIssuesTool(jira_adapter))

        return registry
