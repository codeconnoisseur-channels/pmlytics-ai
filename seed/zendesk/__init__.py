"""Zendesk seeding package."""

from seed.zendesk.minimal_loader import (
    get_demo_tickets_payload,
    get_minimal_tickets_payload,
    load_minimal_tickets,
)

__all__ = ["get_demo_tickets_payload", "get_minimal_tickets_payload", "load_minimal_tickets"]
