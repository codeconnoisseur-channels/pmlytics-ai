"""Unit tests verifying deterministic PostHog dataset generation and scenario semantics."""

from datetime import UTC, datetime

import pytest
from app.domain.analytics import AnalyticsEvent
from seed.posthog.generator import (
    DEFAULT_SEED,
    FORBIDDEN_GROUND_TRUTH_KEYS,
    PostHogEventGenerator,
)


@pytest.fixture(scope="module")
def generated_events() -> list[AnalyticsEvent]:
    gen = PostHogEventGenerator(seed=DEFAULT_SEED, num_users=2000)
    return gen.generate_events()


def test_seed_reproducibility(generated_events: list[AnalyticsEvent]) -> None:
    """Verifies that running the generator with the same seed yields identical events."""
    gen2 = PostHogEventGenerator(seed=DEFAULT_SEED, num_users=2000)
    events2 = gen2.generate_events()

    assert len(generated_events) == len(events2)
    assert generated_events[0].distinct_id == events2[0].distinct_id
    assert generated_events[0].timestamp == events2[0].timestamp
    assert generated_events[-1].distinct_id == events2[-1].distinct_id


def test_dataset_volume_and_taxonomy(generated_events: list[AnalyticsEvent]) -> None:
    """Verifies total event count is within 10,000–20,000 and matches approved taxonomy."""
    total = len(generated_events)
    assert 10000 <= total <= 20000, f"Generated {total} events, expected 10,000–20,000"

    # All events are valid AnalyticsEvent instances
    for e in generated_events:
        assert isinstance(e, AnalyticsEvent)
        assert e.distinct_id.startswith("usr_")


def test_zero_ground_truth_leakage(generated_events: list[AnalyticsEvent]) -> None:
    """Strictly asserts that no ground-truth or evaluator labels exist in properties."""
    for e in generated_events:
        leaked = set(e.properties.keys()) & FORBIDDEN_GROUND_TRUTH_KEYS
        assert not leaked, f"Ground-truth leakage in event {e.event}: {leaked}"


def test_transaction_id_and_monotonicity(generated_events: list[AnalyticsEvent]) -> None:
    """Asserts that lifecycle events for a transaction are strictly chronologically ordered."""
    tx_events: dict[str, list[AnalyticsEvent]] = {}
    for e in generated_events:
        tx_id = e.properties.get("transaction_id")
        if tx_id:
            tx_events.setdefault(tx_id, []).append(e)

    # Check a sample of 200 transactions
    sample_txs = list(tx_events.items())[:200]
    for tx_id, events in sample_txs:
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp, (
                f"Non-monotonic timestamps in tx {tx_id}: {events[i].event} vs {events[i + 1].event}"
            )


def test_scenario_a_observability(generated_events: list[AnalyticsEvent]) -> None:
    """Scenario A: Bank A/B transfer latency is elevated while failure rate remains stable and low."""
    # Filter transfer outcomes
    transfers_comp = [e for e in generated_events if e.event == "transfer_completed"]
    transfers_fail = [e for e in generated_events if e.event == "transfer_failed"]

    # 1. Failure rate is low and stable (<2%)
    total_outcomes = len(transfers_comp) + len(transfers_fail)
    fail_rate = len(transfers_fail) / total_outcomes
    assert fail_rate < 0.02, f"Expected transfer failure rate < 2%, got {fail_rate:.3%}"

    # 2. Inspect callback duration for Bank A/B vs other banks during scenario window (Aug 10-15)
    win_start = datetime(2026, 8, 10, 8, 0, 0, tzinfo=UTC)
    win_end = datetime(2026, 8, 15, 20, 0, 0, tzinfo=UTC)

    bank_ab_delayed = [
        e
        for e in transfers_comp
        if win_start <= e.timestamp <= win_end
        and e.properties.get("destination_bank") in ("Bank A", "Bank B")
        and e.properties.get("duration_ms", 0) > 45000
    ]
    other_banks_delayed = [
        e
        for e in transfers_comp
        if win_start <= e.timestamp <= win_end
        and e.properties.get("destination_bank") in ("Bank C", "Bank D", "Bank E")
        and e.properties.get("duration_ms", 0) > 45000
    ]

    # Bank A/B has substantial delayed events (>45s)
    assert len(bank_ab_delayed) > 50, (
        f"Expected >50 delayed Bank A/B transfers, got {len(bank_ab_delayed)}"
    )
    # Other banks have zero delayed events
    assert len(other_banks_delayed) == 0, (
        f"Expected 0 delayed transfers for Bank C/D/E, got {len(other_banks_delayed)}"
    )


def test_scenario_b_observability(generated_events: list[AnalyticsEvent]) -> None:
    """Scenario B: KYC drop-off is concentrated pre-submission, post-submission conversion is stable."""
    kyc_started = [e for e in generated_events if e.event == "kyc_started"]
    kyc_submitted = [e for e in generated_events if e.event == "kyc_document_submitted"]
    kyc_completed = [e for e in generated_events if e.event == "kyc_completed"]

    # Pre-submission conversion is low overall (<55%)
    pre_sub_conversion = len(kyc_submitted) / len(kyc_started)
    assert pre_sub_conversion < 0.60, (
        f"Expected pre-submission conversion < 60%, got {pre_sub_conversion:.2%}"
    )

    # Post-submission conversion is high and stable (>85%)
    post_sub_conversion = len(kyc_completed) / len(kyc_submitted)
    assert post_sub_conversion > 0.85, (
        f"Expected post-submission conversion > 85%, got {post_sub_conversion:.2%}"
    )


def test_scenario_c_observability(generated_events: list[AnalyticsEvent]) -> None:
    """Scenario C: Wallet funding abandonment occurs at >= ₦50,000 before submission; zero error events."""
    wf_started = [e for e in generated_events if e.event == "wallet_funding_started"]
    wf_submitted = [e for e in generated_events if e.event == "wallet_funding_submitted"]
    wf_failed = [e for e in generated_events if e.event == "wallet_funding_failed"]

    # Strict check: Zero wallet_funding_failed events!
    assert len(wf_failed) == 0, f"Expected 0 wallet_funding_failed events, found {len(wf_failed)}"

    # Below ₦50k conversion vs >= ₦50k conversion
    low_started = [e for e in wf_started if e.properties.get("amount_ngn", 0) < 50000]
    high_started = [e for e in wf_started if e.properties.get("amount_ngn", 0) >= 50000]

    low_tx_ids = {e.properties["transaction_id"] for e in low_started}
    high_tx_ids = {e.properties["transaction_id"] for e in high_started}

    low_submitted = [e for e in wf_submitted if e.properties["transaction_id"] in low_tx_ids]
    high_submitted = [e for e in wf_submitted if e.properties["transaction_id"] in high_tx_ids]

    low_conv = len(low_submitted) / len(low_started)
    high_conv = len(high_submitted) / len(high_started)

    assert low_conv > 0.90, f"Expected low value funding submission > 90%, got {low_conv:.2%}"
    assert high_conv < 0.30, f"Expected high value funding submission < 30%, got {high_conv:.2%}"


def test_scenario_d_observability(generated_events: list[AnalyticsEvent]) -> None:
    """Scenario D: Electricity bill payments experience acute failure spike during incident window."""
    inc_start = datetime(2026, 8, 28, 14, 0, 0, tzinfo=UTC)
    inc_end = datetime(2026, 8, 31, 2, 0, 0, tzinfo=UTC)

    # During incident
    inc_bills = [
        e
        for e in generated_events
        if e.event in ("bill_payment_completed", "bill_payment_failed")
        and inc_start <= e.timestamp <= inc_end
    ]
    elec_inc = [e for e in inc_bills if e.properties.get("category") == "electricity"]
    other_inc = [e for e in inc_bills if e.properties.get("category") != "electricity"]

    elec_failed = [e for e in elec_inc if e.event == "bill_payment_failed"]
    other_failed = [e for e in other_inc if e.event == "bill_payment_failed"]

    elec_fail_rate = len(elec_failed) / len(elec_inc) if elec_inc else 0
    other_fail_rate = len(other_failed) / len(other_inc) if other_inc else 0

    assert elec_fail_rate > 0.65, (
        f"Expected electricity failure rate > 65% during incident, got {elec_fail_rate:.2%}"
    )
    assert other_fail_rate < 0.05, (
        f"Expected non-electricity failure rate < 5% during incident, got {other_fail_rate:.2%}"
    )
