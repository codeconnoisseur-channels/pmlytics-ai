"""Low-level HTTP transport client for Jira Cloud REST API v3.

Handles HTTP Basic Authentication using Base64-encoded username:password,
timeout enforcement, request dispatch, and error mapping.
Credentials and Authorization headers are strictly redacted from logs.
"""

import base64
import logging
from typing import Any

import httpx

from app.integrations.jira.exceptions import (
    JiraAuthError,
    JiraConnectionError,
    JiraHttpError,
    JiraNotFoundError,
    JiraResponseError,
    JiraTimeoutError,
)

logger = logging.getLogger(__name__)


class JiraClient:
    """HTTP transport client for Jira REST API v3."""

    def __init__(
        self,
        base_url: str,
        username: str,
        api_token: str,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.timeout_seconds = timeout_seconds

        # Jira Cloud HTTP Basic Authentication format: Base64(username:password)
        auth_bytes = f"{username}:{api_token}".encode()
        self._auth_header = f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"

    def _get_headers(self) -> dict[str, str]:
        """Generate request headers without leaking secrets."""
        return {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an authenticated GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        safe_endpoint = endpoint.split("?")[0]
        logger.debug("Dispatching GET to Jira endpoint: %s", safe_endpoint)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                )
        except httpx.TimeoutException as exc:
            logger.warning("Jira request timed out on %s", safe_endpoint)
            raise JiraTimeoutError(
                f"Request to {safe_endpoint} timed out after {self.timeout_seconds}s"
            ) from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("Failed to connect to Jira on %s", safe_endpoint)
            raise JiraConnectionError(f"Connection to Jira failed at {self.base_url}") from exc

        return self._handle_response(response, safe_endpoint)

    async def post(self, endpoint: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Perform an authenticated POST request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        safe_endpoint = endpoint.split("?")[0]
        logger.debug("Dispatching POST to Jira endpoint: %s", safe_endpoint)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=json_data,
                )
        except httpx.TimeoutException as exc:
            logger.warning("Jira POST request timed out on %s", safe_endpoint)
            raise JiraTimeoutError(
                f"Request to {safe_endpoint} timed out after {self.timeout_seconds}s"
            ) from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("Failed to connect to Jira on %s", safe_endpoint)
            raise JiraConnectionError(f"Connection to Jira failed at {self.base_url}") from exc

        return self._handle_response(response, safe_endpoint)

    def _handle_response(self, response: httpx.Response, endpoint: str) -> dict[str, Any]:
        """Check status codes and return deserialized JSON."""
        status = response.status_code

        if status in (401, 403):
            logger.warning("Jira authentication rejected (HTTP %d) on %s", status, endpoint)
            raise JiraAuthError(f"Authentication failed for Jira user: {self.username}")

        if status == 404:
            logger.info("Jira resource not found (HTTP 404) on %s", endpoint)
            raise JiraNotFoundError(f"Jira resource not found at {endpoint}")

        if status not in (200, 201, 204):
            logger.warning("Jira returned HTTP %d on %s", status, endpoint)
            raise JiraHttpError(status, response.text)

        if status == 204 or not response.content:
            return {}

        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception as exc:
            logger.error("Failed to parse JSON response from Jira on %s", endpoint)
            raise JiraResponseError(
                f"Malformed JSON response from Jira: {response.text[:200]}"
            ) from exc
