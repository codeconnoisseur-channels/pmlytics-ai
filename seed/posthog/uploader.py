"""Batch uploader for populating a dedicated synthetic PostHog project."""

import asyncio
import logging
from typing import Any

import httpx
from app.config.settings import Settings, get_settings
from app.domain.analytics import AnalyticsEvent

logger = logging.getLogger(__name__)


class PostHogUploader:
    """Safely batches and uploads synthetic events into a designated PostHog project."""

    def __init__(
        self,
        host: str | None = None,
        project_token: str | None = None,
        settings: Settings | None = None,
        batch_size: int = 500,
        delay_between_batches: float = 0.15,
        max_retries: int = 3,
    ) -> None:
        cfg = settings or get_settings()
        self.host = (host or cfg.posthog_host).rstrip("/")
        self.project_token = project_token or cfg.posthog_project_token or cfg.posthog_api_key
        self.environment = cfg.environment
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.max_retries = max_retries

        self._validate_environment()

    def _validate_environment(self) -> None:
        """Enforce environment safety guard preventing accidental production writes."""
        if self.environment.lower() == "production":
            raise RuntimeError(
                "CRITICAL: Event uploading is strictly forbidden when environment is 'production'."
            )
        if not self.project_token:
            logger.warning(
                "PostHog project token is empty; upload will not succeed until configured."
            )

    async def upload_events(self, events: list[AnalyticsEvent]) -> dict[str, Any]:
        """Upload a list of AnalyticsEvent instances in chunked batches.

        Args:
            events: List of synthetic AnalyticsEvent objects.

        Returns:
            Dictionary summary with total_events, batches_sent, and status.
        """
        self._validate_environment()

        if not self.project_token:
            raise ValueError("Cannot upload events without a valid PostHog project token/api_key.")

        url = f"{self.host}/batch/"
        total_events = len(events)
        total_batches = (total_events + self.batch_size - 1) // self.batch_size
        logger.info(
            "Starting upload of %d synthetic events in %d batches to %s",
            total_events,
            total_batches,
            self.host,
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            for batch_idx in range(total_batches):
                chunk = events[batch_idx * self.batch_size : (batch_idx + 1) * self.batch_size]
                payload = {
                    "api_key": self.project_token,
                    "batch": [
                        {
                            "distinct_id": e.distinct_id,
                            "event": e.event,
                            "timestamp": e.timestamp.isoformat(),
                            "properties": e.properties,
                        }
                        for e in chunk
                    ],
                }

                retries = 0
                while True:
                    try:
                        response = await client.post(url, json=payload)
                        if response.status_code in (200, 201):
                            break
                        if response.status_code == 429 and retries < self.max_retries:
                            retries += 1
                            wait = 2.0 * retries
                            logger.warning("Rate limited (429). Retrying in %.1fs...", wait)
                            await asyncio.sleep(wait)
                            continue
                        response.raise_for_status()
                    except Exception as exc:
                        if retries < self.max_retries:
                            retries += 1
                            await asyncio.sleep(1.0 * retries)
                            continue
                        raise RuntimeError(
                            f"Failed to upload batch {batch_idx + 1}/{total_batches}: {exc}"
                        ) from exc

                logger.debug(
                    "Uploaded batch %d/%d (%d events)", batch_idx + 1, total_batches, len(chunk)
                )
                if batch_idx < total_batches - 1 and self.delay_between_batches > 0:
                    await asyncio.sleep(self.delay_between_batches)

        return {
            "status": "success",
            "total_events": total_events,
            "batches_sent": total_batches,
            "host": self.host,
        }
