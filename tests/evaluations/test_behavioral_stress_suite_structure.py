"""Unit tests verifying structural integrity and behavioral invariant contracts of the stress suite."""

import pytest
from evaluations.dataset.evaluator_stress_suite import (
    STRESS_CASES,
    BehavioralCheckType,
    BehavioralInvariant,
    EvaluatorStressCase,
)


def test_stress_suite_counts_and_uniqueness() -> None:
    """Verify exactly 15 unique, handcrafted behavioral stress cases exist."""
    assert len(STRESS_CASES) == 15

    case_ids = [c.case_id for c in STRESS_CASES]
    assert len(set(case_ids)) == 15, "Duplicate case_id in stress suite"

    # Verify each case has at least one behavioral invariant declared
    for case in STRESS_CASES:
        assert isinstance(case, EvaluatorStressCase)
        assert len(case.invariants) >= 1
        assert len(case.behavior_under_test) > 0
        assert len(case.user_query) > 0
        assert len(case.evidence_ledger_entries) > 0
        assert case.candidate_recommendation is not None


def test_behavioral_invariants_predeclared_and_observable() -> None:
    """Verify all behavioral invariants declare observable behaviors rather than scalar gold scores."""
    valid_dimensions = {
        "groundedness",
        "cross_source_reasoning",
        "contradiction_handling",
        "causal_discipline",
        "recommendation_defensibility",
    }

    for case in STRESS_CASES:
        for inv in case.invariants:
            assert isinstance(inv, BehavioralInvariant)
            assert inv.target_dimension in valid_dimensions
            assert isinstance(inv.check_type, BehavioralCheckType)
            assert len(inv.predeclared_expected_behavior) > 10
            assert len(inv.behavior_name) > 3


def test_stress_suite_immutability() -> None:
    """Verify that stress cases are immutable Pydantic models."""
    from pydantic import ValidationError

    case = STRESS_CASES[0]
    with pytest.raises(ValidationError):
        case.case_id = "mutated_id"
