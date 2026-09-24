"""Unit tests verifying the EvidenceLedger and provenance tripartite identity validation."""

from datetime import UTC, datetime

import pytest
from app.agents.ledger import EvidenceLedger
from app.domain.analytics import AnalyticsQueryResult
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.specialists import CustomerFinding, SpecialistResult
from app.domain.zendesk import ZendeskTicket
from app.integrations.zendesk.adapter import ZendeskSearchResult
from app.tools.base import ToolError, ToolProvenance, ToolResult
from app.tools.support import SearchTicketsOutput


@pytest.fixture
def empty_ledger() -> EvidenceLedger:
    """Provide a fresh EvidenceLedger."""
    return EvidenceLedger()


def test_sequential_ledger_ids(empty_ledger: EvidenceLedger) -> None:
    """Verify ledger IDs are sequentially assigned (led_001, led_002, etc.)."""
    ticket1 = ZendeskTicket(
        id=1,
        subject="Ticket 1",
        description="Desc 1",
        status="new",
        priority="normal",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000001",
        tags=[],
    )
    ticket2 = ZendeskTicket(
        id=2,
        subject="Ticket 2",
        description="Desc 2",
        status="new",
        priority="normal",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000002",
        tags=[],
    )

    tr1 = ToolResult[ZendeskTicket](
        success=True,
        data=ticket1,
        provenance=ToolProvenance(
            source_type="zendesk",
            source_reference="ticket_id:1",
        ),
        execution_duration_ms=10.0,
    )
    tr2 = ToolResult[ZendeskTicket](
        success=True,
        data=ticket2,
        provenance=ToolProvenance(
            source_type="zendesk",
            source_reference="ticket_id:2",
        ),
        execution_duration_ms=12.0,
    )

    entry1 = empty_ledger.record_tool_result(tr1)
    entry2 = empty_ledger.record_tool_result(tr2)

    assert entry1 is not None
    assert entry2 is not None
    assert entry1.ledger_entry_id == "led_001"
    assert entry2.ledger_entry_id == "led_002"
    assert len(empty_ledger.entries) == 2


def test_failed_tool_result_not_recorded_in_entries(
    empty_ledger: EvidenceLedger,
) -> None:
    """Verify failed tool results do not produce ledger entries and are tracked in failed results."""
    tr_fail = ToolResult[ZendeskTicket](
        success=False,
        error=ToolError(
            error_type="upstream_error",
            message="Zendesk mock returned 500",
            attempted_source="zendesk",
        ),
        execution_duration_ms=5.0,
    )

    entry = empty_ledger.record_tool_result(tr_fail)
    assert entry is None
    assert len(empty_ledger.entries) == 0
    assert len(empty_ledger.failed_results) == 1

    limitations = empty_ledger.get_failure_limitations()
    assert len(limitations) == 1
    assert "Zendesk mock returned 500" in limitations[0]


def test_negative_search_result_is_valid_evidence(
    empty_ledger: EvidenceLedger,
) -> None:
    """Verify negative search results (0 items returned) are recorded as valid observed evidence."""
    search_res = ZendeskSearchResult(
        tickets=[],
        count=0,
    )
    tr = ToolResult[ZendeskSearchResult](
        success=True,
        data=search_res,
        provenance=ToolProvenance(
            source_type="zendesk",
            source_reference="query:nonexistent_keyword",
        ),
        execution_duration_ms=8.0,
    )

    entry = empty_ledger.record_tool_result(tr)
    assert entry is not None
    assert entry.ledger_entry_id == "led_001"
    assert entry.source_reference == "query:nonexistent_keyword"
    assert entry.typed_payload == search_res


def test_analytics_table_summary_preserves_metric_rows() -> None:
    """Table-shaped analytics results must not be reduced to value=None."""
    summary = EvidenceLedger._analytics_summary(
        AnalyticsQueryResult(
            query_description="Bill payment event counts",
            metric="event_count",
            rows=[
                {"event": "bill_payment_started", "count()": 450},
                {"event": "bill_payment_completed", "count()": 427},
                {"event": "bill_payment_failed", "count()": 23},
            ],
        )
    )

    assert "bill_payment_started" in summary
    assert "450" in summary
    assert "bill_payment_failed" in summary
    assert "23" in summary


def test_ticket_search_summary_preserves_customer_context() -> None:
    """A one-batch specialist must receive the ticket text already returned by search."""
    now = datetime.now(UTC)
    summary = EvidenceLedger._extract_summary(
        SearchTicketsOutput(
            tickets=[
                ZendeskTicket(
                    id=37,
                    requester_id="usr_000037",
                    subject="Electricity token never arrived",
                    description="I was debited but did not receive a token during month end.",
                    status="open",
                    priority="high",
                    channel="web",
                    created_at=now,
                    updated_at=now,
                    tags=["bill_payment"],
                )
            ],
            total_count=1,
            page=1,
        )
    )

    assert "Electricity token never arrived" in summary
    assert "did not receive a token" in summary


def test_tripartite_validation_success(empty_ledger: EvidenceLedger) -> None:
    """Verify tripartite validation passes when ledger_entry_id, source_type, and source_reference match."""
    ticket = ZendeskTicket(
        id=101,
        subject="Delay complaint",
        description="Transfer took 2 hours",
        status="solved",
        priority="high",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000101",
        tags=["delay"],
    )
    tr = ToolResult[ZendeskTicket](
        success=True,
        data=ticket,
        provenance=ToolProvenance(
            source_type="zendesk",
            source_reference="ticket_id:101",
        ),
        execution_duration_ms=15.0,
    )
    entry = empty_ledger.record_tool_result(tr)
    assert entry is not None

    ev = Evidence(
        ledger_entry_id=entry.ledger_entry_id,
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer experienced a 2-hour transfer delay",
        support="ticket.description: 'Transfer took 2 hours'",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Delay reported on transfer",
        facts=["Ticket #101 confirms customer report of 2-hour transfer delay"],
        interpretations=["Transfer delayed past expected window"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="delayed_transfer",
    )
    result = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        overall_facts=["Delay confirmed in ticket 101"],
        overall_interpretations=["Delay occurs"],
        tool_call_count=1,
        llm_call_count=2,
        investigation_complete=True,
    )

    # Should not raise
    empty_ledger.validate_specialist_result(result)


def test_tripartite_validation_fails_on_unregistered_id(
    empty_ledger: EvidenceLedger,
) -> None:
    """Verify validation fails if evidence references an ID not in the ledger."""
    ev = Evidence(
        ledger_entry_id="led_999",  # Non-existent
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Fake finding",
        support="Fake support",
        confidence=EvidenceConfidence.LOW,
    )
    finding = CustomerFinding(
        finding="Fake finding",
        facts=["Fake fact"],
        interpretations=["Fake interpretation"],
        evidence=[ev],
        confidence=EvidenceConfidence.LOW,
        observed_pattern="pattern",
    )
    result = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        tool_call_count=0,
        llm_call_count=1,
        investigation_complete=True,
    )

    with pytest.raises(ValueError) as exc:
        empty_ledger.validate_specialist_result(result)
    assert "led_999" in str(exc.value)


def test_tripartite_validation_fails_on_source_type_mismatch(
    empty_ledger: EvidenceLedger,
) -> None:
    """Verify validation fails if evidence source_type does not match ledger entry."""
    ticket = ZendeskTicket(
        id=101,
        subject="Delay complaint",
        description="Transfer took 2 hours",
        status="solved",
        priority="high",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000101",
        tags=[],
    )
    tr = ToolResult[ZendeskTicket](
        success=True,
        data=ticket,
        provenance=ToolProvenance(
            source_type="zendesk",
            source_reference="ticket_id:101",
        ),
        execution_duration_ms=10.0,
    )
    entry = empty_ledger.record_tool_result(tr)
    assert entry is not None

    # Mismatch: source_type claims to be posthog
    ev = Evidence(
        ledger_entry_id=entry.ledger_entry_id,
        source_type="posthog",  # Mismatch with "zendesk"
        source_reference="ticket_id:101",
        finding="Fake finding",
        support="Fake support",
        confidence=EvidenceConfidence.LOW,
    )
    finding = CustomerFinding(
        finding="Fake finding",
        facts=["Fake fact"],
        interpretations=["Fake interpretation"],
        evidence=[ev],
        confidence=EvidenceConfidence.LOW,
        observed_pattern="pattern",
    )
    result = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        tool_call_count=1,
        llm_call_count=1,
        investigation_complete=True,
    )

    with pytest.raises(ValueError) as exc:
        empty_ledger.validate_specialist_result(result)
    assert "source_type mismatch" in str(exc.value)


def test_tripartite_validation_fails_on_source_reference_mismatch(
    empty_ledger: EvidenceLedger,
) -> None:
    """Verify validation fails if evidence source_reference does not match ledger entry."""
    ticket = ZendeskTicket(
        id=101,
        subject="Delay complaint",
        description="Transfer took 2 hours",
        status="solved",
        priority="high",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000101",
        tags=[],
    )
    tr = ToolResult[ZendeskTicket](
        success=True,
        data=ticket,
        provenance=ToolProvenance(
            source_type="zendesk",
            source_reference="ticket_id:101",
        ),
        execution_duration_ms=10.0,
    )
    entry = empty_ledger.record_tool_result(tr)
    assert entry is not None

    # Mismatch: source_reference claims to be ticket_id:999
    ev = Evidence(
        ledger_entry_id=entry.ledger_entry_id,
        source_type="zendesk",
        source_reference="ticket_id:999",  # Mismatch with "ticket_id:101"
        finding="Fake finding",
        support="Fake support",
        confidence=EvidenceConfidence.LOW,
    )
    finding = CustomerFinding(
        finding="Fake finding",
        facts=["Fake fact"],
        interpretations=["Fake interpretation"],
        evidence=[ev],
        confidence=EvidenceConfidence.LOW,
        observed_pattern="pattern",
    )
    result = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        tool_call_count=1,
        llm_call_count=1,
        investigation_complete=True,
    )

    with pytest.raises(ValueError) as exc:
        empty_ledger.validate_specialist_result(result)
    assert "source_reference mismatch" in str(exc.value)
