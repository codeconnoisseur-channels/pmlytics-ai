"""Unit tests verifying schemas for specialist findings, evidence, and results."""

import pytest
from app.domain.evidence import (
    Evidence,
    EvidenceConfidence,
)
from app.domain.specialists import (
    AnalyticsFinding,
    CustomerFinding,
    EngineeringFinding,
    SpecialistResult,
)
from pydantic import ValidationError


def test_evidence_model_valid() -> None:
    """Verify valid Evidence creation with all required fields."""
    ev = Evidence(
        ledger_entry_id="led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer reported transfer pending for 48 hours",
        support="ticket.description: 'My transfer has been pending since yesterday'",
        confidence=EvidenceConfidence.HIGH,
        limitations=["Single customer report"],
    )
    assert ev.ledger_entry_id == "led_001"
    assert ev.source_type == "zendesk"
    assert ev.source_reference == "ticket_id:101"
    assert ev.confidence == EvidenceConfidence.HIGH
    assert len(ev.limitations) == 1


def test_evidence_model_frozen() -> None:
    """Verify Evidence instances are immutable."""
    ev = Evidence(
        ledger_entry_id="led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Transfer pending",
        support="Quote",
        confidence=EvidenceConfidence.HIGH,
    )
    with pytest.raises(ValidationError):
        ev.finding = "Modified finding"


def test_customer_finding_epistemic_separation() -> None:
    """Verify CustomerFinding requires facts, interpretations, and evidence."""
    ev = Evidence(
        ledger_entry_id="led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer reported transfer pending",
        support="Quote",
        confidence=EvidenceConfidence.HIGH,
    )

    finding = CustomerFinding(
        finding="Users perceive transfers as delayed during peak hours",
        facts=["Ticket #101 shows pending status for 3 hours"],
        interpretations=["User expected instant settlement"],
        hypotheses=["App status updates lack clear ETA messaging"],
        evidence=[ev],
        confidence=EvidenceConfidence.MEDIUM,
        observed_pattern="delayed_transfer_complaint",
        affected_users="Standard tier retail users",
        frequency_context="1 of 5 sampled tickets",
    )

    assert finding.finding == "Users perceive transfers as delayed during peak hours"
    assert len(finding.facts) == 1
    assert len(finding.interpretations) == 1
    assert len(finding.hypotheses) == 1
    assert len(finding.evidence) == 1
    assert finding.observed_pattern == "delayed_transfer_complaint"


def test_finding_requires_at_least_one_fact_and_interpretation() -> None:
    """Verify that finding fails validation if facts or interpretations are empty."""
    ev = Evidence(
        ledger_entry_id="led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Pending transfer",
        support="Quote",
        confidence=EvidenceConfidence.HIGH,
    )

    # Empty facts should fail
    with pytest.raises(ValidationError):
        CustomerFinding(
            finding="Test finding",
            facts=[],
            interpretations=["Some interpretation"],
            evidence=[ev],
            confidence=EvidenceConfidence.LOW,
            observed_pattern="pattern",
        )

    # Empty interpretations should fail
    with pytest.raises(ValidationError):
        CustomerFinding(
            finding="Test finding",
            facts=["Some fact"],
            interpretations=[],
            evidence=[ev],
            confidence=EvidenceConfidence.LOW,
            observed_pattern="pattern",
        )

    # Empty evidence should fail
    with pytest.raises(ValidationError):
        CustomerFinding(
            finding="Test finding",
            facts=["Some fact"],
            interpretations=["Some interpretation"],
            evidence=[],
            confidence=EvidenceConfidence.LOW,
            observed_pattern="pattern",
        )


def test_analytics_finding_schema() -> None:
    """Verify AnalyticsFinding validates required quantitative fields."""
    ev = Evidence(
        ledger_entry_id="led_002",
        source_type="posthog",
        source_reference="event:transfer_failed",
        finding="High failure rate for amount >= 50,000 NGN",
        support="funnel conversion dropped to 17.4%",
        confidence=EvidenceConfidence.HIGH,
    )

    af = AnalyticsFinding(
        finding="Transfer conversion drops sharply above 50k NGN",
        facts=["Conversion rate is 17.4% for amounts >= 50000 NGN"],
        interpretations=["Higher value transfers experience elevated friction"],
        hypotheses=["Bank transfer limit triggers secondary authentication drop-off"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        metric="funnel_conversion_rate",
        value="17.4%",
        comparison="Baseline is 89.2% for amounts < 50000 NGN",
        segment="amount_ngn >= 50000",
        time_period="Last 7 days",
    )

    assert af.metric == "funnel_conversion_rate"
    assert af.value == "17.4%"
    assert af.segment == "amount_ngn >= 50000"


def test_engineering_finding_schema() -> None:
    """Verify EngineeringFinding validates technical fields."""
    ev = Evidence(
        ledger_entry_id="led_003",
        source_type="jira",
        source_reference="issue_key:PAY-117",
        finding="Intermittent webhook timeout causing delayed state sync",
        support="PAY-117 status: In Progress, comments describe 30s timeout",
        confidence=EvidenceConfidence.HIGH,
    )

    ef = EngineeringFinding(
        finding="Webhook timeout explains delayed status reflection in app",
        facts=["PAY-117 is an open bug with priority High"],
        interpretations=["Core banking callback is timing out under peak load"],
        hypotheses=["Retries are eventually succeeding but causing apparent lag"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        issue_status="In Progress",
        technical_context="Core banking callback timeout of 30 seconds exceeded",
        relationship_to_problem="Directly accounts for app showing pending while bank processed",
        is_active_incident=True,
    )

    assert ef.issue_status == "In Progress"
    assert ef.is_active_incident is True
    assert "PAY-117" in ef.facts[0]


def test_specialist_result_container() -> None:
    """Verify SpecialistResult container tracks counts, role, and completion."""
    res = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[],
        overall_facts=["No tickets found for keyword 'crypto'"],
        overall_interpretations=["Crypto is not generating customer support volume"],
        overall_hypotheses=[],
        contradictions=[],
        unanswered_questions=["Are users seeking help elsewhere?"],
        limitations=["Search limited to last 30 days"],
        tool_call_count=3,
        llm_call_count=4,
        investigation_complete=True,
    )

    assert res.agent_role == "research"
    assert res.tool_call_count == 3
    assert res.llm_call_count == 4
    assert res.investigation_complete is True
    assert len(res.overall_facts) == 1
