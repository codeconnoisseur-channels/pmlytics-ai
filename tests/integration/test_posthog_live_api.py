"""Live integration smoke and scenario tests for PostHog API.

These tests are environment-gated: they execute against a live PostHog project
only when POSTHOG_API_KEY (Personal API key, starts with phx_) and POSTHOG_PROJECT_ID
are present in the environment or .env file.
"""

import os
from typing import Any

import pytest
from app.config.settings import Settings
from app.domain.analytics import AnalyticsQueryResult
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.client import PostHogClient

settings = Settings()
LIVE_API_KEY = os.getenv("POSTHOG_API_KEY") or settings.posthog_api_key
LIVE_PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID") or settings.posthog_project_id
LIVE_HOST = os.getenv("POSTHOG_HOST") or settings.posthog_host
ACTIVE_DATASET = [f"properties.dataset_version = '{settings.demo_dataset_version}'"]

pytestmark = pytest.mark.skipif(
    not LIVE_API_KEY or not LIVE_PROJECT_ID,
    reason="Live PostHog credentials not configured (POSTHOG_API_KEY [phx_...] or POSTHOG_PROJECT_ID missing)",
)


@pytest.fixture
def live_adapter() -> PostHogAdapter:
    client = PostHogClient(
        host=LIVE_HOST,
        project_id=LIVE_PROJECT_ID,
        api_key=LIVE_API_KEY,
        timeout_seconds=35.0,
    )
    return PostHogAdapter(client)


@pytest.mark.asyncio
async def test_live_posthog_query_smoke(live_adapter: PostHogAdapter) -> None:
    """Smoke test verifying live query execution against the designated PostHog project."""
    result = await live_adapter.execute_query(
        "SELECT count() FROM events",
        query_description="Live smoke test: count total events",
        metric="total_events",
    )
    assert isinstance(result, AnalyticsQueryResult)
    assert result.metric == "total_events"
    assert result.raw_count >= 1
    total_events = int(result.rows[0]["count()"])
    assert total_events >= 10000, f"Expected >= 10,000 ingested events, found {total_events}"


@pytest.mark.asyncio
async def test_live_scenario_a_transfer_delays(live_adapter: PostHogAdapter) -> None:
    """Live verification of Scenario A: Bank A/B transfer latency is elevated while failure rate is stable."""
    # 1. Failure rate
    fail_res = await live_adapter.query_event_counts(
        ["transfer_completed", "transfer_failed"],
        start_time="2026-08-10T08:00:00Z",
        end_time="2026-08-15T20:00:00Z",
        condition_clauses=ACTIVE_DATASET,
    )
    fail_dict: dict[str, int] = {r["event"]: int(r["count()"]) for r in fail_res.rows}
    total = fail_dict.get("transfer_completed", 0) + fail_dict.get("transfer_failed", 0)
    assert total > 0
    fail_rate = fail_dict.get("transfer_failed", 0) / total
    assert fail_rate < 0.03, f"Expected live failure rate < 3%, got {fail_rate:.2%}"

    # 2. Duration distribution during the incident window (Aug 10 - Aug 15)
    dur_res = await live_adapter.query_lifecycle_duration(
        event="transfer_completed",
        duration_property="duration_ms",
        breakdown_property="destination_bank",
        start_time="2026-08-10T08:00:00Z",
        end_time="2026-08-15T20:00:00Z",
        condition_clauses=ACTIVE_DATASET,
    )
    dur_rows: dict[str, dict[str, Any]] = {r["destination_bank"]: r for r in dur_res.rows}
    # Bank A and Bank B have high p95/median duration (>45,000ms)
    assert float(dur_rows["Bank A"]["p95_duration"]) > 45000
    assert float(dur_rows["Bank B"]["p95_duration"]) > 45000
    # Normal banks have low duration (<=5,000ms)
    assert float(dur_rows["Bank C"]["p95_duration"]) <= 10000
    assert float(dur_rows["Bank D"]["p95_duration"]) <= 10000


@pytest.mark.asyncio
async def test_live_scenario_b_kyc_funnel(live_adapter: PostHogAdapter) -> None:
    """Live verification of Scenario B: KYC drop-off is concentrated pre-submission."""
    funnel_res = await live_adapter.query_funnel(
        steps=["kyc_started", "kyc_document_submitted", "kyc_completed"],
        start_time="2026-08-01T00:00:00Z",
        end_time="2026-08-20T23:59:59Z",
        condition_clauses=ACTIVE_DATASET,
    )
    rows: dict[str, int] = {r["event"]: int(r["unique_users"]) for r in funnel_res.rows}
    started = rows.get("kyc_started", 0)
    submitted = rows.get("kyc_document_submitted", 0)
    completed = rows.get("kyc_completed", 0)

    assert started > 0 and submitted > 0
    pre_sub_drop = (started - submitted) / started
    post_sub_conv = completed / submitted

    assert pre_sub_drop > 0.40, f"Expected pre-submission drop > 40%, got {pre_sub_drop:.2%}"
    assert post_sub_conv > 0.80, f"Expected post-submission conv > 80%, got {post_sub_conv:.2%}"


@pytest.mark.asyncio
async def test_live_scenario_c_wallet_funding(live_adapter: PostHogAdapter) -> None:
    """Live verification of Scenario C: Wallet funding >= ₦50k drops off with zero failures."""
    # Zero failures
    fail_res = await live_adapter.query_event_counts(
        ["wallet_funding_failed"],
        start_time="2026-08-05T00:00:00Z",
        end_time="2026-08-18T23:59:59Z",
        condition_clauses=ACTIVE_DATASET,
    )
    wf_failed = sum(
        int(r["count()"]) for r in fail_res.rows if r.get("event") == "wallet_funding_failed"
    )
    assert wf_failed == 0, f"Expected 0 wallet_funding_failed events, found {wf_failed}"


@pytest.mark.asyncio
async def test_live_scenario_d_electricity_bill_spike(live_adapter: PostHogAdapter) -> None:
    """Live verification of Scenario D: Acute electricity bill payment failure spike."""
    breakdown_res = await live_adapter.query_breakdown(
        event="bill_payment_failed",
        property_name="category",
        start_time="2026-08-28T14:00:00Z",
        end_time="2026-08-31T02:00:00Z",
        condition_clauses=ACTIVE_DATASET,
    )
    cat_counts: dict[str, int] = {r["category"]: int(r["count()"]) for r in breakdown_res.rows}
    assert cat_counts.get("electricity", 0) > 10, (
        "Expected electricity failures during incident window"
    )
    # Other categories have zero or negligible failures
    assert cat_counts.get("cable_tv", 0) < 5
    assert cat_counts.get("airtime", 0) < 5
