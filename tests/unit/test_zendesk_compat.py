"""Unit tests for Pocket Zendesk compatibility layer."""

from mocks.zendesk.compat_handler import PocketZendeskCompatHandler, reset_mock_stores
from mocks.zendesk.upstream.mock_zendesk.handler import TICKETS_STORE


def test_compat_search_keyword_and_tag_filtering() -> None:
    """Verify that PocketZendeskCompatHandler correctly filters tickets by term and tags."""
    reset_mock_stores()

    # Prepopulate TICKETS_STORE
    TICKETS_STORE[1] = {
        "id": 1,
        "subject": "Transfer pending to Bank A",
        "description": "My transaction has been processing for hours",
        "status": "open",
        "priority": "high",
        "tags": ["transfer", "bank_a", "delay"],
    }
    TICKETS_STORE[2] = {
        "id": 2,
        "subject": "Cannot reset password",
        "description": "Password reset email not received",
        "status": "solved",
        "priority": "normal",
        "tags": ["account", "password"],
    }
    TICKETS_STORE[3] = {
        "id": 3,
        "subject": "Another transfer delay on Bank B",
        "description": "Transfer to Bank B pending",
        "status": "open",
        "priority": "normal",
        "tags": ["transfer", "bank_b"],
    }

    handler = PocketZendeskCompatHandler.__new__(PocketZendeskCompatHandler)

    # 1. Search for keyword "transfer"
    matches = [
        t
        for t in TICKETS_STORE.values()
        if handler._ticket_matches(t, kv_filters={}, free_terms=["transfer"])
    ]
    assert len(matches) == 2
    assert {m["id"] for m in matches} == {1, 3}

    # 2. Search for keyword "transfer" + filter "status:open"
    matches_open = [
        t
        for t in TICKETS_STORE.values()
        if handler._ticket_matches(t, kv_filters={"status": "open"}, free_terms=["transfer"])
    ]
    assert len(matches_open) == 2

    # 3. Search with specific tag "bank_a"
    matches_bank_a = [
        t
        for t in TICKETS_STORE.values()
        if handler._ticket_matches(t, kv_filters={"tag": "bank_a"}, free_terms=[])
    ]
    assert len(matches_bank_a) == 1
    assert matches_bank_a[0]["id"] == 1

    # 4. Search for non-matching term
    matches_none = [
        t
        for t in TICKETS_STORE.values()
        if handler._ticket_matches(t, kv_filters={}, free_terms=["crypto"])
    ]
    assert len(matches_none) == 0

    reset_mock_stores()
