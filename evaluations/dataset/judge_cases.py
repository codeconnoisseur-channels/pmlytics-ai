"""Authoritative 20-case dataset for LLM-as-Judge calibration and frozen validation.

Partition:
- 10 Development/Calibration cases: used exclusively for judge prompt and rubric calibration.
- 10 Independent Frozen Validation cases: sealed test set for official kappa qualification.
"""

from typing import Literal

from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from pydantic import BaseModel, ConfigDict, Field


class JudgeCase(BaseModel):
    """A human-annotated SUT run evaluation case for LLM judge calibration and validation."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    split: Literal["dev_calibration", "frozen_validation"]
    scenario_id: str
    product_area: str
    archetype: str
    user_query: str
    sut_recommendation: ProductRecommendation
    human_ground_truth_scores: dict[str, int] = Field(
        ...,
        description="Human gold ratings (0-4) across: groundedness, cross_source_reasoning, contradiction_handling, causal_discipline, recommendation_defensibility",
    )
    human_gold_rationale: dict[str, str] = Field(default_factory=dict)


def _make_evidence(
    ledger_id: str, source_type: Literal["zendesk", "posthog", "jira"], ref: str, finding: str
) -> Evidence:
    return Evidence(
        ledger_entry_id=ledger_id,
        source_type=source_type,
        source_reference=ref,
        finding=finding,
        support=f"Support excerpt from {ref}",
        confidence=EvidenceConfidence.HIGH,
    )


# -----------------------------------------------------------------------------
# 10 DEVELOPMENT / CALIBRATION CASES (dev_calibration)
# -----------------------------------------------------------------------------
DEV_CALIBRATION_CASES: list[JudgeCase] = [
    JudgeCase(
        case_id="judge_dev_01",
        split="dev_calibration",
        scenario_id="scn_001",
        product_area="Transfers",
        archetype="diagnostic",
        user_query="Why are customers reporting a surge in failed transfers this week?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Partner switch callback timeouts causing perceived transfer failures.",
            why_it_matters="High customer anxiety and surge in support tickets.",
            affected_users="Bank A and Bank B account holders",
            factual_observations=[
                "Tickets complain of transfers pending for hours.",
                "Telemetry confirms eventual settlement rate is 98.8%.",
                "PAY-117 documents partner switch timeout on status callbacks.",
            ],
            inferences=["Transfers are settling, but status synchronization is delayed."],
            hypotheses=["Fixing switch webhook will eliminate customer transfer delay reports."],
            evidence=[
                _make_evidence(
                    "led_001", "zendesk", "zen_001", "Customer reports pending transfer"
                ),
                _make_evidence(
                    "led_002", "posthog", "query_latency", "p95 latency > 45s, success rate 98.8%"
                ),
                _make_evidence("led_003", "jira", "PAY-117", "Partner switch webhook timeout bug"),
            ],
            recommendation="Deploy partner switch timeout fix and add pending status banner in UI.",
            recommendation_type="technical_remediation",
            success_metrics=["Support ticket volume reduction", "p95 status sync latency < 5s"],
            risks=["Downstream partner API disruption during patch release"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 4,
            "causal_discipline": 3,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Fully grounded in cited tickets, telemetry, and Jira issue.",
            "cross_source_reasoning": "Synthesizes customer complaints with telemetry and Jira bug.",
            "contradiction_handling": "Accurately reconciles customer failure perception with actual 98.8% settlement.",
            "causal_discipline": "Appropriate attribution to partner switch timeout.",
            "recommendation_defensibility": "Defensible dual technical fix and UI banner.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_02",
        split="dev_calibration",
        scenario_id="scn_002",
        product_area="Transfers",
        archetype="causality_trap",
        user_query="Did Switch X cause all platform transfer failures?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Switch X caused a complete collapse of all platform payments.",
            why_it_matters="Critical revenue loss.",
            affected_users="All platform users across all banks",
            factual_observations=["Switch X experienced timeouts."],
            inferences=["Therefore Switch X caused every payment failure."],
            hypotheses=["Replacing Switch X will fix 100% of payment issues."],
            evidence=[_make_evidence("led_001", "jira", "PAY-117", "Switch X timeout")],
            recommendation="Immediately terminate partner Switch X contract platform-wide.",
            recommendation_type="investigate_further",
            success_metrics=["Zero payment failures"],
            risks=["Extreme partner disruption without backup switch"],
            confidence="high",  # Gross overconfidence
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 1,
            "cross_source_reasoning": 1,
            "contradiction_handling": 0,
            "causal_discipline": 0,
            "recommendation_defensibility": 1,
        },
        human_gold_rationale={
            "groundedness": "Minimal evidence used to justify broad claims.",
            "cross_source_reasoning": "Failed to synthesize telemetry showing Switch X only affects Bank A/B.",
            "contradiction_handling": "Completely ignored contradictory platform telemetry.",
            "causal_discipline": "Severe causal overreach falling directly into the causality trap.",
            "recommendation_defensibility": "Reckless recommendation to terminate partner contract.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_03",
        split="dev_calibration",
        scenario_id="scn_003",
        product_area="Transfers",
        archetype="segmentation_trap",
        user_query="What user cohort is impacted by transfer processing delays?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Transfer delays selectively impacting Bank A and Bank B accounts.",
            why_it_matters="Customer frustration isolated to specific partner routing.",
            affected_users="Bank A and Bank B account holders",
            factual_observations=[
                "p95 latency is 52s for Bank A and B, but under 2s for Banks C and D."
            ],
            inferences=["Issue is isolated to Bank A and B routing switches."],
            hypotheses=["Partner switch configuration is causing the delay."],
            evidence=[
                _make_evidence("led_001", "posthog", "query_latency", "Latency breakdown by bank")
            ],
            recommendation="Target partner switch routing patch for Banks A and B only.",
            recommendation_type="technical_remediation",
            success_metrics=["Bank A and B p95 latency < 3s"],
            risks=["Temporary rerouting overhead"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 3,
            "contradiction_handling": 3,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Directly grounded in cohort segmentation breakdown.",
            "cross_source_reasoning": "Clear distinction between affected and unaffected cohorts.",
            "contradiction_handling": "Not applicable or adequately managed.",
            "causal_discipline": "Cautious and strictly scoped to Bank A/B.",
            "recommendation_defensibility": "Targeted remediation plan.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_04",
        split="dev_calibration",
        scenario_id="scn_004",
        product_area="Transfers",
        archetype="magnitude_trap",
        user_query="How severe is the transfer fee discrepancy reported by users?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Catastrophic fee overcharging across thousands of daily transfers.",
            why_it_matters="Platform existential legal risk.",
            affected_users="Millions of users",
            factual_observations=["3 customer tickets reported a 2 cent rounding discrepancy."],
            inferences=["The entire billing system is systematically corrupted."],
            hypotheses=["Every user is being overbilled."],
            evidence=[
                _make_evidence("led_001", "zendesk", "zen_104", "3 tickets on 2 cent discrepancy")
            ],
            recommendation="Halt all platform billing and refund all historical fees.",
            recommendation_type="investigate_further",
            success_metrics=["Audit completion"],
            risks=["Total operational shutdown"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 1,
            "cross_source_reasoning": 1,
            "contradiction_handling": 1,
            "causal_discipline": 0,
            "recommendation_defensibility": 0,
        },
        human_gold_rationale={
            "groundedness": "Extrapolates 3 tickets into millions of users.",
            "cross_source_reasoning": "Did not check billing transaction telemetry.",
            "contradiction_handling": "Ignored absence of widespread financial discrepancy.",
            "causal_discipline": "Gross magnitude distortion.",
            "recommendation_defensibility": "Disproportionate and destructive action.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_05",
        split="dev_calibration",
        scenario_id="scn_005",
        product_area="Transfers",
        archetype="contradiction_handling",
        user_query="Are transfers actually failing or just delayed?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Perceived transfer failures contrast with confirmed backend settlement.",
            why_it_matters="Customer anxiety leads to duplicate transfer attempts.",
            affected_users="Users initiating transfers during peak processing windows",
            factual_observations=[
                "Tickets state 'my money is gone and transfer failed'.",
                "Backend ledger shows 99.1% eventual settlement within 30 minutes.",
            ],
            inferences=[
                "Customers assume delay equals failure because UI lacks intermediate progress indicator."
            ],
            hypotheses=["Adding live settlement tracker will reduce perceived failure anxiety."],
            evidence=[
                _make_evidence(
                    "led_001", "zendesk", "zen_005", "Customer tickets claiming failure"
                ),
                _make_evidence(
                    "led_002", "posthog", "query_settlement", "Eventual settlement rate 99.1%"
                ),
            ],
            recommendation="Add real-time progress state in mobile app to bridge the perception gap.",
            recommendation_type="investigate_further",
            success_metrics=["Duplicate transfer attempts drop by 80%"],
            risks=["Mobile client update rollout latency"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 4,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Excellent factual citation across Zendesk and PostHog.",
            "cross_source_reasoning": "Explicit cross-source reconciliation.",
            "contradiction_handling": "Flawless identification of perception vs backend truth contradiction.",
            "causal_discipline": "Carefully articulated causal mechanism.",
            "recommendation_defensibility": "Constructive product improvement addressing root cause.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_06",
        split="dev_calibration",
        scenario_id="scn_013",
        product_area="KYC",
        archetype="diagnostic",
        user_query="Why has the document verification drop-off rate doubled this month?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Document verification drop-off doubled due to uncompressed camera uploads failing timeout.",
            why_it_matters="New user onboarding conversion dropped 14%.",
            affected_users="Android users on high-resolution camera devices",
            factual_observations=[
                "Upload error rate increased to 28% following v4.2 release.",
                "Jira issue KYC-88 documents lack of client-side image compression on Android.",
            ],
            inferences=["High-res images exceed upload payload timeout on mobile data."],
            hypotheses=["Client-side compression before upload will restore conversion rate."],
            evidence=[
                _make_evidence("led_001", "posthog", "query_kyc_dropoff", "Upload error rate 28%"),
                _make_evidence(
                    "led_002", "jira", "KYC-88", "Missing client-side compression on Android"
                ),
            ],
            recommendation="Implement client-side JPEG compression and increase API timeout threshold.",
            recommendation_type="technical_remediation",
            success_metrics=["KYC upload success rate > 95%"],
            risks=["Device CPU load on older Android models"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 3,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Directly grounded in KYC telemetry and engineering ticket.",
            "cross_source_reasoning": "Connects mobile client release to upload failure telemetry.",
            "contradiction_handling": "No material contradictions present.",
            "causal_discipline": "Sound technical explanation.",
            "recommendation_defensibility": "Standard best practice for mobile document capture.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_07",
        split="dev_calibration",
        scenario_id="scn_014",
        product_area="KYC",
        archetype="causality_trap",
        user_query="Did the new OCR provider cause passport verification failures?",
        sut_recommendation=ProductRecommendation(
            problem_statement="New OCR provider is completely defective and caused all verification failures.",
            why_it_matters="Onboarding halted.",
            affected_users="All KYC applicants",
            factual_observations=["Passport verifications failed."],
            inferences=["OCR provider algorithm is broken."],
            hypotheses=["Switching back will fix everything."],
            evidence=[
                _make_evidence("led_001", "zendesk", "zen_014", "User reports rejected passport")
            ],
            recommendation="Immediately roll back OCR vendor integration.",
            recommendation_type="investigate_further",
            success_metrics=["Onboarding recovery"],
            risks=["Contract penalty with new vendor"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 1,
            "cross_source_reasoning": 1,
            "contradiction_handling": 0,
            "causal_discipline": 1,
            "recommendation_defensibility": 1,
        },
        human_gold_rationale={
            "groundedness": "Single ticket cited for broad vendor blame.",
            "cross_source_reasoning": "Omitted telemetry showing passport glare was primary cause.",
            "contradiction_handling": "Ignored OCR success on clean scans.",
            "causal_discipline": "Premature causal attribution.",
            "recommendation_defensibility": "Vendor rollback unjustified by evidence.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_08",
        split="dev_calibration",
        scenario_id="scn_024",
        product_area="Funding",
        archetype="diagnostic",
        user_query="Why are debit card deposits declining while bank transfers increase?",
        sut_recommendation=ProductRecommendation(
            problem_statement="3DS authentication failures on debit cards driving shift to bank transfers.",
            why_it_matters="Debit cards offer instant funding; bank transfers take longer.",
            affected_users="Users depositing via debit card with 3DS v2 issuers",
            factual_observations=[
                "Debit card 3DS challenge failure rate rose from 4% to 22%.",
                "Bank transfer funding volume increased by 35% over same period.",
                "Jira issue FUND-42 identifies deprecated 3DS SDK version.",
            ],
            inferences=["Users encountering repeated 3DS card errors substitute bank transfer."],
            hypotheses=["Upgrading 3DS SDK will recover card deposit conversion."],
            evidence=[
                _make_evidence(
                    "led_001", "posthog", "query_card_3ds", "3DS challenge failure rate 22%"
                ),
                _make_evidence("led_002", "posthog", "query_bank_vol", "Bank transfer volume +35%"),
                _make_evidence("led_003", "jira", "FUND-42", "3DS SDK upgrade required"),
            ],
            recommendation="Upgrade 3DS mobile SDK to v2.2 and add fallback notice.",
            recommendation_type="technical_remediation",
            success_metrics=["3DS failure rate < 5%", "Card deposit volume restored"],
            risks=["Requires app store release review"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 4,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Richly grounded in telemetry and engineering context.",
            "cross_source_reasoning": "Insightful substitution effect explanation.",
            "contradiction_handling": "Reconciles card drop with transfer increase.",
            "causal_discipline": "Accurately attributes behavior to 3DS failure friction.",
            "recommendation_defensibility": "Actionable SDK update roadmap.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_09",
        split="dev_calibration",
        scenario_id="scn_035",
        product_area="Bill Payments",
        archetype="diagnostic",
        user_query="Why are utility bill payments failing with error code BP-404?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Biller directory API schema change caused BP-404 errors for water utility.",
            why_it_matters="Over 400 customers unable to pay water bills before due date.",
            affected_users="Customers paying City Water Utility accounts",
            factual_observations=[
                "BP-404 errors isolated to City Water Utility biller ID 992.",
                "Jira PAY-310 notes utility provider changed account number format from 10 to 12 digits.",
            ],
            inferences=["Pocket app validation rejects 12-digit account numbers as invalid."],
            hypotheses=[
                "Updating client validation regex will resolve 100% of BP-404 errors for this biller."
            ],
            evidence=[
                _make_evidence(
                    "led_001", "posthog", "query_biller_errors", "BP-404 on biller ID 992"
                ),
                _make_evidence(
                    "led_002", "jira", "PAY-310", "City Water changed account digits to 12"
                ),
            ],
            recommendation="Update biller account regex in configuration service and re-enable payments.",
            recommendation_type="technical_remediation",
            success_metrics=["BP-404 error rate returns to 0%"],
            risks=["Potential validation regression for other billers if regex not scoped"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 3,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Specific error codes and biller IDs verified.",
            "cross_source_reasoning": "Connects telemetry error spikes with Jira partner spec change.",
            "contradiction_handling": "No contradictions present.",
            "causal_discipline": "Exact causal chain established.",
            "recommendation_defensibility": "Safe, scoped configuration change.",
        },
    ),
    JudgeCase(
        case_id="judge_dev_10",
        split="dev_calibration",
        scenario_id="scn_007",
        product_area="Transfers",
        archetype="missing_evidence",
        user_query="What caused international transfer delays when Jira and logs are unavailable?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Insufficient evidence to determine root cause of international transfer delays.",
            why_it_matters="Customer complaints received without corresponding technical diagnostics.",
            affected_users="International transfer senders",
            factual_observations=["12 customer tickets report delays on Euro transfers."],
            inferences=["Customer friction exists, but technical root cause cannot be confirmed."],
            hypotheses=["Partner FX liquidity or local clearing delay could explain friction."],
            evidence=[
                _make_evidence(
                    "led_001", "zendesk", "zen_007", "12 customer tickets on Euro transfer"
                )
            ],
            recommendation="Instrument telemetry for international clearing and obtain partner FX logs before action.",
            recommendation_type="investigate_further",
            success_metrics=["Clearing telemetry latency instrumentation deployed"],
            risks=["Premature partner escalation without logs"],
            confidence="low",  # Calibrated low confidence
            open_questions=[
                "What is the partner FX response time?",
                "Did the local clearing switch fail?",
            ],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 3,
            "contradiction_handling": 4,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Strictly limited to available evidence without fabrication.",
            "cross_source_reasoning": "Acknowledges source outage and missing technical data.",
            "contradiction_handling": "Refuses to synthesize uncorroborated conclusion.",
            "causal_discipline": "Exemplary epistemic humility; labels root cause as unknown.",
            "recommendation_defensibility": "Correct recommendation is to investigate further.",
        },
    ),
]


# -----------------------------------------------------------------------------
# 10 INDEPENDENT FROZEN VALIDATION CASES (frozen_validation)
# -----------------------------------------------------------------------------
FROZEN_VALIDATION_CASES: list[JudgeCase] = [
    JudgeCase(
        case_id="judge_val_01",
        split="frozen_validation",
        scenario_id="scn_006",
        product_area="Transfers",
        archetype="diagnostic",
        user_query="Why did automated batch transfers fail at midnight?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Database lock contention during midnight maintenance batch job caused transfer failures.",
            why_it_matters="Scheduled payroll and automated recurring transfers delayed.",
            affected_users="Users with scheduled midnight recurring transfers",
            factual_observations=[
                "Batch transfer failure spike at 00:00 UTC.",
                "Jira DB-22 notes maintenance vacuum ran simultaneously with batch scheduler.",
            ],
            inferences=["Vacuum locked transaction table, causing batch transfer timeouts."],
            hypotheses=["Offsetting maintenance schedule by 1 hour will prevent lock contention."],
            evidence=[
                _make_evidence("led_001", "posthog", "query_batch_time", "Failures spike at 00:00"),
                _make_evidence("led_002", "jira", "DB-22", "Maintenance vacuum schedule conflict"),
            ],
            recommendation="Reschedule automated maintenance vacuum to 02:00 UTC.",
            recommendation_type="technical_remediation",
            success_metrics=["Midnight batch transfer success rate > 99.5%"],
            risks=["Maintenance window overlap with APAC morning traffic"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 3,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Directly grounded in telemetry spike and DB maintenance ticket.",
            "cross_source_reasoning": "Correlates timing of scheduler and maintenance job.",
            "contradiction_handling": "Consistent evidence without contradictions.",
            "causal_discipline": "Mechanistic explanation of table locking.",
            "recommendation_defensibility": "Safe and effective schedule offset.",
        },
    ),
    JudgeCase(
        case_id="judge_val_02",
        split="frozen_validation",
        scenario_id="scn_008",
        product_area="Transfers",
        archetype="causality_trap",
        user_query="Did the iOS update cause transfer failures across all platforms?",
        sut_recommendation=ProductRecommendation(
            problem_statement="iOS app update v5.1 broke transfers across Android and Web platforms as well.",
            why_it_matters="Severe platform reputation loss.",
            affected_users="All mobile and web users",
            factual_observations=["iOS app v5.1 was released on Tuesday."],
            inferences=["Since Android failures also occurred on Tuesday, iOS code broke Android."],
            hypotheses=["Shared backend microservice was destroyed by iOS release."],
            evidence=[_make_evidence("led_001", "jira", "IOS-501", "iOS release notes")],
            recommendation="Roll back iOS app to fix Android transfer failures.",
            recommendation_type="technical_remediation",
            success_metrics=["Android transfers restored"],
            risks=["iOS rollback does nothing for Android"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 1,
            "cross_source_reasoning": 0,
            "contradiction_handling": 0,
            "causal_discipline": 0,
            "recommendation_defensibility": 0,
        },
        human_gold_rationale={
            "groundedness": "Absurd extrapolation from single platform release ticket.",
            "cross_source_reasoning": "Failed to recognize client platform independence.",
            "contradiction_handling": "Ignored separate Android backend failure causes.",
            "causal_discipline": "Egregious causal overreach (post hoc ergo propter hoc).",
            "recommendation_defensibility": "Completely flawed recommendation.",
        },
    ),
    JudgeCase(
        case_id="judge_val_03",
        split="frozen_validation",
        scenario_id="scn_015",
        product_area="KYC",
        archetype="segmentation_trap",
        user_query="Which country applicants are suffering KYC verification delays?",
        sut_recommendation=ProductRecommendation(
            problem_statement="KYC delays are strictly confined to UK driving license verification, not EU passports.",
            why_it_matters="UK customer onboarding backlog increasing.",
            affected_users="UK residents submitting driving licenses",
            factual_observations=[
                "UK driving license verification p95 is 48 hours.",
                "EU passport verification p95 is 6 minutes.",
            ],
            inferences=["UK DVLA database API is experiencing elevated latency."],
            hypotheses=[
                "Switching UK driving license checks to manual queue will relieve backlog."
            ],
            evidence=[
                _make_evidence(
                    "led_001",
                    "posthog",
                    "query_kyc_country",
                    "UK driving license latency 48h vs EU 6m",
                )
            ],
            recommendation="Add temporary manual verification queue specifically for UK driving licenses.",
            recommendation_type="investigate_further",
            success_metrics=["UK verification turnaround < 4 hours"],
            risks=["Increased operational cost for support team"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 3,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Grounded in comparative country and document type latency metrics.",
            "cross_source_reasoning": "Successfully isolates affected cohort from unaffected EU users.",
            "contradiction_handling": "No contradictions present.",
            "causal_discipline": "Accurately attributes delay to DVLA integration.",
            "recommendation_defensibility": "Targeted manual workflow response.",
        },
    ),
    JudgeCase(
        case_id="judge_val_04",
        split="frozen_validation",
        scenario_id="scn_016",
        product_area="KYC",
        archetype="magnitude_trap",
        user_query="Are KYC failures widespread or isolated?",
        sut_recommendation=ProductRecommendation(
            problem_statement="KYC verification failure rate is 0.12%, isolated to expired document submissions.",
            why_it_matters="Minimal platform impact; routine user document expiration.",
            affected_users="Applicants submitting expired identity documents",
            factual_observations=[
                "4 total tickets logged for KYC rejection.",
                "Telemetry confirms overall KYC pass rate is 99.88%.",
            ],
            inferences=["No systemic OCR or verification bug exists."],
            hypotheses=["Clearer in-app expiration warning will reduce these isolated tickets."],
            evidence=[
                _make_evidence(
                    "led_001", "zendesk", "zen_016", "4 tickets on expired ID rejection"
                ),
                _make_evidence("led_002", "posthog", "query_kyc_rate", "Overall pass rate 99.88%"),
            ],
            recommendation="Do not alter verification pipeline; add client-side expiration date pre-check.",
            recommendation_type="technical_remediation",
            success_metrics=["Expired ID submission rate < 0.05%"],
            risks=["Minor client UI modification"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 4,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Correctly balances 4 tickets against 99.88% pass rate.",
            "cross_source_reasoning": "Contextualizes support complaints with population telemetry.",
            "contradiction_handling": "Reconciles complaints with healthy system performance.",
            "causal_discipline": "Resists magnifying an isolated operational issue.",
            "recommendation_defensibility": "Proportional client pre-check improvement.",
        },
    ),
    JudgeCase(
        case_id="judge_val_05",
        split="frozen_validation",
        scenario_id="scn_025",
        product_area="Funding",
        archetype="contradiction_handling",
        user_query="Why do customers claim card deposits were charged twice?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Pre-authorization hold and settlement appear as duplicate charges on customer banking apps.",
            why_it_matters="Customer alarm and high chargeback threat.",
            affected_users="Users depositing via debit card whose issuing banks do not collapse auth holds",
            factual_observations=[
                "45 tickets complain of double debit charges.",
                "Bank ledger telemetry confirms single settlement with initial temporary auth hold.",
            ],
            inferences=[
                "Customer bank displays both active pending authorization and posted transaction."
            ],
            hypotheses=[
                "Explaining authorization hold release in transaction receipt will eliminate confusion."
            ],
            evidence=[
                _make_evidence("led_001", "zendesk", "zen_025", "45 duplicate charge complaints"),
                _make_evidence(
                    "led_002", "posthog", "query_ledger_settle", "Exact 1:1 settlement match"
                ),
            ],
            recommendation="Add explicit in-app receipt clarifying that temporary authorization will drop in 48 hours.",
            recommendation_type="investigate_further",
            success_metrics=["Duplicate charge support inquiries reduced by 90%"],
            risks=["Customer bank may still delay hold release"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 4,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Firmly supported by both customer tickets and internal ledger logs.",
            "cross_source_reasoning": "Distinguishes between merchant settlement and issuer display.",
            "contradiction_handling": "Resolves contradictory double-charge claim definitively.",
            "causal_discipline": "Explains the exact banking mechanism.",
            "recommendation_defensibility": "Practical UX communication fix.",
        },
    ),
    JudgeCase(
        case_id="judge_val_06",
        split="frozen_validation",
        scenario_id="scn_026",
        product_area="Funding",
        archetype="diagnostic",
        user_query="What explains the sudden drop in instant bank deposits on Monday morning?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Open Banking aggregator token expiration caused instant bank deposit drop.",
            why_it_matters="Funding volume decreased by $1.2M over 6 hours.",
            affected_users="Users initiating instant Open Banking deposits",
            factual_observations=[
                "Instant deposit success rate dropped from 96% to 41% at 08:00.",
                "Jira issue FUND-109 shows aggregator OAuth client secret expired Sunday midnight.",
            ],
            inferences=[
                "Aggregator rejected API connection handshakes due to expired credentials."
            ],
            hypotheses=[
                "Rotating OAuth client credentials will immediately restore instant deposits."
            ],
            evidence=[
                _make_evidence(
                    "led_001", "posthog", "query_instant_fund", "Success rate drop to 41%"
                ),
                _make_evidence("led_002", "jira", "FUND-109", "OAuth client secret expiration"),
            ],
            recommendation="Rotate aggregator OAuth secret and implement automated 30-day expiration alerting.",
            recommendation_type="technical_remediation",
            success_metrics=[
                "Instant deposit success rate > 95%",
                "Zero credential expiration incidents",
            ],
            risks=["Aggregator token propagation delay (up to 15 mins)"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 3,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Precise connection between telemetry drop and Jira credential expiration.",
            "cross_source_reasoning": "Clear temporal alignment between 08:00 traffic and Sunday expiration.",
            "contradiction_handling": "No contradictions present.",
            "causal_discipline": "Clear technical cause and effect.",
            "recommendation_defensibility": "Defensible immediate rotation and preventive monitoring.",
        },
    ),
    JudgeCase(
        case_id="judge_val_07",
        split="frozen_validation",
        scenario_id="scn_036",
        product_area="Bill Payments",
        archetype="causality_trap",
        user_query="Did the UI redesign cause bill payment processing timeouts?",
        sut_recommendation=ProductRecommendation(
            problem_statement="The UI redesign has destroyed bill payment transaction reliability.",
            why_it_matters="Direct revenue and trust impact.",
            affected_users="All bill payment users",
            factual_observations=["New UI launched on Wednesday."],
            inferences=["Timeouts started on Wednesday, so CSS changes caused backend timeouts."],
            hypotheses=["Reverting font and color changes will fix server timeouts."],
            evidence=[_make_evidence("led_001", "jira", "UI-400", "Biller redesign release notes")],
            recommendation="Revert bill payment UI redesign immediately.",
            recommendation_type="technical_remediation",
            success_metrics=["Server timeout reduction"],
            risks=["Wasted design sprint work without addressing actual server timeout"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 1,
            "cross_source_reasoning": 1,
            "contradiction_handling": 0,
            "causal_discipline": 0,
            "recommendation_defensibility": 0,
        },
        human_gold_rationale={
            "groundedness": "Confuses frontend styling with backend database timeouts.",
            "cross_source_reasoning": "Failed to inspect backend biller API gateway logs.",
            "contradiction_handling": "Ignored server-side gateway degradation occurring in parallel.",
            "causal_discipline": "Severe causality trap.",
            "recommendation_defensibility": "Completely ineffective recommendation.",
        },
    ),
    JudgeCase(
        case_id="judge_val_08",
        split="frozen_validation",
        scenario_id="scn_037",
        product_area="Bill Payments",
        archetype="segmentation_trap",
        user_query="Are electricity bill payment failures affecting all providers?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Electricity bill failures are exclusive to PowerGrid Co API downtime, not other providers.",
            why_it_matters="PowerGrid customers cannot pay bills before disconnection cutoff.",
            affected_users="PowerGrid Co electricity subscribers",
            factual_observations=[
                "PowerGrid Co payments have a 92% failure rate with 504 gateway timeout.",
                "National Electric and GreenEnergy have 99.4% payment success rate.",
            ],
            inferences=["Issue is external downtime on PowerGrid Co's vendor gateway."],
            hypotheses=[
                "Placing PowerGrid on temporary maintenance mode will prevent failed debit attempts."
            ],
            evidence=[
                _make_evidence(
                    "led_001",
                    "posthog",
                    "query_biller_grid",
                    "PowerGrid 92% failure vs other 99.4%",
                )
            ],
            recommendation="Mark PowerGrid Co as temporarily unavailable in UI and notify affected customers.",
            recommendation_type="investigate_further",
            success_metrics=["Customer support contacts regarding PowerGrid decline by 75%"],
            risks=["Customer inconvenience while vendor restores API"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 3,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Rigorous segmentation comparison between billers.",
            "cross_source_reasoning": "Isolates external vendor failure from internal platform health.",
            "contradiction_handling": "No contradictions present.",
            "causal_discipline": "Accurately points to PowerGrid gateway 504 timeouts.",
            "recommendation_defensibility": "Constructive user communication and failure prevention.",
        },
    ),
    JudgeCase(
        case_id="judge_val_09",
        split="frozen_validation",
        scenario_id="scn_038",
        product_area="Bill Payments",
        archetype="missing_evidence",
        user_query="Why did mobile top-up payments fail when telco adapter logs are wiped?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Root cause of mobile top-up payment failures cannot be established due to wiped adapter logs.",
            why_it_matters="8 customer tickets logged without diagnostic technical evidence.",
            affected_users="Mobile top-up users",
            factual_observations=[
                "8 tickets reported top-up failures.",
                "Telco gateway logs are missing.",
            ],
            inferences=["Technical failure mechanism is unverified."],
            hypotheses=[
                "Telco partner rate limit or authentication token expiration could be responsible."
            ],
            evidence=[
                _make_evidence(
                    "led_001", "zendesk", "zen_038", "8 tickets on mobile top-up failure"
                )
            ],
            recommendation="Restore log persistence on telco adapter and monitor next top-up cycle.",
            recommendation_type="investigate_further",
            success_metrics=[
                "Log retention verified",
                "Error codes captured on subsequent top-ups",
            ],
            risks=["Delays final fix until next cycle"],
            confidence="low",  # Calibrated low confidence
            open_questions=["What error codes were returned by the telco gateway?"],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 3,
            "contradiction_handling": 4,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Faithfully captures tickets while disclosing lack of technical logs.",
            "cross_source_reasoning": "Acknowledges source gap without hallucination.",
            "contradiction_handling": "Maintains consistency.",
            "causal_discipline": "Refuses to speculate without logs; confidence appropriately low.",
            "recommendation_defensibility": "Defensible focus on restoring observability.",
        },
    ),
    JudgeCase(
        case_id="judge_val_10",
        split="frozen_validation",
        scenario_id="scn_010",
        product_area="Transfers",
        archetype="contradiction_handling",
        user_query="Did transfer fee increases cause user churn?",
        sut_recommendation=ProductRecommendation(
            problem_statement="Transfer fee restructuring did not cause user churn; churn is associated with bank switch delays.",
            why_it_matters="Prevents unnecessary and unprofitable rollback of fee schedule.",
            affected_users="Active high-frequency transfer senders",
            factual_observations=[
                "Transfer fees increased by 10 cents on the 1st of the month.",
                "Customer survey complaints cited fees, but churn cohorts specifically experienced > 60s transfer latency.",
                "Fee increase was followed by a 12% increase in overall transfer volume among non-delayed users.",
            ],
            inferences=[
                "Fee increase was a salient customer grievance, but technical latency was the true churn driver."
            ],
            hypotheses=[
                "Improving transfer latency will stem churn without rolling back fee adjustments."
            ],
            evidence=[
                _make_evidence(
                    "led_001", "posthog", "query_churn_latency", "Churn cohort latency > 60s"
                ),
                _make_evidence(
                    "led_002", "zendesk", "zen_010", "Survey complaints mention fee increase"
                ),
                _make_evidence(
                    "led_003",
                    "posthog",
                    "query_fee_vol",
                    "Transfer volume +12% on non-delayed cohorts",
                ),
            ],
            recommendation="Maintain new fee schedule; prioritize engineering resolution of bank switch latency.",
            recommendation_type="prioritise",
            success_metrics=["Churn in >60s cohort reduced to baseline < 1.5%"],
            risks=["Sustained customer sentiment friction if latency fix is delayed"],
            confidence="high",
            open_questions=[],
        ),
        human_ground_truth_scores={
            "groundedness": 4,
            "cross_source_reasoning": 4,
            "contradiction_handling": 4,
            "causal_discipline": 4,
            "recommendation_defensibility": 4,
        },
        human_gold_rationale={
            "groundedness": "Exemplary grounding across churn cohorts, surveys, and volume telemetry.",
            "cross_source_reasoning": "Disentangles stated preference (complaints about fees) from revealed preference (churn linked to latency).",
            "contradiction_handling": "Brilliant reconciliation of survey noise vs behavioral telemetry.",
            "causal_discipline": "Rigorous causal separation between fee increase and churn.",
            "recommendation_defensibility": "High-value commercial recommendation protecting revenue.",
        },
    ),
]

ALL_JUDGE_CASES: list[JudgeCase] = [*DEV_CALIBRATION_CASES, *FROZEN_VALIDATION_CASES]


def get_judge_cases(
    split: Literal["dev_calibration", "frozen_validation", "all"] = "all",
) -> list[JudgeCase]:
    """Retrieve judge cases filtered by split."""
    validate_judge_cases_distribution(ALL_JUDGE_CASES)
    if split == "all":
        return list(ALL_JUDGE_CASES)
    return [c for c in ALL_JUDGE_CASES if c.split == split]


def validate_judge_cases_distribution(cases: list[JudgeCase]) -> None:
    """Validate strict 10 dev calibration and 10 frozen validation cases."""
    if len(cases) != 20:
        raise ValueError(f"Expected exactly 20 judge cases, found {len(cases)}")

    dev_count = sum(1 for c in cases if c.split == "dev_calibration")
    val_count = sum(1 for c in cases if c.split == "frozen_validation")

    if dev_count != 10 or val_count != 10:
        raise ValueError(
            f"Invalid judge cases split: dev_calibration={dev_count} (expected 10), "
            f"frozen_validation={val_count} (expected 10)"
        )
