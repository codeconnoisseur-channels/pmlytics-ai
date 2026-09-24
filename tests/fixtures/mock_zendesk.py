"""Test fixtures for Mock Zendesk server."""

import socket
import time
from collections.abc import Generator

import pytest
from mocks.zendesk.compat_handler import reset_mock_stores
from mocks.zendesk.server import MockZendeskServer


def find_free_port() -> int:
    """Find an available ephemeral TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope="module")
def mock_zendesk_server() -> Generator[str, None, None]:
    """Launch native Mock Zendesk server on an ephemeral port, returning its base URL."""
    reset_mock_stores()
    port = find_free_port()
    server = MockZendeskServer(host="127.0.0.1", port=port)
    server.start()

    # Allow server thread to bind
    time.sleep(0.1)
    base_url = f"http://127.0.0.1:{port}"

    try:
        yield base_url
    finally:
        server.stop()
        reset_mock_stores()
