"""Seed configuration for Scenario A: Transfer Status Delays."""

from seed.scenarios.schema import (
    InjectionTimeline,
    JiraSeedIssue,
    ScenarioSeedConfig,
    SegmentConstraint,
)

TRANSFER_DELAYS_SEED_CONFIG = ScenarioSeedConfig(
    scenario_id="scenario_a_transfer_delays",
    name="Transfer Status Delays",
    target_tickets_count=25,
    target_events_count=1500,
    jira_issues=[
        JiraSeedIssue(
            key="PAY-117",
            summary="Intermittent webhook callback delays on partner switch for Bank A and B",
            description=(
                "Downstream switch API accepts transactions with HTTP 202 Accepted, but callback "
                "webhook delivery latency exceeds 45,000ms. Status reconciliation workers queue up, "
                "leaving transactions in processing state until manual or cron poll resolves them."
            ),
            issue_type="Bug",
            status="In Progress",
            priority="High",
            components=["transfer-gateway", "switch-connector"],
            comments=[
                (
                    "Switch partner confirmed queue congestion on their NIP gateway for Bank A and B. "
                    "Transactions eventually settle, but status callbacks are delayed by 2-4 hours."
                ),
                (
                    "Workaround script deployed to poll status every 30 minutes, but real-time status "
                    "remains delayed."
                ),
            ],
        )
    ],
    injection_timeline=InjectionTimeline(
        start_time_iso="2026-08-10T08:00:00Z",
        end_time_iso="2026-08-15T20:00:00Z",
        jira_logged_offset_hours=1.0,
        analytics_degradation_offset_hours=2.0,
        ticket_spike_offset_hours=4.0,
    ),
    target_segment=SegmentConstraint(
        destination_bank="Bank A",
        app_version="2.4.1",
    ),
    noise_ratio=0.25,
)
