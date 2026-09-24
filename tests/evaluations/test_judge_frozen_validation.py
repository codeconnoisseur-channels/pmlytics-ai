"""Enforcement and verification tests for the 10 dev calibration / 10 frozen validation judge split."""

import pytest
from evaluations.dataset.judge_cases import (
    DEV_CALIBRATION_CASES,
    FROZEN_VALIDATION_CASES,
    get_judge_cases,
)
from evaluations.reporting.aggregator import (
    compute_dimension_kappa_with_bootstrap,
)


def test_judge_case_split_distribution() -> None:
    """Verify exactly 10 dev calibration and 10 frozen validation cases exist."""
    assert len(DEV_CALIBRATION_CASES) == 10
    assert len(FROZEN_VALIDATION_CASES) == 10

    all_cases = get_judge_cases("all")
    assert len(all_cases) == 20

    dev_cases = get_judge_cases("dev_calibration")
    assert len(dev_cases) == 10
    for c in dev_cases:
        assert c.split == "dev_calibration"
        assert c.case_id.startswith("judge_dev_")

    val_cases = get_judge_cases("frozen_validation")
    assert len(val_cases) == 10
    for c in val_cases:
        assert c.split == "frozen_validation"
        assert c.case_id.startswith("judge_val_")


def test_frozen_validation_isolation_and_immutability() -> None:
    """Verify validation cases cannot be mutated or conflated with calibration."""
    val_cases = get_judge_cases("frozen_validation")
    case = val_cases[0]

    # Immutability via frozen Pydantic model
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        case.split = "dev_calibration"

    # Verify ID disjointness
    dev_ids = {c.case_id for c in DEV_CALIBRATION_CASES}
    val_ids = {c.case_id for c in FROZEN_VALIDATION_CASES}
    assert len(dev_ids & val_ids) == 0


def test_judge_qualification_on_frozen_validation() -> None:
    """Verify mathematical correctness of weighted kappa and bootstrap CI calculations on ordinal test data.

    NOTE: This test verifies that the statistical evaluator functions (quadratically weighted Cohen's Kappa
    and 1,000 bootstrap resamples) function correctly across the 10 frozen validation cases.
    It does NOT represent a live LLM-as-judge empirical qualification run against human raters.
    """
    val_cases = get_judge_cases("frozen_validation")
    dimensions = [
        "groundedness",
        "cross_source_reasoning",
        "contradiction_handling",
        "causal_discipline",
        "recommendation_defensibility",
    ]

    # Simulated qualified judge scores (close ordinal agreement with gold)
    # Rater 1: Gold ratings
    # Rater 2: Judge ratings with minor natural variance (+/- 1 on small minority)
    for dim in dimensions:
        gold_scores = [c.human_ground_truth_scores[dim] for c in val_cases]
        assert len(gold_scores) == 10

        # Judge evaluation matching gold with high accuracy
        judge_scores = list(gold_scores)
        # Introduce realistic single-point variance on 1 case
        judge_scores[2] = max(0, min(4, judge_scores[2] + (1 if judge_scores[2] < 4 else -1)))

        result = compute_dimension_kappa_with_bootstrap(
            dimension=dim,
            rater1_scores=gold_scores,
            rater2_scores=judge_scores,
            n_resamples=1000,
            seed=20260914,
        )

        assert result.dimension == dim
        assert result.weighted_kappa >= 0.75
        assert result.meets_qualification_threshold is True
        # Confidence interval bounds check
        assert result.ci_lower <= result.weighted_kappa <= result.ci_upper
