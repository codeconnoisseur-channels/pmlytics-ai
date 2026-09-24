"""Seed configuration for Scenario D: Bill Payment Failure."""

from seed.scenarios.schema import (
    InjectionTimeline,
    JiraSeedIssue,
    ScenarioSeedConfig,
    SegmentConstraint,
)

BILL_PAYMENT_SEED_CONFIG = ScenarioSeedConfig(
    scenario_id="scenario_d_bill_payment",
    name="Bill Payment Failure",
    target_tickets_count=30,
    target_events_count=1000,
    jira_issues=[
        JiraSeedIssue(
            key="PAY-134",
            summary="Electricity token purchases timing out during month-end settlement",
            description=(
                "Electricity token purchases are timing out during the month-end settlement period. "
                "Some customers see a debit before their token is available, requiring reconciliation."
            ),
            issue_type="Incident",
            status="In Progress",
            priority="Critical",
            components=["bill-payment-service", "vendor-disco-gateway"],
            comments=[
                "Incident opened at 08:30 UTC. Aggregator confirmed database deadlock on their prepaid service.",
                "Escalated to vendor technical account team. Awaiting estimated time of resolution.",
            ],
        )
    ],
    injection_timeline=InjectionTimeline(
        start_time_iso="2026-08-28T08:00:00Z",
        end_time_iso="2026-08-31T23:00:00Z",
        jira_logged_offset_hours=0.5,
        analytics_degradation_offset_hours=0.0,
        ticket_spike_offset_hours=1.0,
    ),
    target_segment=SegmentConstraint(
        category="electricity",
    ),
    noise_ratio=0.15,
)
