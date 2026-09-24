"""Deterministic routing logic enforcing graph follow-up constraints."""

import logging

from app.orchestration.fingerprint import compute_canonical_task_fingerprint
from app.orchestration.state import InvestigationState

logger = logging.getLogger(__name__)

ROLE_LIMITS = {
    "research": {"tools": 10, "llm": 15},
    "analytics": {"tools": 8, "llm": 12},
    "engineering": {"tools": 8, "llm": 12},
}


def evaluate_follow_up_edge(state: InvestigationState) -> str:
    """Pure deterministic router deciding whether a targeted follow-up round is permitted.

    Returns:
        "targeted_follow_up" if all hard criteria pass, otherwise "finalize".
    """
    # 1. Round limit (strictly max 1 follow-up round, so round_index must be 0)
    if state.round_index >= state.max_rounds:
        logger.info(
            "Follow-up rejected: max rounds reached (%d/%d)", state.round_index, state.max_rounds
        )
        return (
            "pm_synthesis"
            if (state.customer_findings or state.analytics_findings or state.engineering_findings)
            else "finalize"
        )

    # 2. Assessment existence and blocking gaps
    if not state.assessment or not state.assessment.has_blocking_gaps:
        logger.info(
            "Follow-up rejected: no blocking gaps identified by assessment -> proceeding to PM synthesis"
        )
        return (
            "pm_synthesis"
            if (state.customer_findings or state.analytics_findings or state.engineering_findings)
            else "finalize"
        )

    # 3. Specialist recommendation validity
    role = state.assessment.recommended_specialist
    if role not in ROLE_LIMITS:
        logger.info("Follow-up rejected: invalid or null recommended specialist '%s'", role)
        return (
            "pm_synthesis"
            if (state.customer_findings or state.analytics_findings or state.engineering_findings)
            else "finalize"
        )

    # 4. Gap binding: recommended_gap must be non-empty and in identified_gaps
    gap = state.assessment.recommended_gap
    if not gap or gap not in state.assessment.identified_gaps:
        logger.info("Follow-up rejected: recommended_gap '%s' not found in identified_gaps", gap)
        return (
            "pm_synthesis"
            if (state.customer_findings or state.analytics_findings or state.engineering_findings)
            else "finalize"
        )

    # 5. Objective presence
    objective = state.assessment.recommended_objective or ""
    questions = state.assessment.recommended_questions or []
    if len(objective.strip()) < 5:
        logger.info("Follow-up rejected: recommended objective too short or missing")
        return (
            "pm_synthesis"
            if (state.customer_findings or state.analytics_findings or state.engineering_findings)
            else "finalize"
        )

    # 6. Task deduplication via canonical SHA-256 fingerprint
    fp = compute_canonical_task_fingerprint(role, objective, questions)
    if fp in state.executed_task_fingerprints:
        logger.info(
            "Follow-up rejected: task matches previously executed canonical fingerprint '%s'",
            fp[:10],
        )
        return (
            "pm_synthesis"
            if (state.customer_findings or state.analytics_findings or state.engineering_findings)
            else "finalize"
        )

    # 7. Specialist cumulative budget remainder
    limits = ROLE_LIMITS[role]
    if role == "research":
        used_tools = state.budget_usage.research_tool_calls
        used_llm = state.budget_usage.research_llm_calls
    elif role == "analytics":
        used_tools = state.budget_usage.analytics_tool_calls
        used_llm = state.budget_usage.analytics_llm_calls
    else:
        used_tools = state.budget_usage.engineering_tool_calls
        used_llm = state.budget_usage.engineering_llm_calls

    remaining_tools = limits["tools"] - used_tools
    remaining_llm = limits["llm"] - used_llm

    if remaining_tools < 1 or remaining_llm < 1:
        logger.info(
            "Follow-up rejected: specialist '%s' budget exhausted (tools remaining=%d, llm remaining=%d)",
            role,
            remaining_tools,
            remaining_llm,
        )
        return (
            "pm_synthesis"
            if (state.customer_findings or state.analytics_findings or state.engineering_findings)
            else "finalize"
        )

    logger.info(
        "Follow-up authorized for '%s' (tools remaining=%d, llm remaining=%d)",
        role,
        remaining_tools,
        remaining_llm,
    )
    return "targeted_follow_up"


def evaluate_pm_synthesis_edge(state: InvestigationState) -> str:
    """Route from pm_synthesis: proceed to critic if recommendation produced, else finalize."""
    if state.recommendation is not None:
        return "critic"
    logger.warning("PM synthesis produced no recommendation -> finalize directly")
    return "finalize"


def evaluate_critic_edge(state: InvestigationState) -> str:
    """Route from critic: finalize if PASS or max revisions reached, else pm_revision."""
    if not state.critic_reviews:
        return "finalize"

    latest_review = state.critic_reviews[-1]
    if latest_review.decision == "PASS":
        logger.info("Critic review PASSED -> finalizing")
        return "finalize"

    if state.revision_count >= state.max_revisions:
        logger.info(
            "Critic requested REVISE but max revisions reached (%d/%d) -> finalizing",
            state.revision_count,
            state.max_revisions,
        )
        return "finalize"

    logger.info(
        "Critic requested REVISE (round %d/%d) -> routing to pm_revision",
        state.revision_count,
        state.max_revisions,
    )
    return "pm_revision"


def evaluate_pm_revision_edge(state: InvestigationState) -> str:
    """Route every revised recommendation back through the Critic quality gate.

    Standard still permits only one PM revision, while Deep permits two. Both
    profiles must review the revised candidate before finalization so that the
    terminal status describes the recommendation actually shown to the user.
    """
    logger.info("PM revision produced a new candidate -> routing back to critic for final review")
    return "critic"
