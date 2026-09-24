"""Base domain tool contracts and standardized result envelopes."""

import logging
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, Literal, Self, TypeVar

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

T = TypeVar("T")

AgentRole = Literal["research", "analytics", "engineering", "pm", "critic"]


class ToolProvenance(BaseModel):
    """Provenance metadata attributing retrieved evidence."""

    source_type: Literal["zendesk", "posthog", "jira"]
    source_reference: (
        str  # e.g., "ticket_id:101", "query:event_count:transfer_completed", "issue_key:PAY-117"
    )
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolError(BaseModel):
    """Structured error definition for failed tool invocations."""

    error_type: Literal[
        "not_found",
        "timeout",
        "authentication_error",
        "rate_limit",
        "invalid_input",
        "permission_denied",
        "upstream_error",
    ]
    message: str
    attempted_source: Literal["zendesk", "posthog", "jira"] | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel, Generic[T]):
    """Standardized envelope for all domain tool executions."""

    success: bool
    data: T | None = None
    error: ToolError | None = None
    provenance: ToolProvenance | None = None
    execution_duration_ms: float

    @model_validator(mode="after")
    def validate_structural_invariants(self) -> Self:
        """Enforce strict structural invariants for success vs failure outcomes."""
        if self.success:
            if self.data is None:
                raise ValueError("Successful ToolResult must have 'data' populated.")
            if self.error is not None:
                raise ValueError("Successful ToolResult cannot have 'error' populated.")
            if self.provenance is None:
                raise ValueError("Successful ToolResult must have 'provenance' populated.")
        else:
            if self.data is not None:
                raise ValueError("Failed ToolResult cannot have 'data' populated.")
            if self.error is None:
                raise ValueError("Failed ToolResult must have 'error' populated.")
            if self.provenance is not None:
                raise ValueError("Failed ToolResult cannot claim evidence 'provenance'.")
        return self


class ToolPermissionError(Exception):
    """Raised when an agent role attempts to access or execute an unauthorized tool."""


class BaseTool(ABC):
    """Abstract base class for all Pocket domain tools."""

    name: str
    description: str

    @abstractmethod
    async def _execute(self, input_data: Any) -> tuple[Any, str]:
        """Execute the tool operation and return (data, source_reference).

        Raises relevant exceptions on failure.
        """

    @abstractmethod
    def _map_error(self, exc: Exception) -> ToolError:
        """Map underlying adapter or validation exception to a structured ToolError."""

    async def run(self, input_data: BaseModel) -> ToolResult[Any]:
        """Execute the tool operation with duration tracking and error normalization."""
        from app.integrations.observability.tracer import get_current_tracer

        tracer = get_current_tracer()
        span = None
        if tracer and tracer.enabled:
            input_dict = (
                input_data.model_dump()
                if hasattr(input_data, "model_dump")
                else {"input": str(input_data)}
            )
            span = tracer.start_span(name=f"tool:{self.name}", run_type="tool", inputs=input_dict)

        t_start = time.perf_counter()
        try:
            data, source_ref = await self._execute(input_data)
            duration_ms = (time.perf_counter() - t_start) * 1000
            source_type = self._get_source_type()
            if tracer and span:
                tracer.end_span(
                    span,
                    outputs={
                        "success": True,
                        "source_type": source_type,
                        "source_reference": source_ref,
                        "duration_ms": duration_ms,
                    },
                )
            return ToolResult(
                success=True,
                data=data,
                error=None,
                provenance=ToolProvenance(
                    source_type=source_type,
                    source_reference=source_ref,
                ),
                execution_duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - t_start) * 1000
            error = self._map_error(e)
            logger.warning(
                "Tool '%s' failed with %s: %s",
                self.name,
                error.error_type,
                error.message,
            )
            if tracer and span:
                tracer.end_span(
                    span,
                    outputs={
                        "success": False,
                        "error_type": error.error_type,
                        "message": error.message,
                    },
                    error=error.message,
                )
            return ToolResult(
                success=False,
                data=None,
                error=error,
                provenance=None,
                execution_duration_ms=duration_ms,
            )

    @abstractmethod
    def _get_source_type(self) -> Literal["zendesk", "posthog", "jira"]:
        """Return the source system for this domain tool."""
