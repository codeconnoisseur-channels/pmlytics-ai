"""High-level application adapter for Zendesk customer support integration.

Provides a typed, read-only interface for searching tickets, retrieving individual
tickets, and retrieving ticket comments. Maps raw JSON representations into
app.domain.zendesk models and surfaces typed exceptions.
"""

import logging
from datetime import datetime
from typing import Any, Literal, cast

from pydantic import BaseModel

from app.domain.zendesk import (
    TicketChannel,
    TicketPriority,
    TicketStatus,
    ZendeskComment,
    ZendeskTicket,
)
from app.integrations.zendesk.client import ZendeskClient
from app.integrations.zendesk.exceptions import ZendeskResponseError

logger = logging.getLogger(__name__)


class ZendeskSearchResult(BaseModel):
    """Container for paginated search results from Zendesk."""

    tickets: list[ZendeskTicket]
    count: int
    page: int = 1
    page_size: int = 100
    has_more: bool = False


class ZendeskAdapter:
    """Read-only application adapter connecting Pocket services to Zendesk API."""

    def __init__(self, client: ZendeskClient) -> None:
        self.client = client

    async def search_tickets(
        self,
        query: str,
        page: int = 1,
        page_size: int = 100,
    ) -> ZendeskSearchResult:
        """Search tickets by keyword or filter query, returning typed domain entities."""
        params = {
            "query": query,
            "page": page,
            "per_page": page_size,
        }
        data = await self.client.get("api/v2/search.json", params=params)

        results = data.get("results", [])
        count = data.get("count", len(results))

        tickets: list[ZendeskTicket] = []
        for item in results:
            # Upstream and search can return ticket results
            if item.get("result_type") == "ticket" or "subject" in item:
                tickets.append(self._parse_ticket(item))

        has_more = (page * page_size) < count
        return ZendeskSearchResult(
            tickets=tickets,
            count=count,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    async def get_ticket(self, ticket_id: int) -> ZendeskTicket:
        """Retrieve a single customer support ticket by ID."""
        data = await self.client.get(f"api/v2/tickets/{ticket_id}.json")
        ticket_raw = data.get("ticket")
        if not ticket_raw:
            raise ZendeskResponseError(
                f"Zendesk response did not contain 'ticket' key for ID {ticket_id}"
            )

        # Also retrieve comments if not embedded
        comments = await self.get_ticket_comments(ticket_id)
        return self._parse_ticket(ticket_raw, comments=comments)

    async def get_ticket_comments(self, ticket_id: int) -> list[ZendeskComment]:
        """Retrieve conversation comments on a support ticket."""
        data = await self.client.get(f"api/v2/tickets/{ticket_id}/comments.json")
        raw_comments = data.get("comments", [])

        comments: list[ZendeskComment] = []
        for c in raw_comments:
            comments.append(self._parse_comment(c, ticket_id=ticket_id))
        return comments

    def _parse_ticket(
        self,
        raw: dict[str, Any],
        comments: list[ZendeskComment] | None = None,
    ) -> ZendeskTicket:
        """Parse raw Zendesk JSON object into ZendeskTicket domain entity."""
        try:
            # Map raw fields with safe defaults
            raw_status = str(raw.get("status", "open")).lower()
            status: TicketStatus = (
                cast(TicketStatus, raw_status)
                if raw_status in ("new", "open", "pending", "solved", "closed")
                else "open"
            )

            raw_priority = str(raw.get("priority", "normal")).lower()
            priority: TicketPriority = (
                cast(TicketPriority, raw_priority)
                if raw_priority in ("low", "normal", "high", "urgent")
                else "normal"
            )

            raw_channel = str(raw.get("channel", "web")).lower()
            channel: TicketChannel = (
                cast(TicketChannel, raw_channel)
                if raw_channel in ("email", "web", "chat")
                else "web"
            )

            # Standardize requester_id to usr_ format if integer
            req_id = raw.get("requester_id")
            if isinstance(req_id, int):
                requester_str = f"usr_{req_id:06d}"
            elif isinstance(req_id, str) and req_id.startswith("usr_"):
                requester_str = req_id
            else:
                requester_str = "usr_000001"

            created_at = self._parse_iso_datetime(raw.get("created_at"))
            updated_at = self._parse_iso_datetime(raw.get("updated_at")) or created_at

            return ZendeskTicket(
                id=int(raw["id"]),
                requester_id=requester_str,
                subject=str(raw.get("subject", "")),
                description=str(raw.get("description", "")),
                status=status,
                priority=priority,
                channel=channel,
                tags=raw.get("tags", []),
                created_at=created_at,
                updated_at=updated_at,
                comments=comments or [],
            )
        except Exception as exc:
            logger.error("Failed to parse ZendeskTicket: %s", exc)
            raise ZendeskResponseError(f"Failed to parse ticket payload: {exc}") from exc

    def _parse_comment(
        self,
        raw: dict[str, Any],
        ticket_id: int,
        requester_id: str | None = None,
    ) -> ZendeskComment:
        """Parse raw comment JSON into ZendeskComment domain entity with authoritative author_role."""
        try:
            author_id = raw.get("author_id")
            if isinstance(author_id, int):
                author_str = f"usr_{author_id:06d}"
            elif isinstance(author_id, str):
                author_str = author_id
            else:
                author_str = "usr_000001"

            is_public = bool(raw.get("public", True))

            # Determine author_role authoritatively:
            # 1. If explicit in raw payload (e.g. from seed or mock), use it
            # 2. If public is False, strictly an internal staff note ("agent")
            # 3. If requester_id provided, customer if author matches requester, else staff ("agent")
            # 4. Default: "customer" if public else "agent"
            raw_role = raw.get("author_role")
            if raw_role in ("customer", "agent"):
                author_role: Literal["customer", "agent"] = raw_role
            elif not is_public:
                author_role = "agent"
            elif requester_id is not None:
                author_role = "customer" if author_str == requester_id else "agent"
            else:
                author_role = "customer"

            return ZendeskComment(
                id=int(raw.get("id", 1)),
                ticket_id=ticket_id,
                author_id=author_str,
                body=str(raw.get("body", "")),
                created_at=self._parse_iso_datetime(raw.get("created_at")),
                public=is_public,
                author_role=author_role,
            )
        except Exception as exc:
            logger.error("Failed to parse ZendeskComment: %s", exc)
            raise ZendeskResponseError(f"Failed to parse comment payload: {exc}") from exc

    @staticmethod
    def _parse_iso_datetime(dt_val: Any) -> datetime:
        """Parse ISO timestamp or return current datetime as fallback."""
        if isinstance(dt_val, datetime):
            return dt_val
        if isinstance(dt_val, str):
            try:
                return datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
            except ValueError:
                pass
        from datetime import UTC

        return datetime.now(UTC)
