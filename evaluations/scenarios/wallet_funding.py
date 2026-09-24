"""Ground truth for Scenario C: Wallet Funding Abandonment."""

from evaluations.scenarios.schema import ScenarioGroundTruth

WALLET_FUNDING_GROUND_TRUTH = ScenarioGroundTruth(
    scenario_id="scenario_c_wallet_funding",
    name="Wallet Funding Abandonment",
    product_area="Wallet",
    underlying_reality=(
        "Users frequently abandon wallet funding due to surprise fee disclosure on transactions "
        ">= ₦50,000, not technical outages. There is zero engineering incident or bug."
    ),
    required_evidence_sources=["zendesk", "posthog", "jira"],
    expected_findings=[
        "Support tickets contain minor inquiries/complaints regarding funding gateway charges.",
        "PostHog funnel shows drop between wallet_funding_started and submitted on brackets >= ₦50,000.",
        "Jira shows zero open issues or incidents for wallet funding infrastructure.",
    ],
    contradictory_evidence=[
        "Engineering systems show 100% operational uptime and no related error logs.",
    ],
    known_traps=[
        "Concluding that low support ticket volume means no problem exists.",
        "Assuming funding failure is due to a payment gateway outage despite zero error events.",
    ],
    acceptable_conclusions=[
        (
            "Funding abandonment is a commercial/pricing and user-friction issue concentrated in "
            "higher transaction brackets, rather than a technical failure."
        ),
        (
            "Lack of engineering defects indicates fee transparency and UX hesitation cause the "
            "drop between start and submission."
        ),
    ],
    unacceptable_conclusions=[
        "Wallet funding infrastructure is experiencing an outage.",
        "Engineers need to urgently fix a broken payment switch.",
    ],
    expected_recommendation_type="investigate_further",
    expected_product_interpretation=(
        "Investigate user pricing expectations and fee disclosure UX rather than raising an "
        "engineering escalation."
    ),
)
