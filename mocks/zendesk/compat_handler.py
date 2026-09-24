"""Pocket compatibility layer extending allan-simon/http-zendesk-mock.

This module subclasses upstream MockHandler to support:
1. Keyword and tag search across subject, description, and tags in TICKETS_STORE.
2. Formatted search JSON pagination envelopes: {results, count, next_page, prev_page}.
3. Deterministic ticket listing GET /api/v2/tickets.json.
4. Clean in-memory store resets for testing.
"""

import os
import re
import urllib.parse
from copy import deepcopy
from typing import Any

# Ensure environment variables expected by upstream are populated
if "MOCK_ZENDESK_USERNAME" not in os.environ:
    os.environ["MOCK_ZENDESK_USERNAME"] = "mock@pocket.test"
if "MOCK_ZENDESK_API_KEY" not in os.environ:
    os.environ["MOCK_ZENDESK_API_KEY"] = "mock-zendesk-token-pocket"

from mocks.zendesk.upstream.mock_zendesk.handler import (
    COMMENTS_STORE,
    DATA_STORE,
    TICKETS_STORE,
    USERS_STORE,
    MockHandler,
)


def reset_mock_stores() -> None:
    """Clear all in-memory mock stores for clean test isolation."""
    TICKETS_STORE.clear()
    COMMENTS_STORE.clear()
    USERS_STORE.clear()
    DATA_STORE.clear()


class PocketZendeskCompatHandler(MockHandler):
    """Subclass of upstream MockHandler providing Pocket-specific search and listing semantics."""

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests with Pocket search and listing compatibility."""
        if self._verify_auth() is False:
            self._send_json_response({}, status_code=401)
            return

        # 1. Search endpoint: /api/v2/search or /api/v2/search.json
        if self.path.startswith("/api/v2/search"):
            self._handle_compat_search()
            return

        # 2. Tickets list / health-check endpoint: /api/v2/tickets.json or /api/v2/tickets
        if self.path == "/api/v2/tickets.json" or self.path == "/api/v2/tickets":
            tickets = list(TICKETS_STORE.values())
            self._send_json_response({"tickets": tickets, "count": len(tickets)}, status_code=200)
            return

        # Fall back to upstream handling for specific ticket and comment retrieval
        super().do_GET()  # type: ignore[no-untyped-call]

    def _handle_compat_search(self) -> None:
        """Handle search queries with keyword, tag, and status filtering."""
        query_string = self.path.split("?", 1)[1] if "?" in self.path else ""
        parsed_qs = urllib.parse.parse_qs(query_string)
        query_param = parsed_qs.get("query", [""])[0]

        # Extract tokens from query parameter
        # Query may contain key:value pairs (e.g. status:open, type:ticket) and free text terms
        tokens = [t.strip() for t in query_param.split() if t.strip()]

        key_value_filters: dict[str, str] = {}
        free_text_terms: list[str] = []

        for token in tokens:
            if ":" in token:
                k, v = token.split(":", 1)
                key_value_filters[k.lower()] = v.lower()
            else:
                free_text_terms.append(token.lower())

        matching_tickets: list[dict[str, Any]] = []

        for ticket in TICKETS_STORE.values():
            if not self._ticket_matches(ticket, key_value_filters, free_text_terms):
                continue
            t_copy = deepcopy(ticket)
            t_copy["result_type"] = "ticket"
            matching_tickets.append(t_copy)

        # Pagination support
        page = int(parsed_qs.get("page", ["1"])[0])
        page_size = int(parsed_qs.get("per_page", ["100"])[0])
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = matching_tickets[start_idx:end_idx]

        response_payload = {
            "results": paginated_results,
            "count": len(matching_tickets),
            "page": page,
            "next_page": None,
            "previous_page": None,
        }
        self._send_json_response(response_payload, status_code=200)

    def _ticket_matches(
        self,
        ticket: dict[str, Any],
        kv_filters: dict[str, str],
        free_terms: list[str],
    ) -> bool:
        """Check whether a ticket matches key:value filters and free-text terms."""
        # Check key-value filters
        if "status" in kv_filters and str(ticket.get("status", "")).lower() != kv_filters["status"]:
            return False

        if (
            "priority" in kv_filters
            and str(ticket.get("priority", "")).lower() != kv_filters["priority"]
        ):
            return False

        if "tag" in kv_filters:
            tags = [t.lower() for t in ticket.get("tags", [])]
            if kv_filters["tag"] not in tags:
                return False

        if "type" in kv_filters and kv_filters["type"] != "ticket":
            return False

        if not free_terms:
            return True

        # Check free-text terms across subject, description, and tags
        subject = str(ticket.get("subject", "")).lower()
        description = str(ticket.get("description", "")).lower()
        tags_str = " ".join(ticket.get("tags", [])).lower()
        searchable_text = f"{subject} {description} {tags_str}"

        # Match all free terms (AND logic)
        for term in free_terms:
            pattern = rf"\b{re.escape(term)}"
            if not re.search(pattern, searchable_text):
                return False

        return True
