"""Integration contract tests verifying end-to-end analytical querying for Scenarios A-D.

Uses respx to simulate realistic PostHog HogQL API responses and verifies that the
PostHogAdapter produces structured domain results allowing accurate product investigation.
"""

import pytest
import respx
from app.domain.analytics import AnalyticsQueryResult
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.client import PostHogClient

HOST = "https://us.posthog.com"
PROJECT_ID = "pocket-analytics-test"
API_KEY = "phx_test_contract_token"
QUERY_URL = f"{HOST}/api/projects/{PROJECT_ID}/query/"


@pytest.fixture
def adapter() -> PostHogAdapter:
    client = PostHogClient(host=HOST, project_id=PROJECT_ID, api_key=API_KEY)
    return PostHogAdapter(client)


@pytest.mark.asyncio
async def test_contract_scenario_a_transfer_delays(adapter: PostHogAdapter) -> None:
    """Scenario A: Demonstrates that Bank A/B transfer latency is elevated while failures remain low."""
    # 1. Query failure rate
    mock_fail_response = {
        "columns": ["event", "count()"],
        "types": ["String", "UInt64"],
        "results": [
            ["transfer_completed", 4800],
            ["transfer_failed", 58],
        ],
    }
    # 2. Query duration distribution across banks
    mock_duration_response = {
        "columns": [
            "destination_bank",
            "count()",
            "avg_duration",
            "median_duration",
            "p95_duration",
        ],
        "types": ["String", "UInt64", "Float64", "Float64", "Float64"],
        "results": [
            ["Bank A", 950, 7200000.0, 5400000.0, 14400000.0],
            ["Bank B", 940, 6800000.0, 5100000.0, 14000000.0],
            ["Bank C", 960, 3200.0, 3000.0, 4500.0],
            ["Bank D", 970, 3100.0, 2900.0, 4400.0],
            ["Bank E", 980, 3300.0, 3100.0, 4600.0],
        ],
    }

    with respx.mock:
        respx.post(QUERY_URL).mock(
            side_effect=[
                respx.MockResponse(200, json=mock_fail_response),
                respx.MockResponse(200, json=mock_duration_response),
            ]
        )

        # Query 1: Outcomes
        fail_res = await adapter.query_event_counts(["transfer_completed", "transfer_failed"])
        assert isinstance(fail_res, AnalyticsQueryResult)
        fail_dict = {row["event"]: row["count()"] for row in fail_res.rows}
        total = fail_dict["transfer_completed"] + fail_dict["transfer_failed"]
        failure_rate = fail_dict["transfer_failed"] / total
        # Failure rate is stable & low (~1.2%)
        assert failure_rate < 0.02

        # Query 2: Duration breakdown
        dur_res = await adapter.query_lifecycle_duration(
            event="transfer_completed",
            duration_property="duration_ms",
            breakdown_property="destination_bank",
        )
        assert isinstance(dur_res, AnalyticsQueryResult)
        dur_rows = {r["destination_bank"]: r for r in dur_res.rows}

        # Bank A & Bank B median duration is in the millions of ms (>45s)
        assert dur_rows["Bank A"]["median_duration"] > 45000
        assert dur_rows["Bank B"]["median_duration"] > 45000
        # Normal banks median duration is ~3000ms
        assert dur_rows["Bank C"]["median_duration"] < 5000


@pytest.mark.asyncio
async def test_contract_scenario_b_kyc_funnel(adapter: PostHogAdapter) -> None:
    """Scenario B: Demonstrates that KYC drop-off is concentrated before document submission."""
    mock_funnel_response = {
        "columns": ["event", "unique_users", "total_events"],
        "types": ["String", "UInt64", "UInt64"],
        "results": [
            ["kyc_started", 1500, 1500],
            ["kyc_document_submitted", 650, 650],
            ["kyc_completed", 600, 600],
        ],
    }

    with respx.mock:
        respx.post(QUERY_URL).respond(200, json=mock_funnel_response)
        funnel_res = await adapter.query_funnel(
            steps=["kyc_started", "kyc_document_submitted", "kyc_completed"]
        )

        rows = {r["event"]: r["unique_users"] for r in funnel_res.rows}
        started = rows["kyc_started"]
        submitted = rows["kyc_document_submitted"]
        completed = rows["kyc_completed"]

        # Drop-off from started to submitted is high (>50%)
        pre_sub_drop = (started - submitted) / started
        assert pre_sub_drop > 0.50

        # Conversion from submitted to completed is high (>90%)
        post_sub_conv = completed / submitted
        assert post_sub_conv > 0.90


@pytest.mark.asyncio
async def test_contract_scenario_c_wallet_funding_abandonment(adapter: PostHogAdapter) -> None:
    """Scenario C: Demonstrates wallet funding drop-off for amounts >= ₦50,000 without errors."""
    mock_response = {
        "columns": ["amount_bracket", "event", "unique_users"],
        "types": ["String", "String", "UInt64"],
        "results": [
            ["<50k", "wallet_funding_started", 700],
            ["<50k", "wallet_funding_submitted", 670],
            [">=50k", "wallet_funding_started", 700],
            [">=50k", "wallet_funding_submitted", 140],
        ],
    }

    with respx.mock:
        respx.post(QUERY_URL).respond(200, json=mock_response)
        res = await adapter.query_funnel(
            steps=["wallet_funding_started", "wallet_funding_submitted"],
            breakdown_property="amount_bracket",
        )

        rows_low = [r for r in res.rows if r["amount_bracket"] == "<50k"]
        rows_high = [r for r in res.rows if r["amount_bracket"] == ">=50k"]

        low_conv = next(
            r["unique_users"] for r in rows_low if r["event"] == "wallet_funding_submitted"
        ) / next(r["unique_users"] for r in rows_low if r["event"] == "wallet_funding_started")
        high_conv = next(
            r["unique_users"] for r in rows_high if r["event"] == "wallet_funding_submitted"
        ) / next(r["unique_users"] for r in rows_high if r["event"] == "wallet_funding_started")

        assert low_conv > 0.90
        assert high_conv < 0.25


@pytest.mark.asyncio
async def test_contract_scenario_d_electricity_bill_failure_spike(adapter: PostHogAdapter) -> None:
    """Scenario D: Demonstrates acute electricity-specific failure spike."""
    mock_breakdown = {
        "columns": ["category", "count()"],
        "types": ["String", "UInt64"],
        "results": [
            ["electricity", 120],
            ["cable_tv", 2],
            ["airtime", 1],
            ["internet", 1],
        ],
    }

    with respx.mock:
        respx.post(QUERY_URL).respond(200, json=mock_breakdown)
        res = await adapter.query_breakdown(
            event="bill_payment_failed",
            property_name="category",
            start_time="2026-08-12T14:00:00Z",
            end_time="2026-08-13T02:00:00Z",
        )

        rows = {r["category"]: r["count()"] for r in res.rows}
        assert rows["electricity"] > 100
        assert rows["cable_tv"] < 5
        assert rows["airtime"] < 5
        assert rows["internet"] < 5
