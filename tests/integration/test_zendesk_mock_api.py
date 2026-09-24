"""End-to-end live HTTP integration test for Mock Zendesk and ZendeskAdapter.

Exercises the full chain:
ZendeskAdapter -> actual HTTP wire -> Mock Zendesk (compat layer + pinned upstream) -> typed app.domain.zendesk objects.
"""

import pytest
from app.domain.zendesk import ZendeskTicket
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.integrations.zendesk.client import ZendeskClient
from seed.zendesk.minimal_loader import get_demo_tickets_payload, load_minimal_tickets


@pytest.mark.asyncio
async def test_zendesk_mock_api_end_to_end(mock_zendesk_server: str) -> None:
    """Verify live HTTP health-check, seeding, ticket retrieval, comments, and search."""
    client = ZendeskClient(
        base_url=mock_zendesk_server,
        username="mock@pocket.test",
        api_key="mock-zendesk-token-pocket",
        timeout_seconds=2.0,
    )
    adapter = ZendeskAdapter(client)

    # 1. Verify health check endpoint (GET /api/v2/tickets.json)
    health_resp = await client.get("api/v2/tickets.json")
    assert "tickets" in health_resp

    # 2. Seed minimal tickets via HTTP POST /api/v2/tickets.json
    created_ids = await load_minimal_tickets(client)
    assert len(created_ids) == len(get_demo_tickets_payload())
    first_ticket_id = created_ids[0]

    # 3. Retrieve single ticket with comments over actual HTTP
    ticket = await adapter.get_ticket(first_ticket_id)
    assert isinstance(ticket, ZendeskTicket)
    assert ticket.id == first_ticket_id
    assert "transfer" in ticket.tags
    assert len(ticket.comments) >= 1
    assert "provide an update in the app" in ticket.comments[0].body

    # 4. Search tickets by keyword 'transfer' over actual HTTP
    search_results = await adapter.search_tickets("transfer")
    assert search_results.count >= 4
    assert all(isinstance(t, ZendeskTicket) for t in search_results.tickets)
    assert any("scenario_1" in t.tags and "bank_a" in t.tags for t in search_results.tickets)

    # 5. Search with tag filter 'bank_b'
    search_bank_b = await adapter.search_tickets("tag:bank_b")
    assert search_bank_b.count >= 2
    assert all("bank_b" in t.tags for t in search_bank_b.tickets)

    # 6. Verify 404 behavior over live HTTP
    from app.integrations.zendesk.exceptions import ZendeskNotFoundError

    with pytest.raises(ZendeskNotFoundError):
        await adapter.get_ticket(999999)
