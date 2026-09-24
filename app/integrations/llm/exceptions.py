"""Exceptions for LLM integration layer."""


class LLMError(Exception):
    """Base exception for LLM operations."""


class LLMAuthError(LLMError):
    """Authentication or API key failure."""


class LLMTimeoutError(LLMError):
    """Request timeout from model provider."""


class LLMRateLimitError(LLMError):
    """Rate limit encountered with model provider."""


class LLMMalformedOutputError(LLMError):
    """Model output could not be parsed into expected schema."""


class LLMBudgetExceededError(LLMError):
    """Execution budget exceeded (tool calls or LLM invocations)."""
