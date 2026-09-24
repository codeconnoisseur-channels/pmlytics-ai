"""LLM integration module exposing client protocol and exceptions."""

from app.integrations.llm.client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    OpenRouterClient,
    ToolCallRequest,
)
from app.integrations.llm.exceptions import (
    LLMAuthError,
    LLMBudgetExceededError,
    LLMError,
    LLMMalformedOutputError,
    LLMRateLimitError,
    LLMTimeoutError,
)

__all__ = [
    "LLMAuthError",
    "LLMBudgetExceededError",
    "LLMClient",
    "LLMError",
    "LLMMalformedOutputError",
    "LLMMessage",
    "LLMRateLimitError",
    "LLMResponse",
    "LLMTimeoutError",
    "OpenRouterClient",
    "ToolCallRequest",
]
