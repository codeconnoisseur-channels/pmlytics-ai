"""Ground truth for Scenario D: Bill Payment Failure."""

from evaluations.scenarios.schema import ScenarioGroundTruth

BILL_PAYMENT_GROUND_TRUTH = ScenarioGroundTruth(
    scenario_id="scenario_d_bill_payment",
    name="Bill Payment Failure",
    product_area="Bills",
    underlying_reality=(
        "Authentic third-party API outage with the electricity token aggregator returning HTTP 502 "
        "Bad Gateway. All other utility bill categories are completely unaffected."
    ),
    required_evidence_sources=["zendesk", "posthog", "jira"],
    expected_findings=[
        "Support tickets surge with complaints of debited funds without prepaid electricity meter tokens.",
        "PostHog reflects an acute spike in bill_payment_failed specifically for category: electricity.",
        "Jira PAY-134 confirms an active Critical incident with vendor 502 Bad Gateway responses.",
    ],
    contradictory_evidence=[
        "Airtime, Cable TV, and Internet bill categories exhibit normal 99%+ completion rates.",
    ],
    known_traps=[
        "Looking only at aggregate bill payment conversion, which masks the electricity outage.",
        "Failing to recognize that other utility categories are healthy.",
    ],
    acceptable_conclusions=[
        (
            "Electricity bill payment failures are driven by a verified third-party vendor outage "
            "tracked in PAY-134, while general bill payments remain functional."
        ),
        (
            "Evidence converges across support, analytics, and Jira showing a critical partner "
            "integration breakdown isolated to the electricity category."
        ),
    ],
    unacceptable_conclusions=[
        "All bill payment categories are broken across the entire platform.",
        "The issue is user balance inadequacy rather than an upstream vendor failure.",
    ],
    expected_recommendation_type="technical_remediation",
    expected_product_interpretation=(
        "Immediately pursue technical remediation and upstream vendor escalation, while disabling "
        "or placing an in-app maintenance warning on electricity bill purchases."
    ),
)
