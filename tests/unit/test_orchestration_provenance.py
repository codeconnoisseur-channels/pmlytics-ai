"""Unit tests for graph-level evidence provenance validation."""

from datetime import UTC, datetime

import pytest
from app.agents.ledger import EvidenceLedgerEntry
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.specialists import CustomerFinding
from app.domain.zendesk import ZendeskTicket
from app.orchestration.state import InvestigationState
from app.orchestration.validation import (
    ProvenanceValidationError,
    validate_investigation_evidence,
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


def _make_sample_entry(
    entry_id: str,
    source_type: str = "zendesk",
    source_ref: str = "ticket_id:101",
) -> EvidenceLedgerEntry:
    return EvidenceLedgerEntry(
        ledger_entry_id=entry_id,
        source_type=source_type,  # type: ignore[arg-type]
        source_reference=source_ref,
        retrieved_at=datetime.now(UTC),
        data_summary="Sample summary",
        typed_payload=_make_sample_ticket(),
    )


def test_provenance_validation_success() -> None:
    """Verify that correctly grounded evidence passes graph provenance validation."""
    entry = _make_sample_entry("research:led_001", "zendesk", "ticket_id:101")
    ev = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer states transfer delayed",
        support="ticket excerpt",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Delays observed",
        facts=["Fact 1"],
        interpretations=["Interp 1"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="transfer_delay",
    )

    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        evidence_ledger_entries={"research:led_001": entry},
        customer_findings=[finding],
    )

    # Should succeed without raising
    validate_investigation_evidence(state)


def test_provenance_validation_fails_on_unregistered_id() -> None:
    """Verify that evidence with unverified ledger ID raises ProvenanceValidationError."""
    entry = _make_sample_entry("research:led_001", "zendesk", "ticket_id:101")
    ev = Evidence(
        ledger_entry_id="research:led_999",  # Unregistered ID!
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer states transfer delayed",
        support="ticket excerpt",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Delays observed",
        facts=["Fact 1"],
        interpretations=["Interp 1"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="transfer_delay",
    )

    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        evidence_ledger_entries={"research:led_001": entry},
        customer_findings=[finding],
    )

    with pytest.raises(
        ProvenanceValidationError, match="unknown ledger_entry_id 'research:led_999'"
    ):
        validate_investigation_evidence(state)


def test_provenance_validation_fails_on_source_type_mismatch() -> None:
    """Verify that evidence with mismatched source_type raises ProvenanceValidationError."""
    entry = _make_sample_entry("research:led_001", "zendesk", "ticket_id:101")
    ev = Evidence(
        ledger_entry_id="research:led_001",
        source_type="jira",  # Mismatch!
        source_reference="ticket_id:101",
        finding="Customer states transfer delayed",
        support="ticket excerpt",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Delays observed",
        facts=["Fact 1"],
        interpretations=["Interp 1"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="transfer_delay",
    )

    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        evidence_ledger_entries={"research:led_001": entry},
        customer_findings=[finding],
    )

    with pytest.raises(
        ProvenanceValidationError, match="expected source_type 'zendesk', got 'jira'"
    ):
        validate_investigation_evidence(state)


def test_provenance_validation_fails_on_source_reference_mismatch() -> None:
    """Verify that evidence with mismatched source_reference raises ProvenanceValidationError."""
    entry = _make_sample_entry("research:led_001", "zendesk", "ticket_id:101")
    ev = Evidence(
        ledger_entry_id="research:led_001",
        source_type="zendesk",
        source_reference="ticket_id:999",  # Mismatch!
        finding="Customer states transfer delayed",
        support="ticket excerpt",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Delays observed",
        facts=["Fact 1"],
        interpretations=["Interp 1"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="transfer_delay",
    )

    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        evidence_ledger_entries={"research:led_001": entry},
        customer_findings=[finding],
    )

    with pytest.raises(
        ProvenanceValidationError,
        match="expected source_reference 'ticket_id:101', got 'ticket_id:999'",
    ):
        validate_investigation_evidence(state)
