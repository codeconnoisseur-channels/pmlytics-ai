"""Finalization node computing deterministic investigation statuses."""

import logging

from app.domain.recommendation import ProductRecommendation
from app.orchestration.state import InvestigationState, InvestigationStateUpdate
from app.orchestration.validation import (
    ProvenanceValidationError,
    validate_critic_provenance,
    validate_investigation_evidence,
)
from app.tools.base import ToolError

logger = logging.getLogger(__name__)


def finalize_investigation_node(state: InvestigationState) -> InvestigationStateUpdate:
    """Compute deterministic final investigation status, enforce immutability, and validate provenance."""
    # 1. Validate final evidence provenance across all findings, recommendation, and critic reviews
    try:
        validate_investigation_evidence(state)
        for review in state.critic_reviews:
            validate_critic_provenance(review, state)
    except ProvenanceValidationError as pve:
        logger.error("Final provenance validation failure: %s", pve)
        prov_err = ToolError(
            error_type="upstream_error",
            message=str(pve),
            attempted_source=None,
        )
        return {
            "status": "failed",
            "sufficient_for_synthesis": False,
            "tool_errors": [prov_err],
        }

    # 2. Check usable evidence
    has_usable_evidence = bool(
        state.customer_findings or state.analytics_findings or state.engineering_findings
    )
    if not has_usable_evidence:
        logger.warning(
            "Investigation completed with zero usable evidence across all domains -> 'failed'"
        )
        return {
            "status": "failed",
            "sufficient_for_synthesis": False,
        }

    # 3. Check specialist completion: all specialists assigned in Phase 7 plan must have completed
    all_assigned_specialists_complete = True
    if state.plan is not None:
        for task in state.plan.tasks:
            if not state.specialist_completions.get(task.specialist, False):
                all_assigned_specialists_complete = False
                break
    else:
        all_assigned_specialists_complete = bool(state.specialist_completions) and all(
            state.specialist_completions.values()
        )

    has_tool_errors = bool(state.tool_errors)
    has_valid_recommendation = state.recommendation is not None
    latest_review = state.critic_reviews[-1] if state.critic_reviews else None
    critic_passed = latest_review is not None and latest_review.decision == "PASS"
    no_unresolved_critic_issues = latest_review is not None and len(latest_review.issues) == 0

    # 4. Invariant: status="completed" strictly requires ALL conditions
    if (
        state.sufficient_for_synthesis is True
        and all_assigned_specialists_complete
        and not has_tool_errors
        and has_valid_recommendation
        and critic_passed
        and no_unresolved_critic_issues
    ):
        logger.info(
            "Investigation completed successfully satisfying all Phase 8 invariants -> 'completed'"
        )
        return {
            "status": "completed",
            "sufficient_for_synthesis": True,
        }

    # 5. Handle max-revision exhaustion with unresolved Critic issues:
    # Preserve ProductRecommendation immutability: do NOT mutate in place.
    # Use model_copy(update=...) to produce replacement immutable recommendation.
    updated_recommendation: ProductRecommendation | None = state.recommendation
    updated_limitations: list[str] = []

    if (
        state.recommendation is not None
        and latest_review is not None
        and latest_review.decision == "REVISE"
        and len(latest_review.issues) > 0
    ):
        new_open_questions = [
            f"[Unresolved Critic Issue - {issue.category}] Claim: '{issue.claim}' | Problem: {issue.problem} (Required change: {issue.required_change})"
            for issue in latest_review.issues
        ]
        # Immutable copy
        updated_recommendation = state.recommendation.model_copy(
            update={
                "open_questions": [
                    *state.recommendation.open_questions,
                    *new_open_questions,
                ]
            }
        )
        for issue in latest_review.issues:
            limitation_str = f"Unresolved Critic issue ({issue.category}): {issue.problem}"
            if limitation_str not in state.limitations:
                updated_limitations.append(limitation_str)

    logger.info(
        "Investigation concluded as 'partial' (sufficient_for_synthesis=%s, "
        "assigned_complete=%s, tool_errors=%s, valid_rec=%s, critic_passed=%s)",
        state.sufficient_for_synthesis,
        all_assigned_specialists_complete,
        has_tool_errors,
        has_valid_recommendation,
        critic_passed,
    )

    update: InvestigationStateUpdate = {
        "status": "partial",
        "sufficient_for_synthesis": state.sufficient_for_synthesis
        and has_valid_recommendation
        and critic_passed,
    }
    if updated_recommendation != state.recommendation:
        update["recommendation"] = updated_recommendation
    if updated_limitations:
        update["limitations"] = updated_limitations

    return update
