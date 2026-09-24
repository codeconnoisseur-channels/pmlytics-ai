"""Ground truth for Scenario A: Transfer Status Delays."""

from evaluations.scenarios.schema import ScenarioGroundTruth

TRANSFER_DELAYS_GROUND_TRUTH = ScenarioGroundTruth(
    scenario_id="scenario_a_transfer_delays",
    name="Transfer Status Delays",
    product_area="Transfers",
    underlying_reality=(
        "Partner switch callback webhooks for Bank A and Bank B experience high latency (>45s), "
        "causing transfer status updates to hang in processing. Transactions actually settle "
        "successfully, but in-app status updates lag by hours."
    ),
    required_evidence_sources=["zendesk", "posthog", "jira"],
    expected_findings=[
        "Customer complaints cite transfers stuck in pending state for hours.",
        "PostHog funnel reflects processing latency and delayed completion within the standard 60-second window.",
        "Jira issue PAY-117 confirms webhook callback timeouts on the partner switch for Bank A and B.",
    ],
    contradictory_evidence=[
        "Actual transfer failure rate in PostHog is stable and low (~1.2%).",
    ],
    known_traps=[
        "Customers use 'failed' in support tickets to describe transactions that are actually pending.",
        "Assuming that all banks are affected when the issue is concentrated in Bank A and Bank B.",
    ],
    acceptable_conclusions=[
        (
            "Transfer-status synchronization reliability is the primary problem rather than an "
            "actual increase in transfer settlement failures."
        ),
        (
            "Customers perceive delayed transactions as failed due to delayed status webhooks "
            "affecting Bank A and Bank B."
        ),
    ],
    unacceptable_conclusions=[
        "Payment failures have dramatically increased across the platform.",
        "All banks are experiencing identical infrastructure breakdown.",
        "The problem is solely a user frontend UI bug without backend partner delay.",
    ],
    expected_recommendation_type="prioritise",
    expected_product_interpretation=(
        "Prioritise transfer status synchronisation, callback reconciliation, and customer "
        "reassurance messaging rather than treating payment execution as the broken element."
    ),
)
