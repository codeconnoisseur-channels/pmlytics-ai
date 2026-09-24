"""MockServer 7.6.0 REST control API client and lifecycle manager.

Communicates with MockServer running in Docker/subprocess using official control endpoints:
- GET /mockserver/ready: Deterministic readiness verification
- PUT /mockserver/reset: Reset state and clear all expectations
- PUT /mockserver/expectation: Register request matchers and mock responses
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MockServerController:
    """Controls MockServer 7.6.0 instance via its official HTTP REST control API."""

    def __init__(
        self, base_url: str = "http://localhost:1080", timeout_seconds: float = 5.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def is_ready(self) -> bool:
        """Verify MockServer is up and accepting traffic using GET /mockserver/ready."""
        url = f"{self.base_url}/mockserver/ready"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(url)
                return bool(resp.status_code == 200)
        except Exception as exc:
            logger.debug("MockServer readiness probe failed: %s", exc)
            return False

    async def reset(self) -> bool:
        """Clear all active expectations and request logs via PUT /mockserver/reset."""
        url = f"{self.base_url}/mockserver/reset"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.put(url)
                return bool(resp.status_code == 200)
        except Exception as exc:
            logger.error("Failed to reset MockServer: %s", exc)
            return False

    async def load_expectation(self, expectation: dict[str, Any]) -> bool:
        """Register a single expectation in MockServer via PUT /mockserver/expectation."""
        url = f"{self.base_url}/mockserver/expectation"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.put(url, json=expectation)
                return bool(resp.status_code in (200, 201))
        except Exception as exc:
            logger.error("Failed to load expectation into MockServer: %s", exc)
            return False

    async def load_expectations(self, expectations: list[dict[str, Any]]) -> int:
        """Load multiple expectations into MockServer sequentially. Returns count of loaded."""
        loaded = 0
        for exp in expectations:
            if await self.load_expectation(exp):
                loaded += 1
        return loaded
