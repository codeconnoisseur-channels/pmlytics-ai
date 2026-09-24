"""Unit tests for deterministic evaluators, deduplication, and confidence calibration."""

from datetime import UTC, datetime

from app.agents.ledger import EvidenceLedgerEntry
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.jira import JiraIssue
from app.domain.plan import InvestigationPlan, InvestigationTask
from app.domain.recommendation import ProductRecommendation
from app.domain.zendesk import ZendeskTicket
from app.orchestration.state import InvestigationState
from evaluations.dataset.loader import get_scenario_by_id
from evaluations.evaluators.deterministic import (
    evaluate_confidence_calibration,
    evaluate_retrieval_quality,
    evaluate_source_selection,
    evaluate_structural_citations,
    extract_unique_evidence_records,
    map_tasks_to_sources,
)


def _make_sample_zendesk_entry(ledger_id: str, ticket_id: str, summary: str) -> EvidenceLedgerEntry:
    return EvidenceLedgerEntry(
        ledger_entry_id=ledger_id,
        source_type="zendesk",
        source_reference=ticket_id,
        retrieved_at=datetime.now(UTC),
        data_summary=summary,
        typed_payload=ZendeskTicket(
            id=int(ticket_id.replace("zen_", "").replace("t_", "100")),
            requester_id="usr_abc123",
            subject=summary,
            description=summary,
            status="open",
            priority="normal",
            channel="email",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    )


def _make_sample_jira_entry(ledger_id: str, issue_key: str, summary: str) -> EvidenceLedgerEntry:
    num_part = "".join(filter(str.isdigit, issue_key)) or "101"
    return EvidenceLedgerEntry(
        ledger_entry_id=ledger_id,
        source_type="jira",
        source_reference=issue_key,
        retrieved_at=datetime.now(UTC),
        data_summary=summary,
        typed_payload=JiraIssue(
            id=int(num_part),
            key=issue_key,
            summary=summary,
            description=summary,
            issue_type="Bug",
            status="In Progress",
            priority="High",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    )


def _make_evidence(ledger_id: str, source_type: str, ref: str) -> Evidence:
    return Evidence(
        ledger_entry_id=ledger_id,
        source_type=source_type,  # type: ignore[arg-type]
        source_reference=ref,
        finding="Direct finding verified from ledger entry",
        support=f"Extracted payload support from {ref}",
        confidence=EvidenceConfidence.HIGH,
    )


def test_structural_citation_validity_100_percent() -> None:
    """Verify 100% validity when all citations resolve to ledger entries."""
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="test query",
        evidence_ledger_entries={
            "led_001": _make_sample_zendesk_entry(
                "led_001", "zen_001", "Customer complaint summary"
            ),
            "led_002": _make_sample_jira_entry("led_002", "PAY-117", "Engineering bug summary"),
        },
    )

    rec = ProductRecommendation(
        problem_statement="Problem statement explaining customer issues.",
        why_it_matters="Impact statement explaining why it matters.",
        affected_users="Segment A users",
        factual_observations=["Fact 1 observed"],
        inferences=["Inference 1 deduced"],
        hypotheses=["Hypothesis 1 proposed"],
        evidence=[
            _make_evidence("led_001", "zendesk", "zen_001"),
            _make_evidence("led_002", "jira", "PAY-117"),
        ],
        recommendation="Recommended product action to fix the bug.",
        recommendation_type="technical_remediation",
        success_metrics=["Metric 1"],
        risks=["Risk 1"],
        confidence="high",
        open_questions=[],
    )

    validity, total, valid, hallucinated = evaluate_structural_citations(state, rec)
    assert validity == 1.0
    assert total == 2
    assert valid == 2
    assert hallucinated == 0


def test_structural_citation_catches_hallucinated_entry() -> None:
    """Verify validity is degraded when citation references nonexistent entry."""
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="test query",
        evidence_ledger_entries={
            "led_001": _make_sample_zendesk_entry("led_001", "zen_001", "Customer complaint"),
        },
    )

    rec = ProductRecommendation(
        problem_statement="Problem statement explaining customer issues.",
        why_it_matters="Impact statement explaining why it matters.",
        affected_users="Segment A users",
        factual_observations=["Fact 1 observed"],
        inferences=["Inference 1 deduced"],
        hypotheses=["Hypothesis 1 proposed"],
        evidence=[
            _make_evidence("led_001", "zendesk", "zen_001"),
            _make_evidence("led_fabricated", "jira", "PAY-999"),
        ],
        recommendation="Recommended product action to fix the bug.",
        recommendation_type="technical_remediation",
        success_metrics=["Metric 1"],
        risks=["Risk 1"],
        confidence="high",
        open_questions=[],
    )

    validity, total, valid, hallucinated = evaluate_structural_citations(state, rec)
    assert validity == 0.5
    assert total == 2
    assert valid == 1
    assert hallucinated == 1


def test_task_to_source_mapping_and_precision_recall() -> None:
    """Verify specialist tasks map correctly to data domains."""
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="test query",
        plan=InvestigationPlan(
            question_type="diagnostic",
            objectives=["Search tickets and inspect Jira"],
            tasks=[
                InvestigationTask(
                    specialist="research",
                    objective="Search tickets for pending complaints",
                ),
                InvestigationTask(
                    specialist="engineering",
                    objective="Inspect Jira for known timeout bugs",
                ),
            ],
            required_sources=["zendesk", "jira"],
            success_condition="Tickets and Jira issues identified",
        ),
    )

    sources = map_tasks_to_sources(state)
    assert sources == {"zendesk", "jira"}

    prec, rec, jaccard = evaluate_source_selection(sources, ["zendesk", "jira", "posthog"])
    assert prec == 1.0
    assert round(rec, 2) == 0.67
    assert round(jaccard, 2) == 0.67


def test_unique_evidence_record_deduplication_and_redundancy() -> None:
    """Verify repeated retrievals of identical records count once toward unique records."""
    scenario = get_scenario_by_id("scn_001")

    # Simulate state with duplicate ticket retrievals across rounds
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="test query",
        evidence_ledger_entries={
            "research:r0:led_001": _make_sample_zendesk_entry(
                "research:r0:led_001", "zen_001", "Initial ticket search"
            ),
            "research:r1:led_001": _make_sample_zendesk_entry(
                "research:r1:led_001", "zen_001", "Follow-up ticket comment retrieval"
            ),
            "engineering:r0:led_001": _make_sample_jira_entry(
                "engineering:r0:led_001", "PAY-117", "Jira issue PAY-117 webhook timeout"
            ),
            "analytics:r0:led_001": EvidenceLedgerEntry(
                ledger_entry_id="analytics:r0:led_001",
                source_type="posthog",
                source_reference="query_latency",
                retrieved_at=datetime.now(UTC),
                data_summary="p95_processing_latency exceeds 45s for bank_code in ['Bank A', 'Bank B']",
                typed_payload=ZendeskTicket(  # using typed domain payload
                    id=999,
                    requester_id="usr_abc123",
                    subject="analytics summary",
                    description="p95_processing_latency exceeds 45s",
                    status="closed",
                    priority="normal",
                    channel="web",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                ),
            ),
        },
    )

    unique_records, total_entries = extract_unique_evidence_records(state, scenario)

    # 4 ledger entries, but only 3 unique underlying records (zen_001 deduplicated!)
    assert total_entries == 4
    assert len(unique_records) == 3
    assert "zendesk:zen_001" in unique_records
    assert "jira:PAY-117" in unique_records
    assert "analytics:obs_transfer_pending_latency" in unique_records

    # Context recall and precision on unique records
    recall, precision, redundancy = evaluate_retrieval_quality(
        unique_records, scenario, total_entries
    )
    assert recall == 0.75  # 3 of 4 expected records retrieved (zen_001, PAY-117, analytics obs)
    assert precision == 1.0  # All 3 retrieved records are in the expected ground truth set
    assert redundancy == 0.25  # 1 duplicate out of 4 entries = 25% redundancy


def test_confidence_calibration_and_overconfidence_penalty() -> None:
    """Verify confidence range matching and overconfidence penalty detection."""
    # scn_007 has expected_confidence_range: ("low", "low")
    scenario_low = get_scenario_by_id("scn_007")

    rec_overconfident = ProductRecommendation(
        problem_statement="Problem statement explaining customer issues.",
        why_it_matters="Impact statement explaining why it matters.",
        affected_users="Segment A users",
        factual_observations=["Fact 1 observed"],
        inferences=["Inference 1 deduced"],
        hypotheses=["Hypothesis 1 proposed"],
        evidence=[_make_evidence("led_001", "zendesk", "zen_001")],
        recommendation="Recommended product action to fix the bug.",
        recommendation_type="technical_remediation",
        success_metrics=["Metric 1"],
        risks=["Risk 1"],
        confidence="high",  # Overconfident!
        open_questions=[],
    )

    matched, penalty = evaluate_confidence_calibration(rec_overconfident, scenario_low)
    assert matched is False
    assert penalty == 1

    rec_cautious = rec_overconfident.model_copy(update={"confidence": "low"})
    matched_cautious, penalty_cautious = evaluate_confidence_calibration(rec_cautious, scenario_low)
    assert matched_cautious is True
    assert penalty_cautious == 0


def test_scenario_aware_evidence_coverage_single_source() -> None:
    """Verify single-source scenario receives 100% coverage when its single required source is retrieved."""
    from evaluations.evaluators.deterministic import evaluate_scenario_aware_evidence_coverage

    base_scenario = get_scenario_by_id("scn_001")
    single_source_scenario = base_scenario.model_copy(update={"required_sources": ["zendesk"]})

    state_with_only_zendesk = InvestigationState(
        investigation_id="inv_test",
        user_query="test",
        evidence_ledger_entries={
            "led_001": _make_sample_zendesk_entry("led_001", "zen_001", "Bill failure"),
        },
    )

    coverage = evaluate_scenario_aware_evidence_coverage(
        state_with_only_zendesk, single_source_scenario
    )
    assert coverage == 1.0, (
        "Single-source scenario must achieve 1.0 coverage when required source is present"
    )


def test_deterministic_contradiction_fidelity_and_provenance() -> None:
    """Verify deterministic contradiction fidelity and provenance validation."""
    from evaluations.evaluators.deterministic import (
        evaluate_citation_consistency_and_provenance,
        evaluate_deterministic_contradictions,
        evaluate_schema_completeness,
    )

    base_scenario = get_scenario_by_id("scn_001")
    scenario_with_conflict = base_scenario.model_copy(
        update={
            "expected_contradictions": [
                "Complaints claim failure but ledger telemetry confirms 99.8% success"
            ]
        }
    )

    rec_with_conflict = ProductRecommendation(
        problem_statement="Customer complaints surge despite high underlying settlement rate.",
        why_it_matters="Perception gap causing support escalations.",
        affected_users="Mobile users",
        factual_observations=["45 tickets logged", "Settlement success rate 99.8%"],
        inferences=["Complaints reflect notification lag rather than ledger transfer failure."],
        hypotheses=["Push notification delay explains perceived failure."],
        evidence=[_make_evidence("led_001", "zendesk", "zen_001")],
        recommendation="Fix notification pipeline and clarify status banner in app.",
        recommendation_type="technical_remediation",
        success_metrics=["Support contacts drop by 80%"],
        risks=["Backend notification delay"],
        confidence="high",
        open_questions=[],
    )

    # 1. Contradiction detected
    assert evaluate_deterministic_contradictions(rec_with_conflict, scenario_with_conflict) is True

    # 2. Schema completeness
    assert evaluate_schema_completeness(rec_with_conflict) is True

    # 3. Provenance validity
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="test",
        evidence_ledger_entries={
            "led_001": _make_sample_zendesk_entry("led_001", "zen_001", "Complaint"),
        },
    )
    consistent, all_exist, prov_validity, unsupp_count = (
        evaluate_citation_consistency_and_provenance(state, rec_with_conflict)
    )
    assert consistent is True
    assert all_exist is True
    assert prov_validity == 1.0
    assert unsupp_count == 0
