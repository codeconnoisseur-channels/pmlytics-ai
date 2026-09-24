"""Unit tests for PostHogClient using respx for offline HTTP mocking."""

import httpx
import pytest
import respx
from app.integrations.posthog.client import PostHogClient
from app.integrations.posthog.exceptions import (
    PostHogAuthenticationError,
    PostHogConnectionError,
    PostHogNotFoundError,
    PostHogQueryError,
    PostHogRateLimitError,
    PostHogTimeoutError,
)

HOST = "https://us.posthog.com"
PROJECT_ID = "12345"
API_KEY = "phx_test_key_secret"
QUERY_URL = f"{HOST}/api/projects/{PROJECT_ID}/query/"


@pytest.fixture
def posthog_client() -> PostHogClient:
    return PostHogClient(
        host=HOST,
        project_id=PROJECT_ID,
        api_key=API_KEY,
        timeout_seconds=2.0,
        max_retries=2,
    )


@pytest.mark.asyncio
async def test_client_execute_query_success(posthog_client: PostHogClient) -> None:
    expected_response = {
        "columns": ["event", "count()"],
        "types": ["String", "UInt64"],
        "results": [["transfer_completed", 4500]],
    }
    with respx.mock:
        route = respx.post(QUERY_URL).respond(200, json=expected_response)
        result = await posthog_client.execute_query(
            "SELECT event, count() FROM events GROUP BY event"
        )

        assert route.called
        assert route.calls.last.request.headers["Authorization"] == f"Bearer {API_KEY}"
        req_json = route.calls.last.request.read().decode()
        assert "HogQLQuery" in req_json
        assert result == expected_response


@pytest.mark.asyncio
async def test_client_auth_failure(posthog_client: PostHogClient) -> None:
    with respx.mock:
        respx.post(QUERY_URL).respond(401, text="Unauthorized token")
        with pytest.raises(PostHogAuthenticationError) as exc_info:
            await posthog_client.execute_query("SELECT 1")
        assert "401" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_not_found(posthog_client: PostHogClient) -> None:
    with respx.mock:
        respx.post(QUERY_URL).respond(404, text="Project not found")
        with pytest.raises(PostHogNotFoundError) as exc_info:
            await posthog_client.execute_query("SELECT 1")
        assert "404" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_query_syntax_error(posthog_client: PostHogClient) -> None:
    with respx.mock:
        respx.post(QUERY_URL).respond(400, text="HogQL Syntax Error near FOOBAR")
        with pytest.raises(PostHogQueryError) as exc_info:
            await posthog_client.execute_query("SELECT FOOBAR")
        assert "400" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_rate_limit_retry_and_succeed(posthog_client: PostHogClient) -> None:
    expected_response = {"columns": ["count()"], "results": [[10]]}
    with respx.mock:
        r1 = respx.post(QUERY_URL).respond(429, headers={"Retry-After": "0.01"})
        r2 = respx.post(QUERY_URL).respond(200, json=expected_response)
        result = await posthog_client.execute_query("SELECT count() FROM events")

        assert result == expected_response
        assert r1.called
        assert r2.called


@pytest.mark.asyncio
async def test_client_rate_limit_exhausted(posthog_client: PostHogClient) -> None:
    with respx.mock:
        respx.post(QUERY_URL).respond(429, headers={"Retry-After": "0.01"})
        with pytest.raises(PostHogRateLimitError) as exc_info:
            await posthog_client.execute_query("SELECT 1")
        assert "429" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_timeout_handling(posthog_client: PostHogClient) -> None:
    with respx.mock:
        respx.post(QUERY_URL).mock(side_effect=httpx.ReadTimeout("Timeout reading from socket"))
        with pytest.raises(PostHogTimeoutError) as exc_info:
            await posthog_client.execute_query("SELECT 1")
        assert "timed out" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_connection_error(posthog_client: PostHogClient) -> None:
    with respx.mock:
        respx.post(QUERY_URL).mock(side_effect=httpx.ConnectError("Connection refused"))
        with pytest.raises(PostHogConnectionError) as exc_info:
            await posthog_client.execute_query("SELECT 1")
        assert "connection error" in str(exc_info.value)


def test_client_credential_redaction(posthog_client: PostHogClient) -> None:
    rep = repr(posthog_client)
    assert API_KEY not in rep
    assert "api_key='***'" in rep
