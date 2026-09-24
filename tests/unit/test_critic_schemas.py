"""Unit tests for Critic domain schemas and provenance validation."""

from datetime import UTC, datetime

import pytest
from app.domain.critic import (
    CriticIssue,
    CriticReview,
)
from app.domain.zendesk import ZendeskTicket
from app.orchestration.state import (
    EvidenceLedgerEntry,
    InvestigationState,
    ProvenanceValidationError,
)
from app.orchestration.validation import validate_critic_provenance


def _make_sample_ticket() -> ZendeskTicket:
    now = datetime.now(UTC)
    return ZendeskTicket(
        id=101,
        subject="Transfer delayed",
        description="Desc 101",
        status="open",
        priority="normal",
        channel="web",
        created_at=now,
        updated_at=now,
        requester_id="usr_000001",
        tags=[],
    )


def test_critic_issue_valid() -> None:
    issue = CriticIssue(
        category="causal_overreach",
        claim="Delayed callbacks caused all customer drop-offs.",
        problem="The PM claims delayed callbacks caused all customer drop-offs without baseline proof.",
        supporting_ledger_entry_ids=["analytics:r0:led_001"],
        required_change="Rephrase from 'caused' to 'associated with'.",
    )
    assert issue.category == "causal_overreach"
    assert issue.supporting_ledger_entry_ids == ["analytics:r0:led_001"]


def test_critic_review_pass() -> None:
    review = CriticReview(
        decision="PASS",
        issues=[],
        overall_assessment="All claims are corroborated and causality is appropriately restrained.",
        required_changes=[],
    )
    assert review.decision == "PASS"
    assert len(review.issues) == 0


def test_critic_review_revise() -> None:
    review = CriticReview(
        decision="REVISE",
        issues=[
            CriticIssue(
                category="unsupported_claim",
                claim="80% of users churned due to delays",
                problem="Claim that 80% of users churned has no cited evidence.",
                supporting_ledger_entry_ids=[],
                required_change="Remove or ground in PostHog query result.",
            )
        ],
        overall_assessment="Unsupported quantitative claim requires revision.",
        required_changes=["Remove 80% churn claim or cite ledger entry."],
    )
    assert review.decision == "REVISE"
    assert len(review.issues) == 1


def test_critic_provenance_validation_passes() -> None:
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why did transfers fail?",
        evidence_ledger_entries={
            "analytics:r0:led_001": EvidenceLedgerEntry(
                ledger_entry_id="analytics:r0:led_001",
                source_type="zendesk",
                source_reference="ticket_id:101",
                retrieved_at=datetime.now(UTC),
                data_summary="Drop-off at step 2",
                typed_payload=_make_sample_ticket(),
            )
        },
    )
    review = CriticReview(
        decision="REVISE",
        issues=[
            CriticIssue(
                category="causal_overreach",
                claim="Claim under review",
                problem="Issue text describing problem in detail",
                supporting_ledger_entry_ids=["analytics:r0:led_001"],
                required_change="Fix text by softening claim",
            )
        ],
        overall_assessment="Assessment feedback",
        required_changes=["Change"],
    )
    validate_critic_provenance(review, state)  # Should pass without error


def test_critic_provenance_validation_catches_unretrieved_id() -> None:
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why did transfers fail?",
        evidence_ledger_entries={
            "analytics:r0:led_001": EvidenceLedgerEntry(
                ledger_entry_id="analytics:r0:led_001",
                source_type="zendesk",
                source_reference="ticket_id:101",
                retrieved_at=datetime.now(UTC),
                data_summary="Drop-off at step 2",
                typed_payload=_make_sample_ticket(),
            )
        },
    )
    review = CriticReview(
        decision="REVISE",
        issues=[
            CriticIssue(
                category="unsupported_claim",
                claim="Fabricated claim",
                problem="Fabricated citation problem",
                supporting_ledger_entry_ids=["fake:r0:led_999"],
                required_change="Fix citation",
            )
        ],
        overall_assessment="Assessment feedback",
        required_changes=["Change"],
    )
    with pytest.raises(
        ProvenanceValidationError, match="unknown supporting_ledger_entry_id 'fake:r0:led_999'"
    ):
        validate_critic_provenance(review, state)
