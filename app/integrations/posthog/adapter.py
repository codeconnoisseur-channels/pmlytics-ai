"""Read-only PostHog adapter providing query execution and domain mapping."""

import logging
import re
from typing import Any

from app.domain.analytics import AnalyticsQueryResult
from app.integrations.posthog.client import PostHogClient
from app.integrations.posthog.exceptions import PostHogQueryError

logger = logging.getLogger(__name__)

# Disallowed SQL tokens to prevent harmful statements
_DISALLOWED_TOKENS_RE = re.compile(
    r"\b(ALTER|CREATE|DELETE|DROP|INSERT|RENAME|TRUNCATE|UPDATE|ATTACH|DETACH|KILL)\b",
    re.IGNORECASE,
)


class PostHogAdapter:
    """Application adapter for querying product analytics from PostHog.

    Provides a clean lower-level query execution and domain-normalization facade.
    Encapsulates validated HogQL execution and tabular result mapping.
    Zero diagnostic or agent reasoning policies are encoded here.
    """

    def __init__(self, client: PostHogClient) -> None:
        self._client = client

    def _validate_sql(self, query: str) -> None:
        """Enforce read-only SQL safety invariants."""
        stripped = query.strip()
        if not stripped:
            raise PostHogQueryError("Query cannot be empty")

        if _DISALLOWED_TOKENS_RE.search(stripped):
            raise PostHogQueryError(
                "Disallowed statement in query: only read queries are permitted"
            )

        if not re.match(r"^(SELECT|WITH)\b", stripped, re.IGNORECASE):
            raise PostHogQueryError("Query must begin with SELECT or WITH")

    async def execute_query(
        self,
        query: str,
        query_description: str = "Custom HogQL Query",
        metric: str = "custom",
        time_range: str | None = None,
        limitations: list[str] | None = None,
    ) -> AnalyticsQueryResult:
        """Execute a validated HogQL query and normalize the tabular response into AnalyticsQueryResult.

        Args:
            query: The HogQL query string.
            query_description: Human-readable intent of the query.
            metric: Primary metric label.
            time_range: Optional description of the queried time window.
            limitations: Optional known limitations of the query.

        Returns:
            Normalized AnalyticsQueryResult domain model.
        """
        self._validate_sql(query)
        limitations_list = limitations or []

        raw_response = await self._client.execute_query(query)

        columns: list[str] = raw_response.get("columns", [])
        raw_results: list[list[Any]] = raw_response.get("results", [])

        rows: list[dict[str, Any]] = []
        for raw_row in raw_results:
            row_dict = {columns[i]: val for i, val in enumerate(raw_row) if i < len(columns)}
            rows.append(row_dict)

        primary_value: str | float | int | None = None
        if len(rows) == 1 and len(columns) == 1:
            primary_value = raw_results[0][0]
        elif len(rows) == 1 and "count()" in columns:
            primary_value = rows[0]["count()"]
        elif not rows:
            limitations_list.append("Query returned zero rows matching criteria.")

        # Non-aggregate columns are dimensions
        dimensions = [
            c
            for c in columns
            if not (c.endswith("()") or "count" in c.lower() or "sum(" in c.lower())
        ]

        return AnalyticsQueryResult(
            query_description=query_description,
            metric=metric,
            value=primary_value,
            dimensions=dimensions,
            rows=rows,
            time_range=time_range,
            limitations=limitations_list,
            raw_count=len(rows),
        )

    # -------------------------------------------------------------------------
    # Lightweight Query Construction Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_where_clause(
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> str:
        conditions: list[str] = []

        if start_time and end_time:
            conditions.append(f"timestamp >= '{start_time}' AND timestamp <= '{end_time}'")
        elif start_time:
            conditions.append(f"timestamp >= '{start_time}'")
        elif end_time:
            conditions.append(f"timestamp <= '{end_time}'")
        elif time_range_days:
            conditions.append(f"timestamp >= now() - INTERVAL {time_range_days} DAY")

        if filters:
            for k, v in filters.items():
                col = (
                    f"properties.{k}"
                    if not k.startswith("properties.")
                    and k not in ("event", "distinct_id", "timestamp")
                    else k
                )
                if isinstance(v, str):
                    conditions.append(f"{col} = '{v}'")
                elif isinstance(v, (int, float)):
                    conditions.append(f"{col} = {v}")
                elif isinstance(v, list):
                    items = ", ".join(
                        f"'{item}'" if isinstance(item, str) else str(item) for item in v
                    )
                    conditions.append(f"{col} IN ({items})")
                elif v is None:
                    conditions.append(f"{col} IS NULL")

        if condition_clauses:
            conditions.extend(condition_clauses)

        return " AND ".join(conditions) if conditions else "1=1"

    def build_event_count_query(
        self,
        events: list[str],
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> str:
        """Construct HogQL counting occurrences of specified events."""
        where = self._build_where_clause(
            time_range_days, start_time, end_time, filters, condition_clauses
        )
        events_list = ", ".join(f"'{e}'" for e in events)
        return (
            f"SELECT event, count() FROM events "
            f"WHERE event IN ({events_list}) AND {where} "
            f"GROUP BY event ORDER BY count() DESC"
        )

    def build_breakdown_query(
        self,
        event: str,
        property_name: str,
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> str:
        """Construct HogQL breaking down an event by a property."""
        where = self._build_where_clause(
            time_range_days, start_time, end_time, filters, condition_clauses
        )
        prop_col = f"properties.{property_name}"
        return (
            f"SELECT {prop_col} AS {property_name}, count() FROM events "
            f"WHERE event = '{event}' AND {where} "
            f"GROUP BY 1 ORDER BY count() DESC"
        )

    def build_funnel_query(
        self,
        steps: list[str],
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        breakdown_property: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> str:
        """Construct HogQL for sequential step-by-step funnel drop-off analysis."""
        where = self._build_where_clause(
            time_range_days, start_time, end_time, filters, condition_clauses
        )
        steps_list = ", ".join(f"'{s}'" for s in steps)

        if breakdown_property:
            prop_col = f"properties.{breakdown_property}"
            return (
                f"SELECT {prop_col} AS {breakdown_property}, event, count(DISTINCT distinct_id) AS unique_users "
                f"FROM events "
                f"WHERE event IN ({steps_list}) AND {where} "
                f"GROUP BY 1, 2 ORDER BY {breakdown_property}, unique_users DESC"
            )

        return (
            f"SELECT event, count(DISTINCT distinct_id) AS unique_users, count() AS total_events "
            f"FROM events "
            f"WHERE event IN ({steps_list}) AND {where} "
            f"GROUP BY event ORDER BY total_events DESC"
        )

    def build_trend_query(
        self,
        event: str,
        interval: str = "day",
        time_range_days: int | None = 30,
        start_time: str | None = None,
        end_time: str | None = None,
        breakdown_property: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> str:
        """Construct HogQL for time-series trend analysis."""
        where = self._build_where_clause(
            time_range_days, start_time, end_time, filters, condition_clauses
        )
        date_trunc = "toStartOfDay(timestamp)" if interval == "day" else "toStartOfHour(timestamp)"

        if breakdown_property:
            prop_col = f"properties.{breakdown_property}"
            return (
                f"SELECT {date_trunc} AS date, {prop_col} AS {breakdown_property}, count() "
                f"FROM events "
                f"WHERE event = '{event}' AND {where} "
                f"GROUP BY 1, 2 ORDER BY 1 ASC, 3 DESC"
            )

        return (
            f"SELECT {date_trunc} AS date, count() "
            f"FROM events "
            f"WHERE event = '{event}' AND {where} "
            f"GROUP BY 1 ORDER BY 1 ASC"
        )

    def build_lifecycle_duration_query(
        self,
        event: str,
        duration_property: str = "duration_ms",
        breakdown_property: str | None = None,
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> str:
        """Construct HogQL analyzing lifecycle duration metric on events."""
        where = self._build_where_clause(
            time_range_days, start_time, end_time, filters, condition_clauses
        )
        prop_col = f"properties.{duration_property}"

        if breakdown_property:
            b_col = f"properties.{breakdown_property}"
            return (
                f"SELECT {b_col} AS {breakdown_property}, "
                f"count(), "
                f"avg({prop_col}) AS avg_duration, "
                f"median({prop_col}) AS median_duration, "
                f"quantile(0.95)({prop_col}) AS p95_duration "
                f"FROM events "
                f"WHERE event = '{event}' AND {prop_col} IS NOT NULL AND {where} "
                f"GROUP BY 1 ORDER BY count() DESC"
            )

        return (
            f"SELECT count(), "
            f"avg({prop_col}) AS avg_duration, "
            f"median({prop_col}) AS median_duration, "
            f"quantile(0.95)({prop_col}) AS p95_duration "
            f"FROM events "
            f"WHERE event = '{event}' AND {prop_col} IS NOT NULL AND {where}"
        )

    # -------------------------------------------------------------------------
    # High-level Convenience Adapter Methods
    # -------------------------------------------------------------------------

    async def query_event_counts(
        self,
        events: list[str],
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> AnalyticsQueryResult:
        """Execute an event count query across multiple events."""
        sql = self.build_event_count_query(
            events, time_range_days, start_time, end_time, filters, condition_clauses
        )
        return await self.execute_query(
            sql,
            query_description=f"Event counts for {events}",
            metric="event_count",
            time_range=f"{time_range_days} days"
            if time_range_days
            else f"{start_time} to {end_time}",
        )

    async def query_breakdown(
        self,
        event: str,
        property_name: str,
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> AnalyticsQueryResult:
        """Execute a breakdown query for an event by a property."""
        sql = self.build_breakdown_query(
            event, property_name, time_range_days, start_time, end_time, filters, condition_clauses
        )
        return await self.execute_query(
            sql,
            query_description=f"Breakdown of {event} by {property_name}",
            metric=f"{property_name}_breakdown",
            time_range=f"{time_range_days} days"
            if time_range_days
            else f"{start_time} to {end_time}",
        )

    async def query_funnel(
        self,
        steps: list[str],
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        breakdown_property: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> AnalyticsQueryResult:
        """Execute a multi-step funnel query."""
        sql = self.build_funnel_query(
            steps,
            time_range_days,
            start_time,
            end_time,
            breakdown_property,
            filters,
            condition_clauses,
        )
        return await self.execute_query(
            sql,
            query_description=f"Funnel analysis for {steps}",
            metric="funnel_conversion",
            time_range=f"{time_range_days} days"
            if time_range_days
            else f"{start_time} to {end_time}",
        )

    async def query_trend(
        self,
        event: str,
        interval: str = "day",
        time_range_days: int | None = 30,
        start_time: str | None = None,
        end_time: str | None = None,
        breakdown_property: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> AnalyticsQueryResult:
        """Execute a time-series trend query."""
        sql = self.build_trend_query(
            event,
            interval,
            time_range_days,
            start_time,
            end_time,
            breakdown_property,
            filters,
            condition_clauses,
        )
        return await self.execute_query(
            sql,
            query_description=f"Trend for {event} over time",
            metric="event_trend",
            time_range=f"{time_range_days} days"
            if time_range_days
            else f"{start_time} to {end_time}",
        )

    async def query_lifecycle_duration(
        self,
        event: str,
        duration_property: str = "duration_ms",
        breakdown_property: str | None = None,
        time_range_days: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        filters: dict[str, Any] | None = None,
        condition_clauses: list[str] | None = None,
    ) -> AnalyticsQueryResult:
        """Execute a duration distribution query for an event."""
        sql = self.build_lifecycle_duration_query(
            event,
            duration_property,
            breakdown_property,
            time_range_days,
            start_time,
            end_time,
            filters,
            condition_clauses,
        )
        return await self.execute_query(
            sql,
            query_description=f"Lifecycle duration for {event} ({duration_property})",
            metric="duration_ms",
            time_range=f"{time_range_days} days"
            if time_range_days
            else f"{start_time} to {end_time}",
        )
