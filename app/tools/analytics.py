"""Analytics domain tool wrapping PostHogAdapter for the Analytics Agent."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, ValidationError, model_validator

from app.config.settings import get_settings
from app.domain.analytics import AnalyticsQueryResult, EventName
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.exceptions import (
    PostHogAuthenticationError,
    PostHogError,
    PostHogNotFoundError,
    PostHogQueryError,
    PostHogRateLimitError,
    PostHogTimeoutError,
)
from app.tools.base import BaseTool, ToolError

# -----------------------------------------------------------------------------
# Controlled Taxonomy & Operators
# -----------------------------------------------------------------------------

AllowedAnalyticsProperty = Literal[
    "destination_bank",
    "source_bank",
    "primary_bank",
    "app_version",
    "user_type",
    "category",
    "document_type",
    "failure_code",
    "amount_ngn",
    "duration_ms",
]

FilterOperator = Literal["eq", "neq", "in", "not_in", "gt", "gte", "lt", "lte"]

NUMERIC_PROPERTIES: set[AllowedAnalyticsProperty] = {"amount_ngn", "duration_ms"}
CATEGORICAL_PROPERTIES: set[AllowedAnalyticsProperty] = {
    "destination_bank",
    "source_bank",
    "primary_bank",
    "app_version",
    "user_type",
    "category",
    "document_type",
    "failure_code",
}

NUMERIC_OPERATORS: set[FilterOperator] = {
    "gt",
    "gte",
    "lt",
    "lte",
    "eq",
    "neq",
    "in",
    "not_in",
}
CATEGORICAL_OPERATORS: set[FilterOperator] = {"eq", "neq", "in", "not_in"}


# -----------------------------------------------------------------------------
# Typed Filter Models
# -----------------------------------------------------------------------------


class AnalyticsPropertyFilter(BaseModel):
    """Typed property filter constraining dimensions, operators, and values."""

    property_name: AllowedAnalyticsProperty
    operator: FilterOperator = "eq"
    value: str | int | float | list[str] | list[int] | list[float]

    @model_validator(mode="before")
    @classmethod
    def reject_bool(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val = data.get("value")
            if isinstance(val, bool):
                raise ValueError("Boolean values are not supported for analytics property filters.")
            if isinstance(val, list) and any(isinstance(x, bool) for x in val):
                raise ValueError("Boolean values are not supported for analytics property filters.")
        return data

    @model_validator(mode="after")
    def validate_operator_and_value(self) -> Self:
        # Categorical dimensions: only eq, neq, in, not_in with str or list[str]
        if self.property_name in CATEGORICAL_PROPERTIES:
            if self.operator in ("gt", "gte", "lt", "lte"):
                raise ValueError(
                    f"Operator '{self.operator}' is not valid for categorical property '{self.property_name}'. "
                    f"Supported operators: {sorted(CATEGORICAL_OPERATORS)}"
                )
            if self.operator in ("in", "not_in"):
                if not isinstance(self.value, list) or not all(
                    isinstance(v, str) for v in self.value
                ):
                    raise ValueError(
                        f"Value for '{self.operator}' on '{self.property_name}' must be list[str]."
                    )
            else:
                if not isinstance(self.value, str):
                    raise ValueError(
                        f"Value for '{self.operator}' on '{self.property_name}' must be str."
                    )

        # Numeric dimensions: supports gt, gte, lt, lte, eq, neq, in, not_in with int/float
        elif self.property_name in NUMERIC_PROPERTIES:
            if self.operator in ("in", "not_in"):
                if not isinstance(self.value, list) or not all(
                    isinstance(v, (int, float)) and not isinstance(v, bool) for v in self.value
                ):
                    raise ValueError(
                        f"Value for '{self.operator}' on '{self.property_name}' must be list[int | float]."
                    )
            else:
                if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
                    raise ValueError(
                        f"Value for '{self.operator}' on '{self.property_name}' must be int or float."
                    )

        return self

    def to_hogql_clause(self) -> str:
        """Translate typed filter into a validated HogQL condition expression."""
        col = f"properties.{self.property_name}"
        op = self.operator

        if op == "eq":
            val_str = f"'{self.value}'" if isinstance(self.value, str) else str(self.value)
            return f"{col} = {val_str}"
        if op == "neq":
            val_str = f"'{self.value}'" if isinstance(self.value, str) else str(self.value)
            return f"{col} != {val_str}"
        if op == "in":
            items = ", ".join(
                f"'{v}'" if isinstance(v, str) else str(v)
                for v in self.value  # type: ignore[union-attr]
            )
            return f"{col} IN ({items})"
        if op == "not_in":
            items = ", ".join(
                f"'{v}'" if isinstance(v, str) else str(v)
                for v in self.value  # type: ignore[union-attr]
            )
            return f"{col} NOT IN ({items})"
        if op == "gt":
            return f"{col} > {self.value}"
        if op == "gte":
            return f"{col} >= {self.value}"
        if op == "lt":
            return f"{col} < {self.value}"
        if op == "lte":
            return f"{col} <= {self.value}"

        raise ValueError(f"Unsupported operator: {op}")


# -----------------------------------------------------------------------------
# Input & Output Contracts
# -----------------------------------------------------------------------------


class AnalyticsQueryIntent(StrEnum):
    """Controlled analytical intents supported by the Analytics Agent tool."""

    EVENT_COUNT = "event_count"
    BREAKDOWN = "breakdown"
    FUNNEL = "funnel"
    TREND = "trend"
    LIFECYCLE_DURATION = "lifecycle_duration"


class QueryAnalyticsInput(BaseModel):
    """Schema-constrained input for the Analytics Agent tool."""

    intent: AnalyticsQueryIntent = Field(..., description="Analytical intent")
    description: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="Clear human-readable description of what this query measures",
    )
    events: list[EventName] | None = Field(
        default=None,
        description="Event names from the approved 18-event taxonomy (for event_count, breakdown, trend)",
    )
    start_event: EventName | None = Field(
        default=None,
        description="Initiating event for lifecycle_duration intent (e.g. 'transfer_submitted')",
    )
    end_event: EventName | None = Field(
        default=None,
        description="Terminal/completion event for lifecycle_duration intent carrying duration metric (e.g. 'transfer_completed')",
    )
    property_name: AllowedAnalyticsProperty | None = Field(
        default=None,
        description="Property dimension for breakdown intent or duration metric (e.g. duration_ms)",
    )
    breakdown_by: AllowedAnalyticsProperty | None = Field(
        default=None,
        description="Optional breakdown/segmentation dimension for funnel, trend, or lifecycle analysis",
    )
    steps: list[EventName] | None = Field(
        default=None,
        description="Sequential funnel steps from approved taxonomy (minimum 2 steps)",
    )
    interval: Literal["hour", "day"] = Field(
        default="day",
        description="Aggregation time interval for trend analysis",
    )
    time_range_days: int | None = Field(
        default=None,
        ge=1,
        le=90,
        description="Relative time window in days (mutually exclusive with explicit timestamps)",
    )
    start_time: str | None = Field(
        default=None,
        description="ISO 8601 start timestamp (must be paired with end_time)",
    )
    end_time: str | None = Field(
        default=None,
        description="ISO 8601 end timestamp (must be paired with start_time)",
    )
    filters: list[AnalyticsPropertyFilter] | None = Field(
        default=None,
        description="Typed property filters constraining dimensions and values",
    )

    @model_validator(mode="after")
    def validate_time_window(self) -> Self:
        """Validate mutually exclusive time window contracts and ISO 8601 formatting."""
        has_days = self.time_range_days is not None
        has_start = self.start_time is not None
        has_end = self.end_time is not None

        if has_days and (has_start or has_end):
            raise ValueError(
                "Cannot specify both 'time_range_days' and explicit 'start_time'/'end_time'."
            )

        if has_start != has_end:
            raise ValueError(
                "Both 'start_time' and 'end_time' must be provided together for explicit time windows."
            )

        if has_start and has_end:
            try:
                t_start = datetime.fromisoformat(self.start_time.replace("Z", "+00:00"))  # type: ignore[union-attr]
                t_end = datetime.fromisoformat(self.end_time.replace("Z", "+00:00"))  # type: ignore[union-attr]
            except Exception as e:
                raise ValueError(
                    f"Invalid ISO 8601 timestamp in start_time or end_time: {e}"
                ) from e

            if t_end < t_start:
                raise ValueError(
                    f"end_time ({self.end_time}) must be greater than or equal to start_time ({self.start_time})."
                )

        return self

    @model_validator(mode="after")
    def validate_intent_contracts(self) -> Self:
        """Enforce strict intent-specific parameter compatibility."""
        if self.intent == AnalyticsQueryIntent.EVENT_COUNT:
            if not self.events or len(self.events) == 0:
                raise ValueError("Intent 'event_count' requires at least one event in 'events'.")
            if self.steps is not None:
                raise ValueError("Intent 'event_count' does not allow 'steps'.")
            if self.property_name is not None:
                raise ValueError("Intent 'event_count' does not allow 'property_name'.")
            if self.breakdown_by is not None:
                raise ValueError("Intent 'event_count' does not allow 'breakdown_by'.")
            if self.start_event is not None or self.end_event is not None:
                raise ValueError(
                    "Intent 'event_count' does not allow 'start_event' or 'end_event'."
                )

        elif self.intent == AnalyticsQueryIntent.BREAKDOWN:
            if not self.events or len(self.events) != 1:
                raise ValueError("Intent 'breakdown' requires exactly one event in 'events'.")
            if self.property_name is None:
                raise ValueError("Intent 'breakdown' requires 'property_name'.")
            if self.steps is not None:
                raise ValueError("Intent 'breakdown' does not allow 'steps'.")
            if self.breakdown_by is not None:
                raise ValueError(
                    "Intent 'breakdown' does not allow 'breakdown_by' (use 'property_name')."
                )
            if self.start_event is not None or self.end_event is not None:
                raise ValueError("Intent 'breakdown' does not allow 'start_event' or 'end_event'.")

        elif self.intent == AnalyticsQueryIntent.FUNNEL:
            if not self.steps or len(self.steps) < 2:
                raise ValueError("Intent 'funnel' requires at least 2 sequential steps in 'steps'.")
            if self.events is not None:
                raise ValueError("Intent 'funnel' does not allow 'events' (use 'steps').")
            if self.property_name is not None:
                raise ValueError(
                    "Intent 'funnel' does not allow 'property_name' (use 'breakdown_by')."
                )
            if self.start_event is not None or self.end_event is not None:
                raise ValueError("Intent 'funnel' does not allow 'start_event' or 'end_event'.")

        elif self.intent == AnalyticsQueryIntent.TREND:
            if not self.events or len(self.events) != 1:
                raise ValueError("Intent 'trend' requires exactly one event in 'events'.")
            if self.steps is not None:
                raise ValueError("Intent 'trend' does not allow 'steps'.")
            if self.property_name is not None:
                raise ValueError(
                    "Intent 'trend' does not allow 'property_name' (use 'breakdown_by')."
                )
            if self.start_event is not None or self.end_event is not None:
                raise ValueError("Intent 'trend' does not allow 'start_event' or 'end_event'.")

        elif self.intent == AnalyticsQueryIntent.LIFECYCLE_DURATION:
            if self.end_event is None:
                raise ValueError(
                    "Intent 'lifecycle_duration' requires 'end_event' (the terminal event carrying duration_ms)."
                )
            if self.events is not None:
                raise ValueError(
                    "Intent 'lifecycle_duration' does not allow 'events' (use 'end_event' and optional 'start_event')."
                )
            if self.steps is not None:
                raise ValueError("Intent 'lifecycle_duration' does not allow 'steps'.")
            if self.property_name is not None and self.property_name not in NUMERIC_PROPERTIES:
                raise ValueError(
                    f"property_name for 'lifecycle_duration' must be a numeric property (e.g. 'duration_ms'), got '{self.property_name}'."
                )

        return self


class QueryAnalyticsOutput(BaseModel):
    """Output envelope containing normalized analytics query result."""

    result: AnalyticsQueryResult


# -----------------------------------------------------------------------------
# Domain Tool Implementation
# -----------------------------------------------------------------------------


def _map_posthog_error(exc: Exception) -> ToolError:
    """Normalize PostHog integration exceptions into structured ToolError."""
    if isinstance(exc, PostHogNotFoundError):
        return ToolError(
            error_type="not_found",
            message=str(exc),
            attempted_source="posthog",
        )
    if isinstance(exc, PostHogTimeoutError):
        return ToolError(
            error_type="timeout",
            message=str(exc),
            attempted_source="posthog",
        )
    if isinstance(exc, PostHogAuthenticationError):
        return ToolError(
            error_type="authentication_error",
            message=str(exc),
            attempted_source="posthog",
        )
    if isinstance(exc, PostHogRateLimitError):
        return ToolError(
            error_type="rate_limit",
            message=str(exc),
            attempted_source="posthog",
        )
    if isinstance(exc, (PostHogQueryError, ValidationError)):
        return ToolError(
            error_type="invalid_input",
            message=f"Invalid query input: {exc}",
            attempted_source="posthog",
        )
    if isinstance(exc, PostHogError):
        return ToolError(
            error_type="upstream_error",
            message=str(exc),
            attempted_source="posthog",
        )
    return ToolError(
        error_type="upstream_error",
        message=f"Unexpected error: {exc}",
        attempted_source="posthog",
    )


class QueryAnalyticsTool(BaseTool):
    """Domain tool for executing structured product analytics queries in PostHog.

    Provides high-level analytical intents (counts, breakdowns, funnels, trends,
    lifecycle duration) with typed dimension filters and strict time-window validation.
    Arbitrary HogQL queries are strictly barred from this tool.
    """

    name: str = "query_analytics"
    description: str = (
        "Execute structured analytics queries against product event data. "
        "Supports intents: event_count, breakdown, funnel, trend, and lifecycle_duration."
    )

    def __init__(self, adapter: PostHogAdapter) -> None:
        self._adapter = adapter

    def _get_source_type(self) -> Literal["posthog"]:
        return "posthog"

    def _map_error(self, exc: Exception) -> ToolError:
        return _map_posthog_error(exc)

    async def _execute(self, input_data: Any) -> tuple[QueryAnalyticsOutput, str]:
        if not isinstance(input_data, QueryAnalyticsInput):
            input_data = QueryAnalyticsInput.model_validate(input_data)

        # Build condition clauses from typed filters
        condition_clauses: list[str] | None = None
        if input_data.filters:
            condition_clauses = [f.to_hogql_clause() for f in input_data.filters]

        # All runtime analytics reads are isolated to the active reproducible
        # demo dataset. This prevents a reseed from silently mixing old and new
        # synthetic events, while keeping the versioning concern outside agent
        # prompts and decisions.
        dataset_version = get_settings().demo_dataset_version.replace("'", "''")
        condition_clauses = [
            *(condition_clauses or []),
            f"properties.dataset_version = '{dataset_version}'",
        ]

        intent = input_data.intent
        result: AnalyticsQueryResult

        if intent == AnalyticsQueryIntent.EVENT_COUNT:
            assert input_data.events is not None
            result = await self._adapter.query_event_counts(
                events=list(input_data.events),
                time_range_days=input_data.time_range_days,
                start_time=input_data.start_time,
                end_time=input_data.end_time,
                condition_clauses=condition_clauses,
            )
            source_ref = f"query:event_count:{','.join(input_data.events)}"

        elif intent == AnalyticsQueryIntent.BREAKDOWN:
            assert input_data.events is not None
            assert input_data.property_name is not None
            result = await self._adapter.query_breakdown(
                event=input_data.events[0],
                property_name=input_data.property_name,
                time_range_days=input_data.time_range_days,
                start_time=input_data.start_time,
                end_time=input_data.end_time,
                condition_clauses=condition_clauses,
            )
            source_ref = f"query:breakdown:{input_data.events[0]}:{input_data.property_name}"

        elif intent == AnalyticsQueryIntent.FUNNEL:
            assert input_data.steps is not None
            result = await self._adapter.query_funnel(
                steps=list(input_data.steps),
                time_range_days=input_data.time_range_days,
                start_time=input_data.start_time,
                end_time=input_data.end_time,
                breakdown_property=input_data.breakdown_by,
                condition_clauses=condition_clauses,
            )
            source_ref = f"query:funnel:{'->'.join(input_data.steps)}"

        elif intent == AnalyticsQueryIntent.TREND:
            assert input_data.events is not None
            result = await self._adapter.query_trend(
                event=input_data.events[0],
                interval=input_data.interval,
                time_range_days=input_data.time_range_days or 30,
                start_time=input_data.start_time,
                end_time=input_data.end_time,
                breakdown_property=input_data.breakdown_by,
                condition_clauses=condition_clauses,
            )
            source_ref = f"query:trend:{input_data.events[0]}:{input_data.interval}"

        elif intent == AnalyticsQueryIntent.LIFECYCLE_DURATION:
            assert input_data.end_event is not None
            target_event = input_data.end_event
            duration_prop = input_data.property_name or "duration_ms"
            result = await self._adapter.query_lifecycle_duration(
                event=target_event,
                duration_property=duration_prop,
                breakdown_property=input_data.breakdown_by,
                time_range_days=input_data.time_range_days,
                start_time=input_data.start_time,
                end_time=input_data.end_time,
                condition_clauses=condition_clauses,
            )
            event_pair_desc = (
                f"{input_data.start_event}->{target_event}"
                if input_data.start_event
                else target_event
            )
            source_ref = f"query:lifecycle_duration:{event_pair_desc}"

        else:
            raise ValueError(f"Unhandled analytical intent: {intent}")

        output = QueryAnalyticsOutput(result=result)
        return output, source_ref
