"""LangSmith distributed tracing integration using verified RunTree APIs with strict fail-open resilience."""

import contextvars
import logging
import os
import re
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager, suppress
from typing import Any

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

SECRET_KEY_DENYLIST = {
    "api_key",
    "token",
    "authorization",
    "secret",
    "password",
    "bearer",
    "api-key",
    "openrouter_api_key",
    "langsmith_api_key",
    "posthog_api_key",
    "posthog_project_token",
    "jira_api_token",
    "zendesk_api_key",
}

SECRET_REGEX_PATTERNS = [
    re.compile(r"sk-or-v1-[a-f0-9]{32,}", re.IGNORECASE),
    re.compile(r"lsv2_pt_[a-zA-Z0-9_]{16,}", re.IGNORECASE),
    re.compile(r"phc_[a-zA-Z0-9_]{16,}", re.IGNORECASE),
    re.compile(r"phx_[a-zA-Z0-9_]{16,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{16,}", re.IGNORECASE),
]


TOKEN_COUNT_ALLOWLIST = {
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "max_tokens",
    "prompt_tokens",
    "completion_tokens",
    "cached_tokens",
    "reasoning_tokens",
    "audio_tokens",
    "tokens",
}


def sanitize_payload(data: Any, max_depth: int = 4) -> Any:
    """Recursively redact secrets and compact massive payloads for telemetry minimization."""
    if max_depth <= 0:
        return "[MAX_DEPTH_REACHED]"

    if isinstance(data, dict):
        sanitized: dict[str, Any] = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            is_token_count = k_lower in TOKEN_COUNT_ALLOWLIST or k_lower.endswith("_tokens")
            if not is_token_count and any(denied in k_lower for denied in SECRET_KEY_DENYLIST):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_payload(v, max_depth=max_depth - 1)
        return sanitized

    if isinstance(data, list):
        if len(data) > 15:
            # Compact oversized lists to minimize data transit while preserving IDs
            head = [sanitize_payload(x, max_depth=max_depth - 1) for x in data[:5]]
            return head + [f"... [{len(data) - 5} items summarized]"]
        return [sanitize_payload(x, max_depth=max_depth - 1) for x in data]

    if isinstance(data, str):
        sanitized_str = data
        for pattern in SECRET_REGEX_PATTERNS:
            sanitized_str = pattern.sub("[REDACTED]", sanitized_str)
        # Compact individual strings if extremely long (> 1000 chars)
        if len(sanitized_str) > 1000:
            return sanitized_str[:500] + "... [TRUNCATED_FOR_TELEMETRY]"
        return sanitized_str

    if hasattr(data, "model_dump"):
        try:
            return sanitize_payload(data.model_dump(), max_depth=max_depth)
        except Exception:
            return str(data)

    return data


class InvestigationTracer:
    """Manages hierarchical RunTree spans with strict fail-open guarantees.

    Invariants:
    1. Tracing failures never cause investigation failures, evidence mutations, extra retries, or altered outputs.
    2. Zero credentials or secret patterns leak into telemetry.
    3. Tracing overhead is minimal and non-blocking.
    """

    def __init__(
        self,
        investigation_id: str,
        enabled: bool | None = None,
        environment: str | None = None,
    ) -> None:
        self.investigation_id = investigation_id
        settings = get_settings()

        self.enabled = (
            enabled
            if enabled is not None
            else bool(settings.langsmith_tracing and settings.langsmith_api_key)
        )
        self.environment = environment or settings.environment
        self.root_run: Any = None
        self.trace_url: str | None = None
        self._listeners: list[Any] = []

        if self.enabled:
            self._init_root_trace()

    def add_listener(self, listener: Any) -> None:
        """Register a callback for lifecycle events: (event_type: str, name: str, payload: dict) -> None."""
        self._listeners.append(listener)

    def _notify_listeners(self, event_type: str, name: str, payload: dict[str, Any]) -> None:
        """Safely notify registered progress listeners in a fail-open manner."""
        for listener in self._listeners:
            try:
                listener(event_type, name, payload)
            except Exception as exc:
                logger.debug("Tracer listener error (fail-open): %s", exc)

    def _init_root_trace(self) -> None:
        """Initialize top-level RunTree span safely."""
        try:
            settings = get_settings()
            if settings.langsmith_api_key:
                os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
                os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
            if settings.langsmith_project:
                os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
                os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
            if settings.langsmith_endpoint:
                os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
                os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint

            from langsmith.run_trees import RunTree

            # Inputs to root are minimal metadata (data minimization)
            inputs = {
                "investigation_id": self.investigation_id,
                "environment": self.environment,
            }
            metadata = {
                "investigation_id": self.investigation_id,
                "environment": self.environment,
                "runtime": "langgraph_multi_agent",
            }
            self.root_run = RunTree(
                name="investigation_workflow",
                run_type="chain",
                inputs=inputs,
                extra={"metadata": metadata},
                tags=["pocket_investigation", self.environment],
            )
            self.root_run.post()
            if hasattr(self.root_run, "get_url"):
                with suppress(Exception):
                    self.trace_url = self.root_run.get_url()
        except Exception as exc:
            logger.warning(
                "LangSmith root trace initiation failed (fail-open mode active): %s", exc
            )
            self.root_run = None

    def start_span(
        self,
        name: str,
        run_type: str = "chain",
        inputs: dict[str, Any] | None = None,
        parent_span: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Create and post a child span under parent_span, active context span, or root_run."""
        self._notify_listeners(
            "start",
            name,
            {"run_type": run_type, "inputs": inputs, "metadata": metadata},
        )

        if not self.enabled or (
            self.root_run is None and parent_span is None and _current_span.get() is None
        ):
            return None

        effective_parent = parent_span or _current_span.get() or self.root_run
        if effective_parent is None:
            return None

        try:
            sanitized_inputs = sanitize_payload(inputs or {})
            span_meta = {"investigation_id": self.investigation_id}
            if metadata:
                span_meta.update(sanitize_payload(metadata))

            child_span = effective_parent.create_child(
                name=name,
                run_type=run_type,
                inputs=sanitized_inputs,
                extra={"metadata": span_meta},
            )
            child_span.post()
            return child_span
        except Exception as exc:
            logger.debug("Failed to start child span '%s' (fail-open): %s", name, exc)
            return None

    def end_span(
        self,
        span: Any,
        outputs: dict[str, Any] | None = None,
        error: str | None = None,
        usage_metadata: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Patch completion status, sanitized outputs, usage metadata, and metrics to a span."""
        span_name = getattr(span, "name", "span") if span is not None else "span"
        self._notify_listeners(
            "end",
            span_name,
            {
                "outputs": outputs,
                "error": error,
                "usage_metadata": usage_metadata,
                "metadata": metadata,
            },
        )

        if span is None:
            return

        try:
            sanitized_outputs = sanitize_payload(outputs or {})
            sanitized_meta = sanitize_payload(metadata or {})

            if usage_metadata:
                sanitized_outputs["usage_metadata"] = usage_metadata

            if hasattr(span, "set"):
                set_kwargs: dict[str, Any] = {}
                if usage_metadata:
                    set_kwargs["usage_metadata"] = usage_metadata
                if sanitized_meta:
                    set_kwargs["metadata"] = sanitized_meta
                if set_kwargs:
                    span.set(**set_kwargs)
            elif sanitized_meta:
                if hasattr(span, "extra") and isinstance(span.extra, dict):
                    span.extra.setdefault("metadata", {}).update(sanitized_meta)

            span.end(outputs=sanitized_outputs, error=error)
            span.patch()
        except Exception as exc:
            logger.warning(
                "Failed to patch span '%s' (fail-open): %s", getattr(span, "name", "unknown"), exc
            )

    def close(self, final_status: str = "completed", error: str | None = None) -> None:
        """Complete the root investigation trace."""
        self._notify_listeners(
            "close",
            "investigation_workflow",
            {"final_status": final_status, "error": error},
        )

        if self.root_run is not None:
            try:
                self.root_run.end(
                    outputs={"final_status": final_status},
                    error=error,
                )
                self.root_run.patch()
            except Exception as exc:
                logger.warning("Failed to close root trace (fail-open): %s", exc)


_current_tracer: contextvars.ContextVar[InvestigationTracer | None] = contextvars.ContextVar(
    "_current_tracer", default=None
)
_current_span: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "_current_span", default=None
)


def get_current_tracer() -> InvestigationTracer | None:
    """Retrieve active investigation tracer from context, if any."""
    return _current_tracer.get()


@contextmanager
def trace_investigation(tracer: InvestigationTracer) -> Iterator[InvestigationTracer]:
    """Context manager binding an investigation tracer to async execution context."""
    token = _current_tracer.set(tracer)
    try:
        yield tracer
    finally:
        _current_tracer.reset(token)


@contextmanager
def span_context(
    name: str,
    run_type: str = "chain",
    inputs: dict[str, Any] | None = None,
    parent_span: Any | None = None,
) -> Iterator[Any | None]:
    """Synchronous context manager creating and completing an active child span."""
    tracer = get_current_tracer()
    if tracer is None or not tracer.enabled:
        yield None
        return

    span = tracer.start_span(name=name, run_type=run_type, inputs=inputs, parent_span=parent_span)
    token = _current_span.set(span)
    try:
        yield span
        tracer.end_span(span)
    except Exception as exc:
        tracer.end_span(span, error=str(exc))
        raise
    finally:
        _current_span.reset(token)


@asynccontextmanager
async def async_span_context(
    name: str,
    run_type: str = "chain",
    inputs: dict[str, Any] | None = None,
    parent_span: Any | None = None,
) -> AsyncIterator[Any | None]:
    """Asynchronous context manager creating and completing an active child span."""
    tracer = get_current_tracer()
    if tracer is None or not tracer.enabled:
        yield None
        return

    span = tracer.start_span(name=name, run_type=run_type, inputs=inputs, parent_span=parent_span)
    token = _current_span.set(span)
    try:
        yield span
        tracer.end_span(span)
    except Exception as exc:
        tracer.end_span(span, error=str(exc))
        raise
    finally:
        _current_span.reset(token)
