"""Low-level async client for the PostHog Query API."""

import asyncio
import logging
from typing import Any

import httpx

from app.integrations.posthog.exceptions import (
    PostHogAuthenticationError,
    PostHogConnectionError,
    PostHogError,
    PostHogNotFoundError,
    PostHogQueryError,
    PostHogRateLimitError,
    PostHogTimeoutError,
)

logger = logging.getLogger(__name__)


class PostHogClient:
    """Async client communicating exclusively with PostHog's Query API.

    Enforces strict read-only runtime semantics. Zero ingestion/write endpoints
    are implemented here.
    """

    def __init__(
        self,
        host: str,
        project_id: str,
        api_key: str,
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.host = host.rstrip("/")
        self.project_id = project_id
        self._api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._client = client

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout_seconds)
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "PostHogClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        return (
            f"PostHogClient(host={self.host!r}, project_id={self.project_id!r}, "
            f"api_key='***', timeout_seconds={self.timeout_seconds})"
        )

    async def execute_query(self, query: str) -> dict[str, Any]:
        """Execute a HogQL query against POST /api/projects/:id/query/.

        Args:
            query: The HogQL query string.

        Returns:
            The raw JSON response from PostHog containing results, columns, and types.

        Raises:
            PostHogAuthenticationError: On 401 or 403 responses.
            PostHogNotFoundError: On 404 response.
            PostHogRateLimitError: On 429 response exceeding retry budget.
            PostHogQueryError: On 400 bad query response.
            PostHogTimeoutError: When the HTTP call times out.
            PostHogConnectionError: When a network error occurs.
            PostHogError: On unexpected status codes.
        """
        client = self._get_client()
        url = f"{self.host}/api/projects/{self.project_id}/query/"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PMLytics-AI/0.1.0",
        }
        payload = {
            "query": {
                "kind": "HogQLQuery",
                "query": query,
                "explain": False,
            }
        }

        retries = 0
        backoff_delay = 0.5

        while True:
            try:
                logger.debug(
                    "Executing HogQL query against %s (project %s)", self.host, self.project_id
                )
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code in (200, 201):
                    return response.json()  # type: ignore[no-any-return]

                if response.status_code in (401, 403):
                    raise PostHogAuthenticationError(
                        f"PostHog authentication failed (HTTP {response.status_code}): {response.text}"
                    )

                if response.status_code == 404:
                    raise PostHogNotFoundError(
                        f"PostHog project {self.project_id} or query endpoint not found (HTTP 404)"
                    )

                if response.status_code == 400:
                    raise PostHogQueryError(
                        f"PostHog query validation error (HTTP 400): {response.text}"
                    )

                if response.status_code == 429:
                    retry_after_hdr = response.headers.get("Retry-After")
                    retry_after = float(retry_after_hdr) if retry_after_hdr else backoff_delay
                    if retries < self.max_retries:
                        retries += 1
                        logger.warning(
                            "PostHog rate limit exceeded (HTTP 429). Retrying in %.2fs (attempt %d/%d)",
                            retry_after,
                            retries,
                            self.max_retries,
                        )
                        await asyncio.sleep(retry_after)
                        backoff_delay *= 2
                        continue
                    raise PostHogRateLimitError(
                        f"PostHog rate limit exceeded (HTTP 429) after {self.max_retries} retries",
                        retry_after=retry_after,
                    )

                if response.status_code in (502, 503, 504):
                    if retries < self.max_retries:
                        retries += 1
                        logger.warning(
                            "Transient PostHog error HTTP %d. Retrying in %.2fs (attempt %d/%d)",
                            response.status_code,
                            backoff_delay,
                            retries,
                            self.max_retries,
                        )
                        await asyncio.sleep(backoff_delay)
                        backoff_delay *= 2
                        continue
                    raise PostHogError(
                        f"PostHog server error (HTTP {response.status_code}): {response.text}"
                    )

                raise PostHogError(
                    f"Unexpected PostHog HTTP response {response.status_code}: {response.text}"
                )

            except httpx.TimeoutException as exc:
                raise PostHogTimeoutError(f"PostHog query request timed out: {exc}") from exc
            except httpx.NetworkError as exc:
                raise PostHogConnectionError(f"PostHog connection error: {exc}") from exc
