"""Unit tests for Support domain tools (Zendesk)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.domain.zendesk import ZendeskComment, ZendeskTicket
from app.integrations.zendesk.adapter import ZendeskAdapter, ZendeskSearchResult
from app.integrations.zendesk.exceptions import ZendeskNotFoundError, ZendeskTimeoutError
from app.tools.support import (
    GetTicketCommentsInput,
    GetTicketCommentsTool,
    GetTicketInput,
    GetTicketTool,
    SearchTicketsInput,
    SearchTicketsTool,
)
from pydantic import ValidationError


@pytest.fixture
def mock_zendesk_adapter() -> MagicMock:
    return MagicMock(spec=ZendeskAdapter)


@pytest.fixture
def sample_ticket() -> ZendeskTicket:
    return ZendeskTicket(
        id=101,
        subject="Transfer delayed",
        description="My transfer is pending for 2 hours",
        status="open",
        priority="high",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000101",
        tags=["transfer", "pending"],
    )


@pytest.fixture
def sample_comment() -> ZendeskComment:
    return ZendeskComment(
        id=1,
        ticket_id=101,
        author_id="usr_000101",
        body="Still pending please check",
        created_at=datetime.now(UTC),
        public=True,
    )


@pytest.mark.asyncio
async def test_search_tickets_tool_success(
    mock_zendesk_adapter: MagicMock,
    sample_ticket: ZendeskTicket,
) -> None:
    """Verify search_tickets returns matching tickets and records provenance."""
    tool = SearchTicketsTool(mock_zendesk_adapter)
    mock_zendesk_adapter.search_tickets = AsyncMock(
        return_value=ZendeskSearchResult(tickets=[sample_ticket], count=1)
    )

    inp = SearchTicketsInput(query="transfer pending", page=1, limit=10)
    res = await tool.run(inp)

    assert res.success is True
    assert res.error is None
    assert res.provenance is not None
    assert res.provenance.source_type == "zendesk"
    assert res.provenance.source_reference == "query:transfer pending:page:1"
    assert res.data is not None
    assert res.data.total_count == 1
    assert len(res.data.tickets) == 1
    assert res.data.tickets[0].id == 101
    assert res.execution_duration_ms >= 0


@pytest.mark.asyncio
async def test_search_tickets_respects_investigation_period(
    mock_zendesk_adapter: MagicMock,
) -> None:
    """Support evidence outside the PM-selected period must not enter the report."""
    inside = ZendeskTicket(
        id=101,
        requester_id="usr_000101",
        subject="Inside period",
        description="Relevant report",
        status="open",
        priority="high",
        channel="web",
        created_at=datetime(2026, 8, 10, tzinfo=UTC),
        updated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    outside = inside.model_copy(
        update={
            "id": 102,
            "requester_id": "usr_000102",
            "subject": "Outside period",
            "created_at": datetime(2026, 7, 10, tzinfo=UTC),
            "updated_at": datetime(2026, 7, 10, tzinfo=UTC),
        }
    )
    mock_zendesk_adapter.search_tickets = AsyncMock(
        return_value=ZendeskSearchResult(tickets=[inside, outside], count=2)
    )

    result = await SearchTicketsTool(mock_zendesk_adapter).run(
        SearchTicketsInput(
            query="transfer",
            start_time=datetime(2026, 8, 1, tzinfo=UTC),
            end_time=datetime(2026, 8, 20, tzinfo=UTC),
        )
    )

    assert result.success is True
    assert result.data is not None
    assert [ticket.id for ticket in result.data.tickets] == [101]
    assert result.data.total_count == 1


@pytest.mark.asyncio
async def test_get_ticket_tool_success(
    mock_zendesk_adapter: MagicMock,
    sample_ticket: ZendeskTicket,
) -> None:
    """Verify get_ticket retrieves single ticket by ID and records provenance."""
    tool = GetTicketTool(mock_zendesk_adapter)
    mock_zendesk_adapter.get_ticket = AsyncMock(return_value=sample_ticket)

    inp = GetTicketInput(ticket_id=101)
    res = await tool.run(inp)

    assert res.success is True
    assert res.data is not None
    assert res.data.ticket.id == 101
    assert res.provenance is not None
    assert res.provenance.source_type == "zendesk"
    assert res.provenance.source_reference == "ticket_id:101"


@pytest.mark.asyncio
async def test_get_ticket_tool_not_found(mock_zendesk_adapter: MagicMock) -> None:
    """Verify ZendeskNotFoundError maps to not_found with provenance=None."""
    tool = GetTicketTool(mock_zendesk_adapter)
    mock_zendesk_adapter.get_ticket = AsyncMock(
        side_effect=ZendeskNotFoundError("Ticket 999 not found")
    )

    inp = GetTicketInput(ticket_id=999)
    res = await tool.run(inp)

    assert res.success is False
    assert res.data is None
    assert res.provenance is None
    assert res.error is not None
    assert res.error.error_type == "not_found"
    assert res.error.attempted_source == "zendesk"


@pytest.mark.asyncio
async def test_get_ticket_comments_tool_success(
    mock_zendesk_adapter: MagicMock,
    sample_comment: ZendeskComment,
) -> None:
    """Verify get_ticket_comments retrieves comments for ticket."""
    tool = GetTicketCommentsTool(mock_zendesk_adapter)
    mock_zendesk_adapter.get_ticket_comments = AsyncMock(return_value=[sample_comment])

    inp = GetTicketCommentsInput(ticket_id=101)
    res = await tool.run(inp)

    assert res.success is True
    assert res.data is not None
    assert res.data.ticket_id == 101
    assert len(res.data.comments) == 1
    assert res.provenance is not None
    assert res.provenance.source_reference == "ticket_comments:101"


@pytest.mark.asyncio
async def test_support_tool_timeout(mock_zendesk_adapter: MagicMock) -> None:
    """Verify ZendeskTimeoutError maps to timeout with attempted_source=zendesk."""
    tool = SearchTicketsTool(mock_zendesk_adapter)
    mock_zendesk_adapter.search_tickets = AsyncMock(
        side_effect=ZendeskTimeoutError("Zendesk timeout")
    )

    inp = SearchTicketsInput(query="timeout_test")
    res = await tool.run(inp)

    assert res.success is False
    assert res.data is None
    assert res.provenance is None
    assert res.error is not None
    assert res.error.error_type == "timeout"
    assert res.error.attempted_source == "zendesk"


def test_support_input_validation() -> None:
    """Verify pydantic validation on support tool inputs."""
    with pytest.raises(ValidationError):
        SearchTicketsInput(query="")  # min_length 1

    with pytest.raises(ValidationError):
        GetTicketInput(ticket_id=0)  # ge 1
