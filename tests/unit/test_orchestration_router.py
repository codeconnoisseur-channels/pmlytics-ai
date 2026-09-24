"""Unit tests for the deterministic routing logic."""

from app.orchestration.fingerprint import compute_canonical_task_fingerprint
from app.orchestration.nodes.router import evaluate_follow_up_edge
from app.orchestration.state import (
    EvidenceAssessment,
    GraphBudgetUsage,
    InvestigationState,
)


def _make_assessment(
    gaps: list[str] | None = None,
    recommended_gap: str | None = None,
    role: str | None = "research",
    objective: str = "Search for additional tickets with timeout status",
    questions: list[str] | None = None,
) -> EvidenceAssessment:
    identified = gaps or ["Lack of customer confirmation regarding switch timeout frequency"]
    rec_gap = recommended_gap or identified[0]
    return EvidenceAssessment(
        sufficient_for_synthesis=False,
        has_blocking_gaps=True,
        identified_gaps=identified,
        recommended_specialist=role,  # type: ignore[arg-type]
        recommended_gap=rec_gap,
        recommended_objective=objective,
        recommended_questions=questions or ["Are there additional tickets?"],
    )


def test_router_authorizes_valid_follow_up() -> None:
    """Verify that a valid gap, unexhausted budget, and new task routes to targeted_follow_up."""
    assessment = _make_assessment()
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        round_index=0,
        assessment=assessment,
        budget_usage=GraphBudgetUsage(
            research_tool_calls=5,  # 10 - 5 = 5 remaining
            research_llm_calls=7,  # 15 - 7 = 8 remaining
        ),
    )

    route = evaluate_follow_up_edge(state)
    assert route == "targeted_follow_up"


def test_router_rejects_when_round_index_at_max() -> None:
    """Verify that router rejects follow-up when max rounds is reached."""
    assessment = _make_assessment()
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        round_index=1,  # Already executed round 1!
        max_rounds=1,
        assessment=assessment,
    )

    route = evaluate_follow_up_edge(state)
    assert route == "finalize"


def test_router_rejects_when_gap_not_in_identified_gaps() -> None:
    """Verify that router rejects follow-up if recommended_gap is not in identified_gaps."""
    assessment = _make_assessment(
        gaps=["Gap 1: Latency data missing"],
        recommended_gap="Gap 2: Unrelated gap hallucinated by model",
    )
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        round_index=0,
        assessment=assessment,
    )

    route = evaluate_follow_up_edge(state)
    assert route == "finalize"


def test_router_rejects_duplicate_canonical_task() -> None:
    """Verify that router rejects follow-up if canonical task hash was already executed."""
    role = "research"
    objective = "Search for additional tickets with timeout status"
    questions = ["Are there additional tickets?"]
    fp = compute_canonical_task_fingerprint(role, objective, questions)

    assessment = _make_assessment(role=role, objective=objective, questions=questions)
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        round_index=0,
        assessment=assessment,
        executed_task_fingerprints={fp},  # Already executed!
    )

    route = evaluate_follow_up_edge(state)
    assert route == "finalize"


def test_router_rejects_when_specialist_budget_exhausted() -> None:
    """Verify that router rejects follow-up if specialist has 0 tool or 0 LLM calls remaining."""
    assessment = _make_assessment(role="analytics")
    state = InvestigationState(
        investigation_id="inv_test",
        user_query="Why are transfers delayed?",
        round_index=0,
        assessment=assessment,
        budget_usage=GraphBudgetUsage(
            analytics_tool_calls=8,  # Limit is 8 -> 0 remaining!
            analytics_llm_calls=5,
        ),
    )

    route = evaluate_follow_up_edge(state)
    assert route == "finalize"
