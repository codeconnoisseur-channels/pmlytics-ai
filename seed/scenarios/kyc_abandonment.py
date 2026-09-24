"""Seed configuration for Scenario B: KYC Abandonment."""

from seed.scenarios.schema import (
    InjectionTimeline,
    JiraSeedIssue,
    ScenarioSeedConfig,
    SegmentConstraint,
)

KYC_ABANDONMENT_SEED_CONFIG = ScenarioSeedConfig(
    scenario_id="scenario_b_kyc_abandonment",
    name="KYC Abandonment",
    target_tickets_count=15,
    target_events_count=800,
    jira_issues=[
        JiraSeedIssue(
            key="CORE-82",
            summary="Camera preview ratio distortion on specific Android 12 handsets",
            description=(
                "Users on specific low-end Android 12 devices experience image aspect-ratio "
                "distortion during document camera capture. Affects approximately 1.8% of daily "
                "onboarding sessions."
            ),
            issue_type="Bug",
            status="In Progress",
            priority="Medium",
            components=["mobile-android", "kyc-camera"],
            comments=[
                "Reproduced on Tecno Spark 8 and Infinix Hot 11. Patch submitted to staging.",
                "Telemetry confirms this device bug accounts for < 2% of total KYC starts.",
            ],
        )
    ],
    injection_timeline=InjectionTimeline(
        start_time_iso="2026-08-01T00:00:00Z",
        end_time_iso="2026-08-20T23:59:59Z",
        jira_logged_offset_hours=24.0,
        analytics_degradation_offset_hours=0.0,
        ticket_spike_offset_hours=48.0,
    ),
    target_segment=SegmentConstraint(
        user_type="student",
    ),
    noise_ratio=0.30,
)
