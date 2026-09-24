"""Unit tests for ZendeskAdapter and ZendeskClient error mappings."""

import httpx
import pytest
import respx
from app.domain.zendesk import ZendeskTicket
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.integrations.zendesk.client import ZendeskClient
from app.integrations.zendesk.exceptions import (
    ZendeskAuthError,
    ZendeskConnectionError,
    ZendeskNotFoundError,
    ZendeskResponseError,
    ZendeskTimeoutError,
)

BASE_URL = "http://mock-zendesk.test"


@pytest.fixture
def zendesk_adapter() -> ZendeskAdapter:
    """Create a ZendeskAdapter pointing to a mock base URL."""
    client = ZendeskClient(
        base_url=BASE_URL,
        username="mock@pocket.test",
        api_key="test-api-token",
        timeout_seconds=1.0,
    )
    return ZendeskAdapter(client)


@pytest.mark.asyncio
async def test_search_tickets_success(zendesk_adapter: ZendeskAdapter) -> None:
    """Verify search_tickets parses response into typed ZendeskSearchResult."""
    mock_response = {
        "results": [
            {
                "id": 101,
                "requester_id": "usr_001428",
                "subject": "Transfer pending to Bank A",
                "description": "Funds not received by beneficiary",
                "status": "open",
                "priority": "high",
                "channel": "web",
                "tags": ["transfer", "bank_a"],
                "created_at": "2026-08-14T10:00:00Z",
                "updated_at": "2026-08-14T10:00:00Z",
            }
        ],
        "count": 1,
        "page": 1,
    }

    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v2/search.json").respond(json=mock_response, status_code=200)

        result = await zendesk_adapter.search_tickets("transfer pending")
        assert result.count == 1
        assert len(result.tickets) == 1
        ticket = result.tickets[0]
        assert isinstance(ticket, ZendeskTicket)
        assert ticket.id == 101
        assert ticket.requester_id == "usr_001428"
        assert ticket.status == "open"


@pytest.mark.asyncio
async def test_get_ticket_with_comments(zendesk_adapter: ZendeskAdapter) -> None:
    """Verify get_ticket retrieves ticket and conversation comments."""
    ticket_payload = {
        "ticket": {
            "id": 1047,
            "requester_id": 1428,
            "subject": "Callback delay on partner switch",
            "description": "Transfer stuck on processing",
            "status": "pending",
            "priority": "high",
            "channel": "email",
            "tags": ["transfer", "delay"],
            "created_at": "2026-08-14T12:00:00Z",
        }
    }
    comments_payload = {
        "comments": [
            {
                "id": 501,
                "author_id": 1428,
                "body": "Still no confirmation after 2 hours",
                "created_at": "2026-08-14T12:30:00Z",
                "public": True,
            }
        ]
    }

    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v2/tickets/1047.json").respond(json=ticket_payload, status_code=200)
        respx_mock.get("/api/v2/tickets/1047/comments.json").respond(
            json=comments_payload, status_code=200
        )

        ticket = await zendesk_adapter.get_ticket(1047)
        assert ticket.id == 1047
        assert ticket.requester_id == "usr_001428"
        assert len(ticket.comments) == 1
        assert ticket.comments[0].body == "Still no confirmation after 2 hours"


@pytest.mark.asyncio
async def test_adapter_raises_not_found(zendesk_adapter: ZendeskAdapter) -> None:
    """Verify HTTP 404 is mapped to ZendeskNotFoundError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v2/tickets/999.json").respond(status_code=404)

        with pytest.raises(ZendeskNotFoundError) as exc_info:
            await zendesk_adapter.get_ticket(999)
        assert "999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_adapter_raises_auth_error(zendesk_adapter: ZendeskAdapter) -> None:
    """Verify HTTP 401 is mapped to ZendeskAuthError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v2/search.json").respond(status_code=401)

        with pytest.raises(ZendeskAuthError):
            await zendesk_adapter.search_tickets("pending")


@pytest.mark.asyncio
async def test_adapter_raises_timeout_error(zendesk_adapter: ZendeskAdapter) -> None:
    """Verify request timeout is mapped to ZendeskTimeoutError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v2/search.json").mock(side_effect=httpx.TimeoutException("Timeout"))

        with pytest.raises(ZendeskTimeoutError):
            await zendesk_adapter.search_tickets("pending")


@pytest.mark.asyncio
async def test_adapter_raises_connection_error(zendesk_adapter: ZendeskAdapter) -> None:
    """Verify connect error is mapped to ZendeskConnectionError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v2/search.json").mock(side_effect=httpx.ConnectError("Refused"))

        with pytest.raises(ZendeskConnectionError):
            await zendesk_adapter.search_tickets("pending")


@pytest.mark.asyncio
async def test_adapter_raises_response_error_on_malformed_json(
    zendesk_adapter: ZendeskAdapter,
) -> None:
    """Verify malformed response is mapped to ZendeskResponseError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/api/v2/tickets/101.json").respond(text="not valid json", status_code=200)

        with pytest.raises(ZendeskResponseError):
            await zendesk_adapter.get_ticket(101)
