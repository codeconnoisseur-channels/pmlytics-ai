"""Exception hierarchy for PostHog integration."""


class PostHogError(Exception):
    """Base exception for all PostHog integration errors."""


class PostHogAuthenticationError(PostHogError):
    """Raised when authentication fails (HTTP 401 or 403)."""


class PostHogNotFoundError(PostHogError):
    """Raised when a project or endpoint is not found (HTTP 404)."""


class PostHogRateLimitError(PostHogError):
    """Raised when PostHog rate limit is exceeded (HTTP 429)."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class PostHogQueryError(PostHogError):
    """Raised when a HogQL query fails syntax or execution validation."""


class PostHogConnectionError(PostHogError):
    """Raised when network connection to PostHog fails."""


class PostHogTimeoutError(PostHogError):
    """Raised when a query request to PostHog times out."""
