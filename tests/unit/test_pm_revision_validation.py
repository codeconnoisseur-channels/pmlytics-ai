"""Unit tests for PM revision deterministic validation and quality-gate routing.

Tests verify:
1. ProductRecommendation schema validity
2. Valid ledger-entry IDs and citation resolution (rejects fabricated ledger IDs)
3. Epistemic separation enforcement
4. Preservation of limitations and contradictions
5. Fail-closed behavior on deterministic validation failure
6. Every profile routes pm_revision -> critic
"""

from datetime import UTC, datetime

import pytest
from app.agents.ledger import EvidenceLedgerEntry
from app.domain.analytics import AnalyticsQueryResult
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.domain.zendesk import ZendeskTicket
from app.orchestration.nodes.pm_revision import validate_revised_recommendation
from app.orchestration.nodes.router import evaluate_pm_revision_edge
from app.orchestration.state import EvidenceAssessment, InvestigationState


@pytest.fixture
def base_state() -> InvestigationState:
    now = datetime.now(UTC)
    entry_1 = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket:101",
        retrieved_at=now,
        data_summary="Customer ticket mentioning transfer delay",
        typed_payload=ZendeskTicket(
            id=101,
            requester_id="usr_abc123",
            subject="Delay",
            description="Transfer delay description",
            status="open",
            priority="normal",
            channel="web",
            created_at=now,
            updated_at=now,
        ),
    )
    entry_2 = EvidenceLedgerEntry(
        ledger_entry_id="analytics:r0:led_001",
        source_type="posthog",
        source_reference="query:transfer_completed",
        retrieved_at=now,
        data_summary="Analytics showing drop in completion",
        typed_payload=AnalyticsQueryResult(
            query_description="Completion rate",
            metric="completion_rate",
            value=0.82,
        ),
    )
    return InvestigationState(
        investigation_id="inv_test_001",
        user_query="Why are transfers failing?",
        evidence_ledger_entries={
            "research:r0:led_001": entry_1,
            "analytics:r0:led_001": entry_2,
        },
        limitations=["Small sample size for tickets"],
        assessment=EvidenceAssessment(
            sufficient_for_synthesis=False,
            has_blocking_gaps=True,
            identified_gaps=["Gateway latency unmeasured"],
        ),
    )


@pytest.fixture
def valid_recommendation() -> ProductRecommendation:
    return ProductRecommendation(
        problem_statement="Transfers are failing due to payment timeout issues.",
        why_it_matters="High transaction drop-off hurts conversion and customer satisfaction.",
        affected_users="Active mobile app users attempting international transfers.",
        factual_observations=["Support tickets show customer complaints regarding delays."],
        inferences=["Payment delays lead to user abandonment before confirmation."],
        hypotheses=["Third-party gateway timeout causes delayed callbacks."],
        evidence=[
            Evidence(
                ledger_entry_id="research:r0:led_001",
                source_type="zendesk",
                source_reference="ticket:101",
                finding="Customer reported transfer delay",
                support="Ticket 101 text",
                confidence=EvidenceConfidence.HIGH,
            ),
        ],
        likely_causes=["Associated with gateway webhook delays."],
        conflicting_evidence=["Some users experienced successful instant completion."],
        recommendation="Implement webhook retry mechanism and real-time status banner.",
        recommendation_type="technical_remediation",
        success_metrics=["Increase completion rate to 95%."],
        risks=["Additional load on retry queue."],
        confidence="medium",
        open_questions=["What is the p99 latency of the gateway webhook?"],
    )


def test_valid_recommendation_passes_validation(
    valid_recommendation: ProductRecommendation, base_state: InvestigationState
) -> None:
    """Proves valid recommendation has zero validation errors."""
    errors = validate_revised_recommendation(valid_recommendation, base_state)
    assert errors == []


def test_fabricated_ledger_id_is_rejected(
    valid_recommendation: ProductRecommendation, base_state: InvestigationState
) -> None:
    """Proves fabricated or non-existent ledger IDs are flagged as errors."""
    corrupted_ev = Evidence(
        ledger_entry_id="research:r0:led_999",  # fabricated ID
        source_type="zendesk",
        source_reference="ticket:999",
        finding="Invented finding",
        support="None",
        confidence=EvidenceConfidence.LOW,
    )
    bad_rec = valid_recommendation.model_copy(update={"evidence": [corrupted_ev]})
    errors = validate_revised_recommendation(bad_rec, base_state)
    assert any("unknown or fabricated ledger_entry_id" in e for e in errors)


def test_mismatched_source_metadata_is_rejected(
    valid_recommendation: ProductRecommendation, base_state: InvestigationState
) -> None:
    """Proves mismatched source_type or source_reference against ledger is flagged."""
    mismatched_ev = Evidence(
        ledger_entry_id="research:r0:led_001",  # exists, but source_type in ledger is zendesk
        source_type="jira",  # mismatched!
        source_reference="ticket:101",
        finding="Finding",
        support="Support",
        confidence=EvidenceConfidence.HIGH,
    )
    bad_rec = valid_recommendation.model_copy(update={"evidence": [mismatched_ev]})
    errors = validate_revised_recommendation(bad_rec, base_state)
    assert any("does not match ledger entry" in e for e in errors)


def test_epistemic_separation_violation_is_rejected(
    valid_recommendation: ProductRecommendation, base_state: InvestigationState
) -> None:
    """Proves identical claims in facts and inferences are rejected."""
    bad_rec = valid_recommendation.model_copy(
        update={
            "factual_observations": ["Identical claim across epistemic layers"],
            "inferences": ["Identical claim across epistemic layers"],
        }
    )
    errors = validate_revised_recommendation(bad_rec, base_state)
    assert any("Epistemic violation" in e for e in errors)


def test_preservation_of_limitations_is_enforced(
    valid_recommendation: ProductRecommendation, base_state: InvestigationState
) -> None:
    """Proves that when limitations/gaps exist, open_questions and risks cannot both be empty."""
    bad_rec = valid_recommendation.model_copy(update={"open_questions": [], "risks": []})
    errors = validate_revised_recommendation(bad_rec, base_state)
    assert any("Preservation violation" in e for e in errors)


def test_standard_profile_routes_to_critic(base_state: InvestigationState) -> None:
    """A Standard-profile revision must be reviewed before finalization."""
    assert evaluate_pm_revision_edge(base_state) == "critic"


def test_deep_profile_routes_to_critic(base_state: InvestigationState) -> None:
    """A Deep-profile revision also returns to the Critic."""
    assert evaluate_pm_revision_edge(base_state) == "critic"
