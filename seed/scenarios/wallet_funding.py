"""Seed configuration for Scenario C: Wallet Funding Abandonment."""

from seed.scenarios.schema import (
    InjectionTimeline,
    ScenarioSeedConfig,
    SegmentConstraint,
)

WALLET_FUNDING_SEED_CONFIG = ScenarioSeedConfig(
    scenario_id="scenario_c_wallet_funding",
    name="Wallet Funding Abandonment",
    target_tickets_count=8,
    target_events_count=1200,
    jira_issues=[],  # Deliberately empty: no active technical incident or bug exists
    injection_timeline=InjectionTimeline(
        start_time_iso="2026-08-05T00:00:00Z",
        end_time_iso="2026-08-18T23:59:59Z",
        jira_logged_offset_hours=0.0,
        analytics_degradation_offset_hours=0.0,
        ticket_spike_offset_hours=72.0,
    ),
    target_segment=SegmentConstraint(
        amount_brackets=["50k-200k", ">=200k"],  # Fee threshold at >= NGN 50,000
    ),
    noise_ratio=0.20,
)
