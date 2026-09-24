"""Automated invariant testing that all material evidence fields are represented in judge context.

Verifies:
1. Every ledger entry ID appears.
2. Every finding / data summary appears.
3. Every support excerpt appears.
4. Source type and source reference are preserved.
5. Material provenance metadata (retrieved timestamp) is preserved.
6. Zero ground-truth fields (conclusions, expected findings, distractors, causal boundaries) leak into the context.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.agents.ledger import EvidenceLedgerEntry
from app.domain.analytics import AnalyticsQueryResult
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.jira import JiraIssue
from app.domain.recommendation import ProductRecommendation
from app.domain.zendesk import ZendeskTicket
from app.orchestration.state import InvestigationState
from app.tools.analytics import QueryAnalyticsOutput
from evaluations.evaluators.judge import LLMJudgeEvaluator
from evaluations.ground_truth.schema import EvaluationScenario


def test_judge_context_integrity_and_isolation() -> None:
    """Invariant test proving complete evidence serialization and strict ground-truth isolation."""
    # 1. Build rich test ledger entries across Zendesk, PostHog, and Jira
    zen_entry = EvidenceLedgerEntry(
        ledger_entry_id="led_zen_001",
        source_type="zendesk",
        source_reference="zen_ticket_8821",
        retrieved_at=datetime(2026, 9, 15, 10, 30, 0, tzinfo=UTC),
        data_summary="Customer reports card transfer button failed 3 times",
        typed_payload=ZendeskTicket(
            id=8821,
            requester_id="usr_abc123",
            subject="Card transfer failed",
            description="User clicked transfer button on iOS v2.4.1; spinner hung for 45s then showed error ERR_TIMEOUT.",
            status="open",
            priority="urgent",
            channel="email",
            created_at=datetime(2026, 9, 15, 10, 25, 0, tzinfo=UTC),
            updated_at=datetime(2026, 9, 15, 10, 25, 0, tzinfo=UTC),
        ),
    )

    jira_entry = EvidenceLedgerEntry(
        ledger_entry_id="led_jira_002",
        source_type="jira",
        source_reference="CARD-404",
        retrieved_at=datetime(2026, 9, 15, 10, 32, 0, tzinfo=UTC),
        data_summary="Upstream card processor timeout regression in release 2.4.1",
        typed_payload=JiraIssue(
            id=404,
            key="CARD-404",
            summary="Card processor gateway timeout",
            description="Issuer API timeout threshold was decreased to 250ms causing premature HTTP 504 dropped connections.",
            issue_type="Bug",
            status="In Progress",
            priority="High",
            created_at=datetime(2026, 9, 15, 9, 0, 0, tzinfo=UTC),
            updated_at=datetime(2026, 9, 15, 9, 0, 0, tzinfo=UTC),
        ),
    )

    posthog_entry = EvidenceLedgerEntry(
        ledger_entry_id="led_ph_003",
        source_type="posthog",
        source_reference="query_card_failures",
        retrieved_at=datetime(2026, 9, 15, 10, 35, 0, tzinfo=UTC),
        data_summary="Card transfer failure rate elevated at 14.8%",
        typed_payload=QueryAnalyticsOutput(
            result=AnalyticsQueryResult(
                query_description="Card transfer failure rate elevated at 14.8%",
                metric="p95_latency_ms",
                value="P95 latency elevated to 12,400ms with 504 status codes across 840 attempts.",
            ),
            cached=False,
            row_count=1,
        ),
    )

    rec = ProductRecommendation(
        problem_statement="Card transfer failures are caused by upstream processor timeout threshold misconfiguration.",
        why_it_matters="High user friction and card funding dropoff.",
        affected_users="iOS card depositors",
        factual_observations=[
            "Zendesk ticket reports spinner hung for 45s with ERR_TIMEOUT.",
            "PostHog query confirms 840 attempts with 14.8% failure rate and P95 latency of 12,400ms.",
            "Jira CARD-404 confirms issuer API timeout threshold was decreased to 250ms.",
        ],
        inferences=["Premature 250ms client timeout drops connections before 12.4s completion."],
        hypotheses=["Increasing timeout to 15,000ms will resolve card funding failures."],
        evidence=[
            Evidence(
                ledger_entry_id="led_zen_001",
                source_type="zendesk",
                source_reference="zen_ticket_8821",
                finding="User experienced 45s spinner and ERR_TIMEOUT.",
                support="User clicked transfer button on iOS v2.4.1; spinner hung for 45s then showed error ERR_TIMEOUT.",
                confidence=EvidenceConfidence.HIGH,
            ),
            Evidence(
                ledger_entry_id="led_jira_002",
                source_type="jira",
                source_reference="CARD-404",
                finding="Jira bug details 250ms threshold decrease.",
                support="Issuer API timeout threshold was decreased to 250ms causing premature HTTP 504 dropped connections.",
                confidence=EvidenceConfidence.HIGH,
            ),
            Evidence(
                ledger_entry_id="led_ph_003",
                source_type="posthog",
                source_reference="query_card_failures",
                finding="Telemetry logs confirm 504 errors.",
                support="P95 latency elevated to 12,400ms with 504 status codes across 840 attempts.",
                confidence=EvidenceConfidence.HIGH,
            ),
        ],
        recommendation="Update timeout threshold in CARD-404 to 15,000ms.",
        recommendation_type="technical_remediation",
        success_metrics=["Card transfer failure rate drops below 1%"],
        risks=["Increased client wait time on genuinely dead sockets"],
        confidence="high",
        open_questions=[],
    )

    state = InvestigationState(
        investigation_id="inv_test_context_integrity",
        user_query="Why are card transfers failing today?",
        evidence_ledger_entries={
            "led_zen_001": zen_entry,
            "led_jira_002": jira_entry,
            "led_ph_003": posthog_entry,
        },
        recommendation=rec,
    )

    # 2. Build scenario with sensitive ground truth strings that MUST NOT enter the context
    scenario = EvaluationScenario(
        scenario_id="scn_secret_id_999",
        name="Secret Scenario Name",
        version="1.0",
        split="val",
        archetype="synthetic_trap",
        product_area="Card Deposits",
        user_query="Why are card transfers failing today?",
        required_sources=["zendesk", "posthog", "jira"],
        expected_findings=["HIDDEN_EXPECTED_FINDING_CARD_TIMEOUT"],
        distractor_facts=["HIDDEN_DISTRACTOR_FACT_UNRELATED_FEE"],
        expected_contradictions=["HIDDEN_CONTRADICTION_UNNOTICED_FAILURES"],
        causal_boundaries=["HIDDEN_CAUSAL_BOUNDARY_DO_NOT_BLAME_NETWORK"],
        acceptable_recommendation_types=["technical_remediation"],
        acceptable_conclusions=["HIDDEN_ACCEPTABLE_CONCLUSION_TIMEOUT"],
        unacceptable_conclusions=["HIDDEN_UNACCEPTABLE_CONCLUSION_DATABASE"],
        expected_confidence_range=("high", "high"),
    )

    # 3. Assemble context
    evaluator = LLMJudgeEvaluator(llm_client=MagicMock(), model_name="dummy_model")
    context = evaluator._assemble_judge_context(state, scenario, rec)

    # 4. Verify Context Integrity: Every ledger entry field must appear
    for eid, entry in state.evidence_ledger_entries.items():
        assert eid in context, f"Missing ledger entry ID {eid} in judge context"
        assert entry.source_type in context, (
            f"Missing source type {entry.source_type} in judge context"
        )
        assert entry.source_reference in context, (
            f"Missing source ref {entry.source_reference} in judge context"
        )
        assert entry.data_summary in context, f"Missing data summary for {eid} in judge context"

    # Support excerpts must appear in judge context
    assert "spinner hung for 45s then showed error ERR_TIMEOUT" in context, (
        "Zendesk support excerpt missing from judge context"
    )
    assert "Issuer API timeout threshold was decreased to 250ms" in context, (
        "Jira support excerpt missing from judge context"
    )
    assert (
        "P95 latency elevated to 12,400ms with 504 status codes across 840 attempts." in context
    ), "PostHog support excerpt missing from judge context"

    # Provenance timestamp must appear
    assert "2026-09-15T10:30:00+00:00" in context
    assert "2026-09-15T10:32:00+00:00" in context
    assert "2026-09-15T10:35:00+00:00" in context

    # 5. Verify Ground Truth Isolation: Zero ground-truth fields enter context
    forbidden_gt_strings = [
        "HIDDEN_EXPECTED_FINDING_CARD_TIMEOUT",
        "HIDDEN_DISTRACTOR_FACT_UNRELATED_FEE",
        "HIDDEN_CONTRADICTION_UNNOTICED_FAILURES",
        "HIDDEN_CAUSAL_BOUNDARY_DO_NOT_BLAME_NETWORK",
        "HIDDEN_ACCEPTABLE_CONCLUSION_TIMEOUT",
        "HIDDEN_UNACCEPTABLE_CONCLUSION_DATABASE",
        "scn_secret_id_999",
        "=== GROUND TRUTH EXPECTATIONS ===",
    ]
    for secret in forbidden_gt_strings:
        assert secret not in context, f"Ground truth leakage in judge context: {secret}"
