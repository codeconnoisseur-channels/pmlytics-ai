from app.domain.critic import CriticReview
from app.domain.provenance import source_references_match
from app.orchestration.state import (
    InvestigationState,
    ProvenanceCollisionError,
    ProvenanceValidationError,
)

__all__ = [
    "ProvenanceCollisionError",
    "ProvenanceValidationError",
    "validate_critic_provenance",
    "validate_investigation_evidence",
]


def validate_critic_provenance(review: CriticReview, state: InvestigationState) -> None:
    """Validate that every ledger ID referenced by a CriticReview exists in the ledger.

    Invariants:
    1. Every id in issue.supporting_ledger_entry_ids must exist in state.evidence_ledger_entries.
    2. Zero fabricated or unretrieved citations allowed.

    Raises:
        ProvenanceValidationError: If any ledger reference is unknown.
    """
    valid_ids = sorted(state.evidence_ledger_entries.keys())
    for issue in review.issues:
        for ledger_id in issue.supporting_ledger_entry_ids:
            if ledger_id not in state.evidence_ledger_entries:
                raise ProvenanceValidationError(
                    f"Critic provenance violation: issue '{issue.category}' references unknown "
                    f"supporting_ledger_entry_id '{ledger_id}'. Valid retrieved IDs: {valid_ids}"
                )


def validate_investigation_evidence(state: InvestigationState) -> None:
    """Enforce tripartite provenance across all aggregated specialist findings and recommendation.

    Invariants:
    1. Every evidence ledger_entry_id must exist in state.evidence_ledger_entries.
    2. Finding/recommendation evidence source_type must match entry.source_type exactly.
    3. Finding/recommendation evidence source_reference must match entry.source_reference exactly.

    Raises:
        ProvenanceValidationError: If any evidence item is unverified or mismatched.
    """
    all_findings = state.customer_findings + state.analytics_findings + state.engineering_findings
    for finding in all_findings:
        for ev in finding.evidence:
            entry = state.evidence_ledger_entries.get(ev.ledger_entry_id)
            if entry is None:
                valid_ids = sorted(state.evidence_ledger_entries.keys())
                raise ProvenanceValidationError(
                    f"Graph provenance violation: evidence item references unknown "
                    f"ledger_entry_id '{ev.ledger_entry_id}'. Valid retrieved IDs: {valid_ids}"
                )
            if ev.source_type != entry.source_type:
                raise ProvenanceValidationError(
                    f"Graph provenance violation for '{ev.ledger_entry_id}': "
                    f"expected source_type '{entry.source_type}', got '{ev.source_type}'."
                )
            if not source_references_match(
                entry.source_type, entry.source_reference, ev.source_reference
            ):
                raise ProvenanceValidationError(
                    f"Graph provenance violation for '{ev.ledger_entry_id}': "
                    f"expected source_reference '{entry.source_reference}', got '{ev.source_reference}'."
                )

    if state.recommendation is not None:
        for ev in state.recommendation.evidence:
            entry = state.evidence_ledger_entries.get(ev.ledger_entry_id)
            if entry is None:
                valid_ids = sorted(state.evidence_ledger_entries.keys())
                raise ProvenanceValidationError(
                    f"Graph provenance violation: recommendation references unknown "
                    f"ledger_entry_id '{ev.ledger_entry_id}'. Valid retrieved IDs: {valid_ids}"
                )
            if ev.source_type != entry.source_type:
                raise ProvenanceValidationError(
                    f"Graph provenance violation in recommendation for '{ev.ledger_entry_id}': "
                    f"expected source_type '{entry.source_type}', got '{ev.source_type}'."
                )
            if not source_references_match(
                entry.source_type, entry.source_reference, ev.source_reference
            ):
                raise ProvenanceValidationError(
                    f"Graph provenance violation in recommendation for '{ev.ledger_entry_id}': "
                    f"expected source_reference '{entry.source_reference}', got '{ev.source_reference}'."
                )
