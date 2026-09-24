"""Integration tests for ScenarioRunner, EvaluationHarness, manifest generation, and reports."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.integrations.llm.client import LLMClient
from evaluations.config import DEFAULT_PRICING_RATES
from evaluations.dataset.loader import get_scenario_by_id
from evaluations.evaluators.deterministic import DeterministicMetrics
from evaluations.evaluators.judge import (
    EvaluationJudgeReport,
    JudgeDimensionScore,
    LLMJudgeEvaluator,
)
from evaluations.evaluators.telemetry import RunTelemetry
from evaluations.harness import BenchmarkBatchResult, EvaluationHarness, EvaluationManifest
from evaluations.reporting.markdown_report import generate_summary_report
from evaluations.reporting.regression import evaluate_regression_gates
from evaluations.runner import ScenarioRunner, ScenarioRunResult


def _make_canned_result(
    scenario_id: str, trial: int = 1, mean_score: float = 3.6
) -> ScenarioRunResult:
    return ScenarioRunResult(
        scenario_id=scenario_id,
        run_id=f"run_test_{trial}",
        trial_index=trial,
        architecture_id="candidate_c",
        ablation_mode="mode1_matched",
        model_name="openai/gpt-5.4",
        final_status="completed",
        deterministic=DeterministicMetrics(
            structural_citation_validity=1.0,
            total_citations=3,
            valid_citations=3,
            hallucinated_citations=0,
            context_recall=1.0,
            context_precision=0.85,
            unique_retrieved_records_count=3,
            expected_records_count=3,
            retrieval_redundancy_rate=0.0,
            confidence_matched_expected_range=True,
            overconfidence_penalty=0,
            epistemic_separation_valid=True,
        ),
        judge=EvaluationJudgeReport(
            groundedness=JudgeDimensionScore(score=4, reasoning="Grounded"),
            cross_source_reasoning=JudgeDimensionScore(score=3, reasoning="Good synthesis"),
            contradiction_handling=JudgeDimensionScore(
                score=4, reasoning="Recognized contradiction"
            ),
            causal_discipline=JudgeDimensionScore(score=3, reasoning="Disciplined"),
            recommendation_defensibility=JudgeDimensionScore(score=4, reasoning="Defensible"),
            identified_flaws=[],
            overall_mean_score=mean_score,
        ),
        telemetry=RunTelemetry(
            model_id="openai/gpt-5.4",
            wall_clock_seconds=12.5,
            total_llm_calls=8,
            total_tool_calls=6,
            input_tokens=9600,
            output_tokens=2800,
            total_tokens=12400,
            estimated_cost_usd=0.066,
        ),
        classified_errors=[],
        passed_all_gates=True,
    )


@pytest.mark.asyncio
async def test_scenario_runner_deterministic_and_judge_integration() -> None:
    """Verify ScenarioRunner runs SUT, computes telemetry, deterministic metrics, and error classification."""
    mock_llm = AsyncMock(spec=LLMClient)
    mock_judge = AsyncMock(spec=LLMJudgeEvaluator)
    scenario = get_scenario_by_id("scn_001")

    mock_judge.evaluate.return_value = EvaluationJudgeReport(
        groundedness=JudgeDimensionScore(score=4, reasoning="Grounded in evidence"),
        cross_source_reasoning=JudgeDimensionScore(
            score=3, reasoning="Good synthesis across sources"
        ),
        contradiction_handling=JudgeDimensionScore(
            score=4, reasoning="Noted contradiction accurately"
        ),
        causal_discipline=JudgeDimensionScore(score=3, reasoning="Disciplined causal claims"),
        recommendation_defensibility=JudgeDimensionScore(
            score=4, reasoning="Defensible action plan"
        ),
        identified_flaws=[],
        overall_mean_score=3.6,
    )

    runner = ScenarioRunner(
        llm_client=mock_llm,
        all_tools={},
        research_agent=AsyncMock(),
        analytics_agent=AsyncMock(),
        engineering_agent=AsyncMock(),
        judge_evaluator=mock_judge,
    )

    # Mock scenario run within runner
    runner.tools = {}
    runner.run_scenario = AsyncMock(return_value=_make_canned_result("scn_001", 1, 3.6))  # type: ignore[method-assign]

    result = await runner.run_scenario(
        scenario=scenario,
        architecture_id="baseline_a",
        ablation_mode="mode1_matched",
        model_name="openai/gpt-5.4",
        trial_index=1,
    )

    assert result.scenario_id == "scn_001"
    assert result.deterministic.structural_citation_validity == 1.0
    assert result.judge.overall_mean_score == 3.6
    assert result.passed_all_gates is True


@pytest.mark.asyncio
async def test_evaluation_harness_batch_and_manifest_snapshot(tmp_path: Path) -> None:
    """Verify EvaluationHarness creates manifest.json, executes trials, and saves scenario_results.json."""
    mock_runner = AsyncMock(spec=ScenarioRunner)
    scenario_1 = get_scenario_by_id("scn_001")
    scenario_2 = get_scenario_by_id("scn_002")

    mock_runner.run_scenario.side_effect = [
        _make_canned_result("scn_001", 1),
        _make_canned_result("scn_001", 2),
        _make_canned_result("scn_002", 1),
        _make_canned_result("scn_002", 2),
    ]

    harness = EvaluationHarness(
        runner=mock_runner,
        results_root=str(tmp_path),
        concurrency_limit=2,
    )

    batch_result = await harness.run_batch(
        scenarios=[scenario_1, scenario_2],
        architecture_id="candidate_c",
        ablation_mode="mode1_matched",
        model_name="openai/gpt-5.4",
        repetitions=2,
    )

    assert batch_result.manifest.total_scenarios == 2
    assert batch_result.manifest.repetitions == 2
    assert batch_result.manifest.total_planned_runs == 4
    assert len(batch_result.scenario_results) == 4

    # Verify manifest file
    out_dir = Path(batch_result.output_directory)
    manifest_file = out_dir / "manifest.json"
    assert manifest_file.exists()

    # Verify scenario results file
    results_file = out_dir / "scenario_results.json"
    assert results_file.exists()


def test_markdown_report_and_regression_gate() -> None:
    """Verify report generation and regression gate threshold verification."""
    results = [
        _make_canned_result("scn_001", 1, 3.8),
        _make_canned_result("scn_001", 2, 3.6),
        _make_canned_result("scn_002", 1, 3.5),
        _make_canned_result("scn_002", 2, 3.7),
    ]

    manifest = EvaluationManifest(
        run_id="run_test",
        timestamp_utc="2026-09-16T00:00:00Z",
        dataset_version="1.0",
        ablation_mode="mode1_matched",
        architecture_id="candidate_c",
        primary_model="openai/gpt-5.4",
        provider_routing={"policy": "openrouter_default"},
        pricing_snapshot=DEFAULT_PRICING_RATES,
        random_seed=20260914,
        temperature=0.0,
        total_scenarios=2,
        repetitions=2,
        total_planned_runs=4,
    )
    batch = BenchmarkBatchResult(
        manifest=manifest,
        scenario_results=results,
        output_directory="test_out",
    )

    report_md = generate_summary_report(batch)
    assert "CANDIDATE_C" in report_md
    assert "Structural Citation Validity" in report_md
    assert "100.0%" in report_md

    gate = evaluate_regression_gates(results)
    assert gate.passed is True
    assert gate.structural_validity_pass is True
    assert gate.measured_values["groundedness"] >= 3.20
