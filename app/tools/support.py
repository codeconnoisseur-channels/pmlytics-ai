"""Support domain tools wrapping ZendeskAdapter for the Research Agent."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.domain.zendesk import ZendeskComment, ZendeskTicket
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.integrations.zendesk.exceptions import (
    ZendeskAuthError,
    ZendeskError,
    ZendeskNotFoundError,
    ZendeskTimeoutError,
)
from app.tools.base import BaseTool, ToolError

# -----------------------------------------------------------------------------
# Input & Output Contracts
# -----------------------------------------------------------------------------


class SearchTicketsInput(BaseModel):
    """Input parameters for searching Zendesk tickets."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search query string or tag to find matching tickets",
    )
    page: int = Field(default=1, ge=1, le=100, description="Page number for pagination")
    limit: int = Field(default=20, ge=1, le=100, description="Number of tickets per page")
    start_time: datetime | None = Field(
        default=None,
        description="Inclusive investigation-period start applied to ticket creation time",
    )
    end_time: datetime | None = Field(
        default=None,
        description="Inclusive investigation-period end applied to ticket creation time",
    )


class SearchTicketsOutput(BaseModel):
    """Output envelope containing matching Zendesk tickets."""

    tickets: list[ZendeskTicket]
    total_count: int
    page: int


class GetTicketInput(BaseModel):
    """Input parameters for retrieving a specific Zendesk ticket."""

    ticket_id: int = Field(..., ge=1, description="Unique Zendesk ticket ID")


class GetTicketOutput(BaseModel):
    """Output envelope containing the requested Zendesk ticket."""

    ticket: ZendeskTicket


class GetTicketCommentsInput(BaseModel):
    """Input parameters for retrieving comments on a Zendesk ticket."""

    ticket_id: int = Field(..., ge=1, description="Unique Zendesk ticket ID")


class GetTicketCommentsOutput(BaseModel):
    """Output envelope containing comments for a Zendesk ticket."""

    ticket_id: int
    comments: list[ZendeskComment]


# -----------------------------------------------------------------------------
# Domain Tools
# -----------------------------------------------------------------------------


def _map_zendesk_error(exc: Exception) -> ToolError:
    """Normalize Zendesk integration exceptions into structured ToolError."""
    if isinstance(exc, ZendeskNotFoundError):
        return ToolError(
            error_type="not_found",
            message=str(exc),
            attempted_source="zendesk",
        )
    if isinstance(exc, ZendeskTimeoutError):
        return ToolError(
            error_type="timeout",
            message=str(exc),
            attempted_source="zendesk",
        )
    if isinstance(exc, ZendeskAuthError):
        return ToolError(
            error_type="authentication_error",
            message=str(exc),
            attempted_source="zendesk",
        )
    if isinstance(exc, ValidationError):
        return ToolError(
            error_type="invalid_input",
            message=f"Validation error: {exc}",
            attempted_source="zendesk",
        )
    if isinstance(exc, ZendeskError):
        return ToolError(
            error_type="upstream_error",
            message=str(exc),
            attempted_source="zendesk",
        )
    return ToolError(
        error_type="upstream_error",
        message=f"Unexpected error: {exc}",
        attempted_source="zendesk",
    )


class SearchTicketsTool(BaseTool):
    """Domain tool for searching customer support tickets in Zendesk."""

    name: str = "search_tickets"
    description: str = (
        "Search customer support tickets by keyword or tag. Returns a paginated list of tickets."
    )

    def __init__(self, adapter: ZendeskAdapter) -> None:
        self._adapter = adapter

    def _get_source_type(self) -> Literal["zendesk"]:
        return "zendesk"

    def _map_error(self, exc: Exception) -> ToolError:
        return _map_zendesk_error(exc)

    async def _execute(self, input_data: Any) -> tuple[SearchTicketsOutput, str]:
        if not isinstance(input_data, SearchTicketsInput):
            input_data = SearchTicketsInput.model_validate(input_data)

        search_res = await self._adapter.search_tickets(
            query=input_data.query,
            page=input_data.page,
            page_size=input_data.limit,
        )
        tickets = search_res.tickets
        if input_data.start_time is not None:
            tickets = [ticket for ticket in tickets if ticket.created_at >= input_data.start_time]
        if input_data.end_time is not None:
            tickets = [ticket for ticket in tickets if ticket.created_at <= input_data.end_time]

        output = SearchTicketsOutput(
            tickets=tickets,
            total_count=len(tickets),
            page=input_data.page,
        )
        source_ref = f"query:{input_data.query}:page:{input_data.page}"
        return output, source_ref


class GetTicketTool(BaseTool):
    """Domain tool for retrieving a single Zendesk ticket by ID."""

    name: str = "get_ticket"
    description: str = "Retrieve a single Zendesk support ticket by its numeric ticket ID."

    def __init__(self, adapter: ZendeskAdapter) -> None:
        self._adapter = adapter

    def _get_source_type(self) -> Literal["zendesk"]:
        return "zendesk"

    def _map_error(self, exc: Exception) -> ToolError:
        return _map_zendesk_error(exc)

    async def _execute(self, input_data: Any) -> tuple[GetTicketOutput, str]:
        if not isinstance(input_data, GetTicketInput):
            input_data = GetTicketInput.model_validate(input_data)

        ticket = await self._adapter.get_ticket(ticket_id=input_data.ticket_id)
        output = GetTicketOutput(ticket=ticket)
        source_ref = f"ticket_id:{input_data.ticket_id}"
        return output, source_ref


class GetTicketCommentsTool(BaseTool):
    """Domain tool for retrieving comments associated with a Zendesk ticket."""

    name: str = "get_ticket_comments"
    description: str = (
        "Retrieve customer and agent comments for a specific Zendesk ticket by ticket ID."
    )

    def __init__(self, adapter: ZendeskAdapter) -> None:
        self._adapter = adapter

    def _get_source_type(self) -> Literal["zendesk"]:
        return "zendesk"

    def _map_error(self, exc: Exception) -> ToolError:
        return _map_zendesk_error(exc)

    async def _execute(self, input_data: Any) -> tuple[GetTicketCommentsOutput, str]:
        if not isinstance(input_data, GetTicketCommentsInput):
            input_data = GetTicketCommentsInput.model_validate(input_data)

        comments = await self._adapter.get_ticket_comments(ticket_id=input_data.ticket_id)
        output = GetTicketCommentsOutput(
            ticket_id=input_data.ticket_id,
            comments=comments,
        )
        source_ref = f"ticket_comments:{input_data.ticket_id}"
        return output, source_ref
