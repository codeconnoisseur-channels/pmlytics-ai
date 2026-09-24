"""Deterministic PostHog synthetic dataset loader.

Generates the approved synthetic dataset (SEED=20260914, DATASET_VERSION=1.0)
and uploads it in batches into the designated PostHog project.
"""

import asyncio
import logging
import time
from typing import Any

from app.config.settings import Settings, get_settings

from seed.posthog.generator import DEFAULT_SEED, PostHogEventGenerator
from seed.posthog.uploader import PostHogUploader

logger = logging.getLogger(__name__)


async def load_synthetic_analytics_dataset(
    settings: Settings | None = None,
    batch_size: int = 500,
) -> dict[str, Any]:
    """Generate and upload the deterministic synthetic dataset to PostHog.

    Returns:
        Execution summary dictionary with event counts, batch counts, and timings.
    """
    cfg = settings or get_settings()
    start_time = time.perf_counter()

    # 1. Generate events
    logger.info("Generating deterministic synthetic events (SEED=%s)...", DEFAULT_SEED)
    generator = PostHogEventGenerator(seed=DEFAULT_SEED, num_users=2000)
    events = generator.generate_events()
    total_events = len(events)
    logger.info("Generated %d events across all scenarios.", total_events)

    # 2. Upload events
    uploader = PostHogUploader(settings=cfg, batch_size=batch_size)
    upload_result = await uploader.upload_events(events)

    elapsed = time.perf_counter() - start_time
    summary = {
        "status": upload_result.get("status", "success"),
        "total_events": total_events,
        "batches_sent": upload_result.get("batches_sent", 0),
        "host": cfg.posthog_host,
        "project_id": cfg.posthog_project_id,
        "elapsed_seconds": round(elapsed, 2),
    }
    logger.info("Completed PostHog seed run in %.2fs: %s", elapsed, summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = asyncio.run(load_synthetic_analytics_dataset())
    print("\n--- Ingestion Result ---")
    for k, v in result.items():
        print(f"{k}: {v}")
