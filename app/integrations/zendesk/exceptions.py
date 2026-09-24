"""Typed exceptions for Zendesk integration."""


class ZendeskError(Exception):
    """Base exception for all Zendesk integration errors."""


class ZendeskConnectionError(ZendeskError):
    """Raised when connecting to Zendesk fails (e.g. connection refused, network unreachable)."""


class ZendeskTimeoutError(ZendeskError):
    """Raised when an HTTP request to Zendesk exceeds the configured timeout."""


class ZendeskAuthError(ZendeskError):
    """Raised when Zendesk rejects credentials (HTTP 401 Unauthorized)."""


class ZendeskNotFoundError(ZendeskError):
    """Raised when a requested ticket or resource does not exist (HTTP 404 Not Found)."""


class ZendeskHttpError(ZendeskError):
    """Raised when Zendesk responds with an unexpected HTTP status code."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Zendesk HTTP {status_code}: {message}")


class ZendeskResponseError(ZendeskError):
    """Raised when Zendesk returns a malformed response or domain schema validation fails."""
