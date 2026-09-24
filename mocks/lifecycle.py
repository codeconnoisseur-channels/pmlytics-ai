"""Lifecycle helper for the local Zendesk mock.

Jira is intentionally not started here: the approved Jira test double is the
pinned MockServer container, managed through ``mocks/jira/docker-compose.yml``.
"""

import logging
import socket
from copy import deepcopy
from urllib.parse import urlparse

from app.config.settings import get_settings
from seed.zendesk.minimal_loader import get_demo_tickets_payload

from mocks.zendesk.server import MockZendeskServer
from mocks.zendesk.upstream.mock_zendesk.handler import COMMENTS_STORE, TICKETS_STORE

logger = logging.getLogger(__name__)

_zendesk_server: MockZendeskServer | None = None


def is_port_in_use(host: str, port: int) -> bool:
    """Check if a port is actively open and accepting TCP connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def seed_zendesk_in_memory() -> None:
    """Ensure in-memory TICKETS_STORE and COMMENTS_STORE contain default scenario tickets."""
    if not TICKETS_STORE:
        payloads = get_demo_tickets_payload()
        for idx, item in enumerate(payloads, start=1):
            ticket_id = item.get("id") or idx
            ticket = deepcopy(item)
            ticket["id"] = ticket_id
            comment = ticket.pop("comment", None)
            TICKETS_STORE[ticket_id] = ticket

            if comment:
                comment_record = {
                    "id": idx * 100,
                    "body": comment.get("body", ""),
                    "author_id": comment.get("author_id", 1000 + idx),
                    "public": True,
                    "created_at": ticket.get("created_at", "2026-08-10T10:00:00Z"),
                }
                COMMENTS_STORE[ticket_id] = [comment_record]
        logger.info("Seeded %d scenario tickets into Zendesk in-memory store.", len(TICKETS_STORE))


def ensure_mock_services_running() -> None:
    """Ensure the pinned Zendesk mock is available for local development."""
    global _zendesk_server

    # Always ensure in-memory stores are populated
    seed_zendesk_in_memory()

    # 1. Zendesk Mock. Read the host and port from the configured adapter
    # endpoint; never silently bind a second hard-coded service.
    configured_url = urlparse(get_settings().zendesk_base_url)
    host = configured_url.hostname or "127.0.0.1"
    port = configured_url.port or 80
    if not is_port_in_use(host, port):
        try:
            logger.info("Starting native Python Mock Zendesk server on %s:%s...", host, port)
            _zendesk_server = MockZendeskServer(host=host, port=port)
            _zendesk_server.start()
            logger.info("Mock Zendesk server started successfully on port 8080.")
        except Exception as exc:
            logger.warning("Could not start Mock Zendesk server on port %s: %s", port, exc)
    else:
        logger.info("Mock Zendesk server port %s is already in use.", port)


def stop_mock_services() -> None:
    """Terminate background mock servers if started by this process."""
    global _zendesk_server
    if _zendesk_server:
        _zendesk_server.stop()
        _zendesk_server = None
