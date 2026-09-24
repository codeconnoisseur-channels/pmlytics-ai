"""Typed exceptions for Jira integration."""


class JiraError(Exception):
    """Base exception for all Jira integration failures."""


class JiraConnectionError(JiraError):
    """Raised when connecting to Jira / MockServer fails or service is unreachable."""


class JiraTimeoutError(JiraError):
    """Raised when an HTTP request to Jira exceeds the configured timeout."""


class JiraAuthError(JiraError):
    """Raised when Jira rejects credentials (HTTP 401/403)."""


class JiraNotFoundError(JiraError):
    """Raised when a requested issue, comment, or link does not exist (HTTP 404)."""


class JiraHttpError(JiraError):
    """Raised when Jira responds with an unhandled HTTP status code."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Jira HTTP {status_code}: {message}")


class JiraResponseError(JiraError):
    """Raised when Jira returns a malformed response or domain validation fails."""
