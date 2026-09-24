"""Test fixtures for MockServer 7.6.0 Jira test double."""

import time
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from mocks.jira.expectations import get_jira_mock_expectations
from mocks.jira.mockserver_controller import MockServerController

MOCKSERVER_URL = "http://localhost:1080"


@pytest_asyncio.fixture(scope="function")
async def mock_jira_server() -> AsyncGenerator[str, None]:
    """Provide clean MockServer 7.6.0 Jira test double with loaded expectations.

    Ensures readiness via GET /mockserver/ready, clears state via PUT /mockserver/reset,
    and loads scenario expectations (PAY-117, CORE-82, PAY-134, etc.).
    """
    controller = MockServerController(base_url=MOCKSERVER_URL, timeout_seconds=5.0)

    # 1. Verify readiness
    is_ready = False
    for _ in range(10):
        if await controller.is_ready():
            is_ready = True
            break
        time.sleep(0.5)

    if not is_ready:
        pytest.skip(
            f"MockServer 7.6.0 is not running or not ready at {MOCKSERVER_URL}. "
            "Start with `docker compose -f mocks/jira/docker-compose.yml up -d`."
        )

    # 2. Reset expectations
    await controller.reset()

    # 3. Load deterministic scenario expectations
    expectations = get_jira_mock_expectations()
    await controller.load_expectations(expectations)

    yield MOCKSERVER_URL

    # 4. Clean up after test
    await controller.reset()
