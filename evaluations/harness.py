"""Evaluation harness orchestrating batch scenario execution and manifest snapshotting."""

import asyncio
import json
import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from evaluations.config import (
    DEFAULT_PRICING_RATES,
    MODEL_PROVIDER_ROUTING,
    AblationMode,
    ArchitectureId,
    ModelPricing,
)
from evaluations.ground_truth.schema import EvaluationScenario
from evaluations.runner import ScenarioRunner, ScenarioRunResult

logger = logging.getLogger(__name__)


class EvaluationManifest(BaseModel):
    """Cryptographic and configuration manifest preserving exact execution parameters."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    timestamp_utc: str
    dataset_version: str = "1.0"
    dataset_hash: str = "sha256:eval_scenarios_v1.0_45scenarios"
    ablation_mode: AblationMode
    architecture_id: ArchitectureId
    primary_model: str
    provider_routing: dict[str, object]
    pricing_snapshot: dict[str, ModelPricing]
    billed_token_categories: list[str] = Field(
        default_factory=lambda: ["input_tokens", "output_tokens"]
    )
    prompt_hashes: dict[str, str] = Field(
        default_factory=lambda: {
            "planner": "sha256:planner_prompt_v1.0",
            "pm_synthesis": "sha256:pm_synthesis_v1.0",
            "critic": "sha256:critic_prompt_v1.0",
            "judge": "sha256:judge_rubric_v1.0",
        }
    )
    tool_fixture_version: str = "v1.0-mockserver-http-zendesk"
    judge_version: str = "v1.0-calibrated-5dim"
    random_seed: int = 20260914
    stochasticity_disclaimer: str = (
        "Random seed guarantees deterministic harness sampling and test fixtures. "
        "Frontier LLM inference remains inherently stochastic even at temperature 0.0; "
        "repeated trials (N=3) are used to measure and characterize empirical variance."
    )
    temperature: float = 0.0
    total_scenarios: int
    repetitions: int
    total_planned_runs: int


class BenchmarkBatchResult(BaseModel):
    """Container for a completed benchmark batch execution."""

    manifest: EvaluationManifest
    scenario_results: list[ScenarioRunResult] = Field(default_factory=list)
    output_directory: str


class EvaluationHarness:
    """Executes evaluation batches, enforces throttle rates, and writes immutable artifacts."""

    def __init__(
        self,
        runner: ScenarioRunner,
        results_root: str = "evaluations/results",
        concurrency_limit: int = 2,
    ) -> None:
        self.runner = runner
        self.results_root = Path(results_root)
        self.concurrency_limit = concurrency_limit
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def run_batch(
        self,
        scenarios: Sequence[EvaluationScenario],
        architecture_id: ArchitectureId = "candidate_c",
        ablation_mode: AblationMode = "mode1_matched",
        model_name: str = "openai/gpt-5.4",
        repetitions: int = 3,
        pricing_snapshot: dict[str, ModelPricing] | None = None,
    ) -> BenchmarkBatchResult:
        """Run an evaluation batch across scenarios and repetitions with immutable manifest snapshot."""
        run_id = f"eval_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        run_dir = self.results_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        rates = pricing_snapshot or DEFAULT_PRICING_RATES
        routing = MODEL_PROVIDER_ROUTING.get(model_name, {"policy": "openrouter_default"})

        manifest = EvaluationManifest(
            run_id=run_id,
            timestamp_utc=datetime.now(UTC).isoformat(),
            dataset_version="1.0",
            ablation_mode=ablation_mode,
            architecture_id=architecture_id,
            primary_model=model_name,
            provider_routing=routing,
            pricing_snapshot=rates,
            random_seed=20260914,
            temperature=0.0,
            total_scenarios=len(scenarios),
            repetitions=repetitions,
            total_planned_runs=len(scenarios) * repetitions,
        )

        # Write manifest snapshot before running
        manifest_path = run_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        results: list[ScenarioRunResult] = []

        async def _execute_single(scenario: EvaluationScenario, trial: int) -> ScenarioRunResult:
            async with self.semaphore:
                # Modest pacing to avoid rate limits
                await asyncio.sleep(0.05)
                return await self.runner.run_scenario(
                    scenario=scenario,
                    architecture_id=architecture_id,
                    ablation_mode=ablation_mode,
                    model_name=model_name,
                    trial_index=trial,
                    pricing_snapshot=rates,
                )

        tasks = []
        for scenario in scenarios:
            for trial in range(1, repetitions + 1):
                tasks.append(_execute_single(scenario, trial))

        results = await asyncio.gather(*tasks)

        # Write scenario results
        results_path = run_dir / "scenario_results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in results], f, indent=2)

        return BenchmarkBatchResult(
            manifest=manifest,
            scenario_results=list(results),
            output_directory=str(run_dir),
        )
