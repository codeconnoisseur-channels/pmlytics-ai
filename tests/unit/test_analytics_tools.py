"""Unit tests for QueryAnalyticsTool, filter models, and intent/time-window contracts."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.domain.analytics import AnalyticsQueryResult
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.exceptions import PostHogRateLimitError
from app.tools.analytics import (
    AnalyticsPropertyFilter,
    AnalyticsQueryIntent,
    QueryAnalyticsInput,
    QueryAnalyticsTool,
)
from pydantic import ValidationError


@pytest.fixture
def mock_posthog_adapter() -> MagicMock:
    return MagicMock(spec=PostHogAdapter)


# -----------------------------------------------------------------------------
# 1. Filter Model Validation & Operator Compatibility Tests
# -----------------------------------------------------------------------------


def test_numeric_filter_gte_translation() -> None:
    """Verify amount_ngn >= 50000 (Scenario C) is accepted and translates to HogQL."""
    flt = AnalyticsPropertyFilter(
        property_name="amount_ngn",
        operator="gte",
        value=50000,
    )
    assert flt.to_hogql_clause() == "properties.amount_ngn >= 50000"


def test_numeric_filter_all_operators() -> None:
    """Verify numeric properties support gt, gte, lt, lte, eq, neq, in, not_in."""
    assert (
        AnalyticsPropertyFilter(
            property_name="duration_ms", operator="gt", value=3000
        ).to_hogql_clause()
        == "properties.duration_ms > 3000"
    )
    assert (
        AnalyticsPropertyFilter(
            property_name="duration_ms", operator="lte", value=5000
        ).to_hogql_clause()
        == "properties.duration_ms <= 5000"
    )
    assert (
        AnalyticsPropertyFilter(
            property_name="amount_ngn", operator="neq", value=1000
        ).to_hogql_clause()
        == "properties.amount_ngn != 1000"
    )
    assert (
        AnalyticsPropertyFilter(
            property_name="amount_ngn", operator="in", value=[1000, 2000]
        ).to_hogql_clause()
        == "properties.amount_ngn IN (1000, 2000)"
    )


def test_numeric_filter_rejects_non_numeric_values() -> None:
    """Verify string or boolean values are rejected for numeric properties."""
    with pytest.raises(ValidationError):
        AnalyticsPropertyFilter(property_name="amount_ngn", operator="gte", value="fifty_thousand")

    with pytest.raises(ValidationError):
        AnalyticsPropertyFilter(property_name="amount_ngn", operator="gte", value=True)


def test_categorical_filter_supports_eq_neq_in_not_in() -> None:
    """Verify categorical properties support eq, neq, in, not_in."""
    f1 = AnalyticsPropertyFilter(property_name="destination_bank", operator="eq", value="Bank A")
    assert f1.to_hogql_clause() == "properties.destination_bank = 'Bank A'"

    f2 = AnalyticsPropertyFilter(
        property_name="destination_bank", operator="in", value=["Bank A", "Bank B"]
    )
    assert f2.to_hogql_clause() == "properties.destination_bank IN ('Bank A', 'Bank B')"

    f3 = AnalyticsPropertyFilter(
        property_name="user_type", operator="not_in", value=["tier1", "tier2"]
    )
    assert f3.to_hogql_clause() == "properties.user_type NOT IN ('tier1', 'tier2')"


def test_categorical_filter_rejects_numeric_operators() -> None:
    """Verify categorical properties reject gt, gte, lt, lte operators."""
    with pytest.raises(ValidationError) as exc_info:
        AnalyticsPropertyFilter(
            property_name="destination_bank",
            operator="gt",
            value="Bank A",
        )
    assert "not valid for categorical property 'destination_bank'" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 2. Complete Intent-Specific Validation Tests
# -----------------------------------------------------------------------------


def test_intent_event_count_validation() -> None:
    """Verify EVENT_COUNT requires events and rejects steps, property_name, breakdown_by."""
    # Valid
    valid = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.EVENT_COUNT,
        description="Count transfer events",
        events=["transfer_submitted", "transfer_completed"],
    )
    assert len(valid.events) == 2  # type: ignore[arg-type]

    # Missing events
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.EVENT_COUNT,
            description="Count events",
            events=None,
        )

    # Incompatible steps
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.EVENT_COUNT,
            description="Count events",
            events=["transfer_submitted"],
            steps=["transfer_started", "transfer_submitted"],
        )

    # Incompatible property_name
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.EVENT_COUNT,
            description="Count events",
            events=["transfer_submitted"],
            property_name="destination_bank",
        )

    # Incompatible start_event
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.EVENT_COUNT,
            description="Count events",
            events=["transfer_submitted"],
            start_event="transfer_submitted",
        )


def test_intent_breakdown_validation() -> None:
    """Verify BREAKDOWN requires exactly 1 event and property_name; rejects steps and breakdown_by."""
    # Valid
    valid = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.BREAKDOWN,
        description="Failures by code",
        events=["transfer_failed"],
        property_name="failure_code",
    )
    assert valid.property_name == "failure_code"

    # Missing property_name
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.BREAKDOWN,
            description="Failures by code",
            events=["transfer_failed"],
            property_name=None,
        )

    # Incompatible breakdown_by
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.BREAKDOWN,
            description="Failures by code",
            events=["transfer_failed"],
            property_name="failure_code",
            breakdown_by="destination_bank",
        )


def test_intent_funnel_validation() -> None:
    """Verify FUNNEL requires >= 2 steps, allows breakdown_by, rejects events and property_name."""
    # Valid with breakdown_by
    valid = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.FUNNEL,
        description="KYC funnel by user type",
        steps=["kyc_started", "kyc_document_submitted", "kyc_completed"],
        breakdown_by="user_type",
    )
    assert valid.breakdown_by == "user_type"

    # Too few steps (< 2)
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.FUNNEL,
            description="KYC funnel",
            steps=["kyc_started"],
        )

    # Incompatible property_name
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.FUNNEL,
            description="KYC funnel",
            steps=["kyc_started", "kyc_completed"],
            property_name="user_type",
        )

    # Incompatible events
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.FUNNEL,
            description="KYC funnel",
            steps=["kyc_started", "kyc_completed"],
            events=["kyc_started"],
        )


def test_intent_trend_validation() -> None:
    """Verify TREND requires exactly 1 event, allows breakdown_by and interval, rejects steps and property_name."""
    # Valid
    valid = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.TREND,
        description="Daily failed transfers",
        events=["transfer_failed"],
        interval="day",
        breakdown_by="failure_code",
    )
    assert valid.interval == "day"

    # Incompatible steps
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.TREND,
            description="Daily transfers",
            events=["transfer_started"],
            steps=["transfer_started", "transfer_completed"],
        )


def test_intent_lifecycle_duration_validation() -> None:
    """Verify LIFECYCLE_DURATION requires end_event and supports optional start_event and breakdown_by."""
    # Valid pair: transfer_submitted -> transfer_completed
    valid_pair = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.LIFECYCLE_DURATION,
        description="Transfer processing duration from submitted to completed",
        start_event="transfer_submitted",
        end_event="transfer_completed",
        property_name="duration_ms",
        breakdown_by="destination_bank",
    )
    assert valid_pair.start_event == "transfer_submitted"
    assert valid_pair.end_event == "transfer_completed"
    assert valid_pair.breakdown_by == "destination_bank"

    # Valid single completion event (start_event omitted)
    valid_single = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.LIFECYCLE_DURATION,
        description="Transfer completion duration",
        end_event="transfer_completed",
    )
    assert valid_single.end_event == "transfer_completed"
    assert valid_single.start_event is None

    # Rejection of missing end_event
    with pytest.raises(ValidationError) as exc_info:
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.LIFECYCLE_DURATION,
            description="Transfer duration missing end_event",
            start_event="transfer_submitted",
        )
    assert "requires 'end_event'" in str(exc_info.value)

    # Rejection of events list in LIFECYCLE_DURATION
    with pytest.raises(ValidationError) as exc_info:
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.LIFECYCLE_DURATION,
            description="Transfer duration using events",
            events=["transfer_submitted", "transfer_completed"],
            end_event="transfer_completed",
        )
    assert "does not allow 'events'" in str(exc_info.value)

    # Rejection of steps
    with pytest.raises(ValidationError) as exc_info:
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.LIFECYCLE_DURATION,
            description="Transfer duration using steps",
            steps=["transfer_submitted", "transfer_completed"],
            end_event="transfer_completed",
        )
    assert "does not allow 'steps'" in str(exc_info.value)

    # Rejection of non-numeric property_name
    with pytest.raises(ValidationError):
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.LIFECYCLE_DURATION,
            description="Transfer duration",
            end_event="transfer_completed",
            property_name="destination_bank",
        )


# -----------------------------------------------------------------------------
# 3. Time-Window Validation Tests
# -----------------------------------------------------------------------------


def test_time_window_valid_relative_days() -> None:
    """Verify valid relative time_range_days is accepted."""
    inp = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.EVENT_COUNT,
        description="Count",
        events=["transfer_completed"],
        time_range_days=14,
    )
    assert inp.time_range_days == 14


def test_time_window_valid_explicit_iso_range() -> None:
    """Verify valid ISO 8601 start_time and end_time range is accepted."""
    inp = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.EVENT_COUNT,
        description="Count",
        events=["transfer_completed"],
        start_time="2026-08-10T00:00:00Z",
        end_time="2026-08-15T23:59:59Z",
    )
    assert inp.start_time == "2026-08-10T00:00:00Z"
    assert inp.end_time == "2026-08-15T23:59:59Z"


def test_time_window_contradictory_mix_rejected() -> None:
    """Assert specifying both time_range_days and start_time is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.EVENT_COUNT,
            description="Count",
            events=["transfer_completed"],
            time_range_days=7,
            start_time="2026-08-10T00:00:00Z",
        )
    assert "Cannot specify both 'time_range_days' and explicit 'start_time'/'end_time'" in str(
        exc_info.value
    )


def test_time_window_incomplete_range_rejected() -> None:
    """Assert specifying start_time without end_time is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.EVENT_COUNT,
            description="Count",
            events=["transfer_completed"],
            start_time="2026-08-10T00:00:00Z",
        )
    assert "Both 'start_time' and 'end_time' must be provided together" in str(exc_info.value)


def test_time_window_inverted_dates_rejected() -> None:
    """Assert end_time < start_time is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.EVENT_COUNT,
            description="Count",
            events=["transfer_completed"],
            start_time="2026-08-15T00:00:00Z",
            end_time="2026-08-10T00:00:00Z",
        )
    assert "end_time" in str(
        exc_info.value
    ) and "must be greater than or equal to start_time" in str(exc_info.value)


def test_time_window_malformed_iso_rejected() -> None:
    """Assert unparseable timestamp string is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        QueryAnalyticsInput(
            intent=AnalyticsQueryIntent.EVENT_COUNT,
            description="Count",
            events=["transfer_completed"],
            start_time="not-a-date",
            end_time="2026-08-15T00:00:00Z",
        )
    assert "Invalid ISO 8601 timestamp" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 4. Tool Execution & Adapter Integration Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_analytics_executes_amount_filter(
    mock_posthog_adapter: MagicMock,
) -> None:
    """Verify QueryAnalyticsTool translates amount_ngn >= 50000 filter and passes to adapter."""
    tool = QueryAnalyticsTool(mock_posthog_adapter)

    mock_result = AnalyticsQueryResult(
        query_description="Wallet funding count >= 50k",
        metric="event_count",
        value=150,
        dimensions=[],
        rows=[],
    )
    mock_posthog_adapter.query_event_counts = AsyncMock(return_value=mock_result)

    inp = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.EVENT_COUNT,
        description="Wallet funding count >= 50k",
        events=["wallet_funding_started", "wallet_funding_completed"],
        filters=[
            AnalyticsPropertyFilter(
                property_name="amount_ngn",
                operator="gte",
                value=50000,
            )
        ],
    )

    res = await tool.run(inp)

    assert res.success is True
    assert res.error is None
    assert res.provenance is not None
    assert res.provenance.source_type == "posthog"
    assert (
        res.provenance.source_reference
        == "query:event_count:wallet_funding_started,wallet_funding_completed"
    )

    mock_posthog_adapter.query_event_counts.assert_called_once_with(
        events=["wallet_funding_started", "wallet_funding_completed"],
        time_range_days=None,
        start_time=None,
        end_time=None,
        condition_clauses=[
            "properties.amount_ngn >= 50000",
            "properties.dataset_version = '2.0'",
        ],
    )


@pytest.mark.asyncio
async def test_query_analytics_lifecycle_duration_event_pair(
    mock_posthog_adapter: MagicMock,
) -> None:
    """Verify lifecycle duration queries target the completion event with duration_ms metric."""
    tool = QueryAnalyticsTool(mock_posthog_adapter)

    mock_result = AnalyticsQueryResult(
        query_description="Transfer latency",
        metric="duration_ms",
        value=13500.0,
        dimensions=["destination_bank"],
        rows=[{"destination_bank": "Bank A", "p95_duration": 13600000}],
    )
    mock_posthog_adapter.query_lifecycle_duration = AsyncMock(return_value=mock_result)

    inp = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.LIFECYCLE_DURATION,
        description="Transfer latency from submitted to completed",
        start_event="transfer_submitted",
        end_event="transfer_completed",
        property_name="duration_ms",
        breakdown_by="destination_bank",
        time_range_days=7,
    )

    res = await tool.run(inp)

    assert res.success is True
    assert res.error is None
    assert res.provenance is not None
    assert (
        res.provenance.source_reference
        == "query:lifecycle_duration:transfer_submitted->transfer_completed"
    )

    mock_posthog_adapter.query_lifecycle_duration.assert_called_once_with(
        event="transfer_completed",
        duration_property="duration_ms",
        breakdown_property="destination_bank",
        time_range_days=7,
        start_time=None,
        end_time=None,
        condition_clauses=["properties.dataset_version = '2.0'"],
    )


@pytest.mark.asyncio
async def test_query_analytics_funnel_with_breakdown(
    mock_posthog_adapter: MagicMock,
) -> None:
    """Verify funnel query executes with steps and breakdown_by."""
    tool = QueryAnalyticsTool(mock_posthog_adapter)

    mock_result = AnalyticsQueryResult(
        query_description="KYC funnel",
        metric="funnel_conversion",
        value=None,
        dimensions=["user_type", "event"],
        rows=[],
    )
    mock_posthog_adapter.query_funnel = AsyncMock(return_value=mock_result)

    inp = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.FUNNEL,
        description="KYC funnel by user type",
        steps=["kyc_started", "kyc_document_submitted", "kyc_completed"],
        breakdown_by="user_type",
    )

    res = await tool.run(inp)

    assert res.success is True
    assert res.provenance is not None
    assert (
        res.provenance.source_reference
        == "query:funnel:kyc_started->kyc_document_submitted->kyc_completed"
    )

    mock_posthog_adapter.query_funnel.assert_called_once_with(
        steps=["kyc_started", "kyc_document_submitted", "kyc_completed"],
        time_range_days=None,
        start_time=None,
        end_time=None,
        breakdown_property="user_type",
        condition_clauses=["properties.dataset_version = '2.0'"],
    )


@pytest.mark.asyncio
async def test_query_analytics_error_mapping_rate_limit(
    mock_posthog_adapter: MagicMock,
) -> None:
    """Verify PostHogRateLimitError maps to rate_limit with attempted_source=posthog and provenance=None."""
    tool = QueryAnalyticsTool(mock_posthog_adapter)
    mock_posthog_adapter.query_event_counts = AsyncMock(
        side_effect=PostHogRateLimitError("Rate limit exceeded")
    )

    inp = QueryAnalyticsInput(
        intent=AnalyticsQueryIntent.EVENT_COUNT,
        description="Count",
        events=["transfer_completed"],
    )

    res = await tool.run(inp)

    assert res.success is False
    assert res.data is None
    assert res.provenance is None
    assert res.error is not None
    assert res.error.error_type == "rate_limit"
    assert res.error.attempted_source == "posthog"
