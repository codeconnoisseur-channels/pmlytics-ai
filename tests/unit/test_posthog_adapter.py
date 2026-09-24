"""Unit tests for PostHogAdapter query builders and response normalization."""

import pytest
import respx
from app.domain.analytics import AnalyticsQueryResult
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.client import PostHogClient
from app.integrations.posthog.exceptions import PostHogQueryError

HOST = "https://us.posthog.com"
PROJECT_ID = "12345"
API_KEY = "phx_test_key"
QUERY_URL = f"{HOST}/api/projects/{PROJECT_ID}/query/"


@pytest.fixture
def adapter() -> PostHogAdapter:
    client = PostHogClient(host=HOST, project_id=PROJECT_ID, api_key=API_KEY)
    return PostHogAdapter(client)


def test_sql_validation_disallowed_tokens(adapter: PostHogAdapter) -> None:
    with pytest.raises(PostHogQueryError) as exc_info:
        adapter._validate_sql("DROP TABLE events")
    assert "Disallowed statement" in str(exc_info.value)

    with pytest.raises(PostHogQueryError) as exc_info:
        adapter._validate_sql("DELETE FROM events WHERE 1=1")
    assert "Disallowed statement" in str(exc_info.value)

    with pytest.raises(PostHogQueryError) as exc_info:
        adapter._validate_sql("INSERT INTO events VALUES (1)")
    assert "Disallowed statement" in str(exc_info.value)

    with pytest.raises(PostHogQueryError) as exc_info:
        adapter._validate_sql("UPDATE events SET x=1")
    assert "Disallowed statement" in str(exc_info.value)


def test_sql_validation_non_select(adapter: PostHogAdapter) -> None:
    with pytest.raises(PostHogQueryError) as exc_info:
        adapter._validate_sql("SHOW TABLES")
    assert "must begin with SELECT or WITH" in str(exc_info.value)


def test_build_event_count_query(adapter: PostHogAdapter) -> None:
    sql = adapter.build_event_count_query(
        events=["transfer_submitted", "transfer_completed"],
        time_range_days=7,
        filters={"destination_bank": "Bank A"},
    )
    assert "SELECT event, count() FROM events" in sql
    assert "event IN ('transfer_submitted', 'transfer_completed')" in sql
    assert "properties.destination_bank = 'Bank A'" in sql
    assert "INTERVAL 7 DAY" in sql


def test_build_breakdown_query(adapter: PostHogAdapter) -> None:
    sql = adapter.build_breakdown_query(
        event="bill_payment_failed",
        property_name="category",
        start_time="2026-08-12T00:00:00Z",
        end_time="2026-08-13T00:00:00Z",
    )
    assert "properties.category AS category" in sql
    assert "event = 'bill_payment_failed'" in sql
    assert "timestamp >= '2026-08-12T00:00:00Z'" in sql
    assert "timestamp <= '2026-08-13T00:00:00Z'" in sql


def test_build_funnel_query(adapter: PostHogAdapter) -> None:
    sql = adapter.build_funnel_query(
        steps=["kyc_started", "kyc_document_submitted", "kyc_completed"],
        breakdown_property="user_type",
    )
    assert "properties.user_type AS user_type" in sql
    assert "count(DISTINCT distinct_id) AS unique_users" in sql
    assert "event IN ('kyc_started', 'kyc_document_submitted', 'kyc_completed')" in sql


def test_build_trend_query(adapter: PostHogAdapter) -> None:
    sql = adapter.build_trend_query(
        event="transfer_completed",
        interval="day",
        time_range_days=14,
    )
    assert "toStartOfDay(timestamp) AS date" in sql
    assert "event = 'transfer_completed'" in sql


def test_build_lifecycle_duration_query(adapter: PostHogAdapter) -> None:
    sql = adapter.build_lifecycle_duration_query(
        event="transfer_completed",
        duration_property="duration_ms",
        breakdown_property="destination_bank",
    )
    assert "properties.destination_bank AS destination_bank" in sql
    assert "median(properties.duration_ms) AS median_duration" in sql
    assert "quantile(0.95)(properties.duration_ms) AS p95_duration" in sql


@pytest.mark.asyncio
async def test_execute_query_normalizes_tabular_response(adapter: PostHogAdapter) -> None:
    fake_response = {
        "columns": ["event", "count()"],
        "types": ["String", "UInt64"],
        "results": [
            ["transfer_started", 100],
            ["transfer_completed", 95],
        ],
    }
    with respx.mock:
        respx.post(QUERY_URL).respond(200, json=fake_response)
        result = await adapter.query_event_counts(["transfer_started", "transfer_completed"])

        assert isinstance(result, AnalyticsQueryResult)
        assert result.metric == "event_count"
        assert result.raw_count == 2
        assert len(result.rows) == 2
        assert result.rows[0] == {"event": "transfer_started", "count()": 100}
        assert result.rows[1] == {"event": "transfer_completed", "count()": 95}
        assert "event" in result.dimensions


@pytest.mark.asyncio
async def test_execute_query_scalar_value(adapter: PostHogAdapter) -> None:
    fake_response = {
        "columns": ["count()"],
        "types": ["UInt64"],
        "results": [[42]],
    }
    with respx.mock:
        respx.post(QUERY_URL).respond(200, json=fake_response)
        result = await adapter.execute_query("SELECT count() FROM events", metric="total_count")

        assert result.value == 42
        assert result.raw_count == 1
        assert len(result.limitations) == 0


@pytest.mark.asyncio
async def test_execute_query_empty_results_adds_limitation(adapter: PostHogAdapter) -> None:
    fake_response = {
        "columns": ["event", "count()"],
        "types": ["String", "UInt64"],
        "results": [],
    }
    with respx.mock:
        respx.post(QUERY_URL).respond(200, json=fake_response)
        result = await adapter.execute_query("SELECT event, count() FROM events WHERE 1=0")

        assert result.raw_count == 0
        assert len(result.rows) == 0
        assert any("zero rows" in lim for lim in result.limitations)
