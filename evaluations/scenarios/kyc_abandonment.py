"""Ground truth for Scenario B: KYC Abandonment."""

from evaluations.scenarios.schema import ScenarioGroundTruth

KYC_ABANDONMENT_GROUND_TRUTH = ScenarioGroundTruth(
    scenario_id="scenario_b_kyc_abandonment",
    name="KYC Abandonment",
    product_area="Onboarding / KYC",
    underlying_reality=(
        "High KYC drop-off is driven by UX friction and ambiguity around acceptable student/freelancer "
        "identification documents. An open camera aspect-ratio crash bug (CORE-82) affects < 2% of "
        "devices and accounts for only a minor fraction of the overall drop-off."
    ),
    required_evidence_sources=["zendesk", "posthog", "jira"],
    expected_findings=[
        "Support tickets inquire about rejected student IDs and unreadable document errors.",
        "PostHog funnel indicates drop-off occurs between kyc_started and kyc_document_submitted, skewed to students.",
        "Jira issue CORE-82 documents a camera crash affecting only 1.8% of daily sessions.",
    ],
    contradictory_evidence=[
        "Device and OS distribution in PostHog indicates >98% of dropping-off users never encounter CORE-82.",
    ],
    known_traps=[
        "Concluding that fixing Jira CORE-82 will resolve the KYC abandonment problem.",
        "Treating the drop-off as purely a technical stability defect.",
    ],
    acceptable_conclusions=[
        (
            "KYC abandonment is primarily driven by onboarding friction and document confusion among "
            "students/freelancers; technical defects explain only a small fraction."
        ),
        (
            "Technical bugs contribute marginally (<2%), but UX and document guidelines require "
            "comprehensive overhaul."
        ),
    ],
    unacceptable_conclusions=[
        "CORE-82 is the sole or primary root cause of KYC abandonment.",
        "Document capture technology is fundamentally non-functional across the entire user base.",
    ],
    expected_recommendation_type="experiment",
    expected_product_interpretation=(
        "Run product UX experiments on document requirements and validation guidance, while treating "
        "the Android camera bug as an independent minor fix."
    ),
)
