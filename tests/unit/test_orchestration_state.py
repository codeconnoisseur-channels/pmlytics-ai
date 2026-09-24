"""Unit tests for LangGraph state schema, reducers, and global ledger identity."""

from datetime import UTC, datetime

from app.agents.ledger import EvidenceLedgerEntry
from app.domain.analytics import AnalyticsQueryResult
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.jira import JiraIssue
from app.domain.specialists import CustomerFinding
from app.domain.zendesk import ZendeskTicket
from app.orchestration.state import (
    GraphBudgetUsage,
    append_customer_findings,
    merge_evidence_ledger_entries,
    update_graph_budget,
)


def _make_sample_ticket() -> ZendeskTicket:
    return ZendeskTicket(
        id=101,
        subject="Ticket 101",
        description="Desc 101",
        status="open",
        priority="normal",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000001",
        tags=[],
    )


def _make_sample_jira() -> JiraIssue:
    return JiraIssue(
        id=10001,
        key="PAY-117",
        summary="Webhook timeout issue",
        description="Desc",
        issue_type="Bug",
        status="In Progress",
        priority="High",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        components=[],
    )


def _make_sample_analytics() -> AnalyticsQueryResult:
    return AnalyticsQueryResult(
        query_description="Transfer funnel",
        metric="conversion_rate",
        value=0.25,
        rows=[],
    )


def test_global_ledger_identity_prevents_parallel_collision() -> None:
    """Prove that parallel specialists producing the same local sequence number do not collide when aggregated."""
    now = datetime.now(UTC)

    research_entry = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        retrieved_at=now,
        data_summary="Customer ticket 101 description",
        typed_payload=_make_sample_ticket(),
    )

    analytics_entry = EvidenceLedgerEntry(
        ledger_entry_id="analytics:r0:led_001",
        source_type="posthog",
        source_reference="query:funnel:dropoff",
        retrieved_at=now,
        data_summary="Analytics funnel metric",
        typed_payload=_make_sample_analytics(),
    )

    engineering_entry = EvidenceLedgerEntry(
        ledger_entry_id="engineering:r0:led_001",
        source_type="jira",
        source_reference="issue_key:PAY-117",
        retrieved_at=now,
        data_summary="Jira issue PAY-117 details",
        typed_payload=_make_sample_jira(),
    )

    # Merge via reducer
    merged = merge_evidence_ledger_entries({}, {"research:r0:led_001": research_entry})
    merged = merge_evidence_ledger_entries(merged, {"analytics:r0:led_001": analytics_entry})
    merged = merge_evidence_ledger_entries(merged, {"engineering:r0:led_001": engineering_entry})

    # Assert all 3 exist with distinct keys and zero clobbering
    assert len(merged) == 3
    assert "research:r0:led_001" in merged
    assert "analytics:r0:led_001" in merged
    assert "engineering:r0:led_001" in merged
    assert merged["research:r0:led_001"].source_type == "zendesk"
    assert merged["analytics:r0:led_001"].source_type == "posthog"
    assert merged["engineering:r0:led_001"].source_type == "jira"


def test_evidence_reducer_rejects_duplicate_ledger_id_fail_closed() -> None:
    """Verify that merging an incoming ledger entry with an already existing ID raises ProvenanceCollisionError."""
    import pytest
    from app.orchestration.state import ProvenanceCollisionError

    now = datetime.now(UTC)
    entry_original = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        retrieved_at=now,
        data_summary="Original customer ticket",
        typed_payload=_make_sample_ticket(),
    )
    entry_duplicate = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",  # Same ID!
        source_type="zendesk",
        source_reference="ticket_id:102",
        retrieved_at=now,
        data_summary="Different ticket with duplicate ID",
        typed_payload=_make_sample_ticket(),
    )

    left = {"research:r0:led_001": entry_original}
    right = {"research:r0:led_001": entry_duplicate}

    with pytest.raises(ProvenanceCollisionError, match="Evidence ledger collision detected"):
        merge_evidence_ledger_entries(left, right)

    # Assert original left mapping was not mutated
    assert left["research:r0:led_001"].source_reference == "ticket_id:101"


def test_round_scoped_ledger_identity_prevents_same_specialist_collision() -> None:
    """Verify that same specialist executing in Round 0 and Round 1 produces distinct keys that merge cleanly."""
    now = datetime.now(UTC)
    r0_entry = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        retrieved_at=now,
        data_summary="Round 0 ticket",
        typed_payload=_make_sample_ticket(),
    )
    r1_entry = EvidenceLedgerEntry(
        ledger_entry_id="research:r1:led_001",
        source_type="zendesk",
        source_reference="ticket_id:102",
        retrieved_at=now,
        data_summary="Round 1 follow-up ticket",
        typed_payload=_make_sample_ticket(),
    )

    merged = merge_evidence_ledger_entries(
        {"research:r0:led_001": r0_entry},
        {"research:r1:led_001": r1_entry},
    )

    assert len(merged) == 2
    assert "research:r0:led_001" in merged
    assert "research:r1:led_001" in merged
    assert merged["research:r0:led_001"].source_reference == "ticket_id:101"
    assert merged["research:r1:led_001"].source_reference == "ticket_id:102"


def test_specialist_completions_reducer_merges_statuses() -> None:
    """Verify that merge_specialist_completions accumulates specialist completion flags."""
    from app.orchestration.state import merge_specialist_completions

    left = {"research": True, "analytics": True}
    right = {"engineering": False}
    merged = merge_specialist_completions(left, right)

    assert merged == {"research": True, "analytics": True, "engineering": False}


def test_findings_reducers_accumulate_without_loss() -> None:
    """Verify that finding lists accumulate across parallel branch completions."""
    ev1 = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Finding 1",
        support="Support 1",
        confidence=EvidenceConfidence.HIGH,
    )
    ev2 = Evidence(
        ledger_entry_id="research:led_002",
        source_type="zendesk",
        source_reference="ticket_id:102",
        finding="Finding 2",
        support="Support 2",
        confidence=EvidenceConfidence.HIGH,
    )

    f1 = CustomerFinding(
        finding="Observation 1",
        facts=["Fact 1"],
        interpretations=["Interp 1"],
        evidence=[ev1],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="pattern_1",
    )
    f2 = CustomerFinding(
        finding="Observation 2",
        facts=["Fact 2"],
        interpretations=["Interp 2"],
        evidence=[ev2],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="pattern_2",
    )

    accumulated = append_customer_findings([f1], [f2])
    assert len(accumulated) == 2
    assert accumulated[0].finding == "Observation 1"
    assert accumulated[1].finding == "Observation 2"


def test_budget_usage_reducer_aggregates_actual_counts() -> None:
    """Verify that GraphBudgetUsage accumulates actual counters accurately."""
    b1 = GraphBudgetUsage(
        planner_llm_calls=2,
        research_tool_calls=5,
        research_llm_calls=7,
    )
    b2 = GraphBudgetUsage(
        analytics_tool_calls=4,
        analytics_llm_calls=6,
        engineering_tool_calls=3,
        engineering_llm_calls=5,
    )

    total = update_graph_budget(b1, b2)
    assert total.planner_llm_calls == 2
    assert total.research_tool_calls == 5
    assert total.analytics_tool_calls == 4
    assert total.engineering_tool_calls == 3
    assert total.total_tool_calls == 12
    assert total.total_llm_calls == 20
