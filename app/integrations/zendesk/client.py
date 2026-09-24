"""Low-level HTTP transport client for Zendesk API.

Handles HTTP basic authentication, timeout enforcement, request dispatch,
and conversion of transport-level errors into typed Zendesk exceptions.
Credentials and Authorization headers are strictly sanitized from logs.
"""

import base64
import logging
from typing import Any

import httpx

from app.integrations.zendesk.exceptions import (
    ZendeskAuthError,
    ZendeskConnectionError,
    ZendeskHttpError,
    ZendeskNotFoundError,
    ZendeskResponseError,
    ZendeskTimeoutError,
)

logger = logging.getLogger(__name__)


class ZendeskClient:
    """HTTP transport client for interacting with Zendesk REST API."""

    def __init__(
        self,
        base_url: str,
        username: str,
        api_key: str,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.timeout_seconds = timeout_seconds

        # Zendesk API Token authentication format: {username}/token:{api_key}
        auth_bytes = f"{username}/token:{api_key}".encode()
        self._auth_header = f"Basic {base64.b64encode(auth_bytes).decode()}"

    def _get_headers(self) -> dict[str, str]:
        """Generate request headers without leaking secrets to callers."""
        return {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an authenticated GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        safe_endpoint = endpoint.split("?")[0]
        logger.debug("Dispatching GET request to Zendesk endpoint: %s", safe_endpoint)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                )
        except httpx.TimeoutException as exc:
            logger.warning("Zendesk request timed out on %s", safe_endpoint)
            raise ZendeskTimeoutError(
                f"Request to {safe_endpoint} timed out after {self.timeout_seconds}s"
            ) from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("Failed to connect to Zendesk on %s", safe_endpoint)
            raise ZendeskConnectionError(
                f"Connection to Zendesk service failed at {self.base_url}"
            ) from exc

        return self._handle_response(response, safe_endpoint)

    async def post(self, endpoint: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Perform an authenticated POST request (used primarily for seeding/testing)."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        safe_endpoint = endpoint.split("?")[0]
        logger.debug("Dispatching POST request to Zendesk endpoint: %s", safe_endpoint)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=json_data,
                )
        except httpx.TimeoutException as exc:
            logger.warning("Zendesk POST request timed out on %s", safe_endpoint)
            raise ZendeskTimeoutError(
                f"Request to {safe_endpoint} timed out after {self.timeout_seconds}s"
            ) from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error("Failed to connect to Zendesk on %s", safe_endpoint)
            raise ZendeskConnectionError(
                f"Connection to Zendesk service failed at {self.base_url}"
            ) from exc

        return self._handle_response(response, safe_endpoint)

    def _handle_response(self, response: httpx.Response, endpoint: str) -> dict[str, Any]:
        """Inspect status code and deserialize JSON response."""
        status = response.status_code

        if status == 401:
            logger.warning("Zendesk authentication rejected (HTTP 401) on %s", endpoint)
            raise ZendeskAuthError(f"Authentication failed for Zendesk username: {self.username}")

        if status == 404:
            logger.info("Zendesk resource not found (HTTP 404) on %s", endpoint)
            raise ZendeskNotFoundError(f"Zendesk resource not found at {endpoint}")

        if status not in (200, 201, 204):
            logger.warning("Zendesk returned HTTP %d on %s", status, endpoint)
            raise ZendeskHttpError(status, response.text)

        if status == 204 or not response.content:
            return {}

        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception as exc:
            logger.error("Failed to decode JSON payload from Zendesk response on %s", endpoint)
            raise ZendeskResponseError(
                f"Malformed JSON response from Zendesk: {response.text[:200]}"
            ) from exc
