"""Unit tests for judge calibration, weighted kappa, bootstrap CIs, and Wilcoxon testing."""

from unittest.mock import AsyncMock

import pytest
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.integrations.llm.client import LLMClient
from app.orchestration.state import InvestigationState
from evaluations.dataset.loader import get_scenario_by_id
from evaluations.evaluators.judge import (
    EvaluationJudgeReport,
    JudgeDimensionScore,
    LLMJudgeEvaluator,
)
from evaluations.reporting.aggregator import (
    compute_bootstrap_ci,
    compute_dimension_kappa_with_bootstrap,
    compute_paired_wilcoxon,
    compute_quadratically_weighted_kappa,
)


def test_quadratically_weighted_kappa_perfect_agreement() -> None:
    """Verify kappa is 1.0 when rater 1 and rater 2 scores are identical."""
    rater1 = [0, 1, 2, 3, 4, 3, 2, 1, 0, 4, 3, 2, 1, 0, 4]
    rater2 = [0, 1, 2, 3, 4, 3, 2, 1, 0, 4, 3, 2, 1, 0, 4]
    kappa = compute_quadratically_weighted_kappa(rater1, rater2)
    assert kappa == 1.0


def test_quadratically_weighted_kappa_high_ordinal_agreement() -> None:
    """Verify kappa >= 0.75 for very close ratings (mostly 0 distance, occasional 1)."""
    rater1 = [3, 4, 4, 3, 2, 4, 3, 2, 1, 4, 3, 4, 2, 1, 3, 4, 4, 2, 1, 0]
    rater2 = [3, 4, 3, 3, 2, 4, 3, 2, 1, 4, 4, 4, 2, 1, 3, 3, 4, 2, 1, 0]
    kappa = compute_quadratically_weighted_kappa(rater1, rater2)
    assert kappa >= 0.80


def test_quadratically_weighted_kappa_disagreement() -> None:
    """Verify kappa is low or negative when raters systematically disagree."""
    rater1 = [4, 4, 4, 3, 3, 4, 4, 3, 4, 3]
    rater2 = [0, 1, 0, 0, 1, 0, 1, 0, 1, 0]
    kappa = compute_quadratically_weighted_kappa(rater1, rater2)
    assert kappa < 0.2


def test_dimension_kappa_with_bootstrap_ci() -> None:
    """Verify dimension kappa returns bootstrap CI and threshold qualification."""
    rater1 = [3, 4, 4, 3, 2, 4, 3, 2, 1, 4, 3, 4, 2, 1, 3, 4, 4, 2, 1, 0]
    rater2 = [3, 4, 3, 3, 2, 4, 3, 2, 1, 4, 4, 4, 2, 1, 3, 3, 4, 2, 1, 0]
    result = compute_dimension_kappa_with_bootstrap("groundedness", rater1, rater2, n_resamples=500)

    assert result.dimension == "groundedness"
    assert result.weighted_kappa >= 0.75
    assert result.meets_qualification_threshold is True
    assert result.ci_lower <= result.weighted_kappa <= result.ci_upper


def test_paired_wilcoxon_signed_rank_test() -> None:
    """Verify paired Wilcoxon signed-rank test detects significant differences without pseudo-replication."""
    # Group A consistently scores higher than Group B across 15 scenarios
    group_a = [3.8, 3.7, 4.0, 3.9, 3.5, 3.6, 4.0, 3.8, 3.7, 3.9, 3.8, 3.6, 4.0, 3.7, 3.9]
    group_b = [2.8, 2.7, 3.0, 2.9, 2.5, 2.6, 3.0, 2.8, 2.7, 2.9, 2.8, 2.6, 3.0, 2.7, 2.9]

    result = compute_paired_wilcoxon(group_a, group_b)
    assert result.n_pairs == 15
    assert result.significant_at_05 is True
    assert result.p_value < 0.01

    # Identical groups produce p_value == 1.0
    identical_result = compute_paired_wilcoxon(group_a, group_a)
    assert identical_result.p_value == 1.0
    assert identical_result.significant_at_05 is False


def test_bootstrap_ci_mean_bounds() -> None:
    """Verify 95% bootstrap confidence interval encapsulates sample mean."""
    data = [10.0, 12.0, 11.0, 13.0, 9.0, 14.0, 11.5, 10.5]
    ci = compute_bootstrap_ci(data, n_resamples=500)
    assert ci.ci_lower <= ci.mean <= ci.ci_upper
    assert ci.std_dev > 0.0


@pytest.mark.asyncio
async def test_llm_judge_evaluator_success_and_fallback() -> None:
    """Verify LLMJudgeEvaluator produces structured score report and fallback when no rec is present."""
    mock_client = AsyncMock(spec=LLMClient)
    judge = LLMJudgeEvaluator(llm_client=mock_client)
    scenario = get_scenario_by_id("scn_001")

    # Fallback when recommendation is None
    empty_state = InvestigationState(investigation_id="inv_empty", user_query="test")
    report = await judge.evaluate(empty_state, scenario)
    assert report.overall_mean_score == 0.0
    assert "NO_RECOMMENDATION_PRODUCED" in report.identified_flaws

    # When recommendation is present, mock LLM returns valid JSON
    state_with_rec = InvestigationState(
        investigation_id="inv_rec",
        user_query="test",
        recommendation=ProductRecommendation(
            problem_statement="Problem statement explaining customer issues.",
            why_it_matters="Impact statement explaining why it matters.",
            affected_users="Segment A users",
            factual_observations=["Fact 1 observed"],
            inferences=["Inference 1 deduced"],
            hypotheses=["Hypothesis 1 proposed"],
            evidence=[
                Evidence(
                    ledger_entry_id="led_001",
                    source_type="zendesk",
                    source_reference="zen_001",
                    finding="Verified finding",
                    support="Verified support",
                    confidence=EvidenceConfidence.HIGH,
                )
            ],
            recommendation="Recommended product action to fix the bug.",
            recommendation_type="technical_remediation",
            success_metrics=["Metric 1"],
            risks=["Risk 1"],
            confidence="high",
            open_questions=[],
        ),
    )

    expected_report = EvaluationJudgeReport(
        groundedness=JudgeDimensionScore(score=4, reasoning="Completely grounded in evidence."),
        cross_source_reasoning=JudgeDimensionScore(
            score=3, reasoning="Good synthesis across sources."
        ),
        contradiction_handling=JudgeDimensionScore(
            score=4, reasoning="Accurately noted contradiction."
        ),
        causal_discipline=JudgeDimensionScore(score=3, reasoning="Careful causal framing."),
        recommendation_defensibility=JudgeDimensionScore(
            score=4, reasoning="Actionable and low risk."
        ),
        identified_flaws=[],
        overall_mean_score=3.6,
    )

    mock_client.complete_structured.return_value = expected_report

    scored_report = await judge.evaluate(state_with_rec, scenario)
    assert scored_report.groundedness.score == 4
    assert scored_report.overall_mean_score == 3.6
    assert scored_report.identified_flaws == []
