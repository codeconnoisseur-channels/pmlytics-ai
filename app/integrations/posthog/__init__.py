"""PostHog integration package.

Provides read-only query client and adapter for product analytics.
"""

from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.client import PostHogClient
from app.integrations.posthog.exceptions import (
    PostHogAuthenticationError,
    PostHogConnectionError,
    PostHogError,
    PostHogNotFoundError,
    PostHogQueryError,
    PostHogRateLimitError,
    PostHogTimeoutError,
)

__all__ = [
    "PostHogAdapter",
    "PostHogAuthenticationError",
    "PostHogClient",
    "PostHogConnectionError",
    "PostHogError",
    "PostHogNotFoundError",
    "PostHogQueryError",
    "PostHogRateLimitError",
    "PostHogTimeoutError",
]
