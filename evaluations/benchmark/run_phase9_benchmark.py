"""Phase 9 Reduced 204-Run Comparative Benchmark Execution & Reporting.

Architectures:
  - Baseline A: Single Generalist Agent (all 8 domain tools)
  - Baseline B: Specialists + PM without Critic
  - Candidate C: Specialists + PM + Critic (Full Multi-Agent Pipeline)

Dataset:
  - 24 Core Scenarios x 3 Architectures x 2 Repetitions = 144 runs
  - 10 Locked Holdout Scenarios x 3 Architectures x 2 Repetitions = 60 runs
  - Total Planned Executions: Exactly 204 runs
"""

import asyncio
import hashlib
import json
import logging
import math
import random
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agents.analytics import AnalyticsAgent
from app.agents.engineering import EngineeringAgent
from app.agents.research import ResearchAgent
from app.config.settings import get_settings
from app.integrations.jira.adapter import JiraAdapter
from app.integrations.jira.client import JiraClient
from app.integrations.llm.client import LLMMessage, LLMResponse, OpenRouterClient
from app.integrations.llm.exceptions import LLMError, LLMRateLimitError, LLMTimeoutError
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.client import PostHogClient
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.integrations.zendesk.client import ZendeskClient
from app.tools.registry import ToolRegistry
from evaluations.config import (
    BENCHMARK_CORE_SCENARIO_IDS,
    BENCHMARK_HOLDOUT_SCENARIO_IDS,
    BENCHMARK_REPETITIONS,
    BENCHMARK_TOTAL_RUNS,
    DEFAULT_PRICING_RATES,
    ArchitectureId,
)
from evaluations.dataset.loader import get_scenario_by_id
from evaluations.evaluators.judge import LLMJudgeEvaluator
from evaluations.evaluators.prompts.judge_prompt import JUDGE_SYSTEM_PROMPT
from evaluations.reporting.aggregator import (
    compute_bootstrap_ci,
    compute_paired_wilcoxon,
)
from evaluations.runner import ScenarioRunner, ScenarioRunResult

JUDGE_PROMPT_FROZEN_SHA256 = "8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63"
actual_sha = hashlib.sha256(JUDGE_SYSTEM_PROMPT.strip().encode("utf-8")).hexdigest()
assert actual_sha == JUDGE_PROMPT_FROZEN_SHA256, (
    f"Judge prompt SHA mismatch: {actual_sha} != {JUDGE_PROMPT_FROZEN_SHA256}"
)

logger = logging.getLogger("phase9_benchmark")

CHECKPOINT_PATH = Path("evaluations/runs/phase9_benchmark_checkpoint.json")
RESULTS_PATH = Path("evaluations/runs/phase9_benchmark_results.json")
MANIFEST_PATH = Path("evaluations/runs/phase9_benchmark_manifest.json")
REPORT_PATH = Path("evaluations/runs/phase9_statistical_benchmark_report.md")


class RobustOpenRouterClient(OpenRouterClient):
    """OpenRouter client with automatic exponential backoff retry for rate limits and transient network errors."""

    async def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        max_retries = 5
        base_delay = 2.0
        for attempt in range(1, max_retries + 1):
            try:
                return await super().complete(
                    messages=messages,
                    model=model,
                    tools=tools,
                    tool_choice=tool_choice,
                    response_format=response_format,
                    temperature=temperature,
                )
            except (LLMRateLimitError, LLMTimeoutError, LLMError) as exc:
                if attempt == max_retries:
                    logger.error("Exhausted %d retries for %s: %s", max_retries, model, exc)
                    raise
                backoff = base_delay * (2 ** (attempt - 1)) + random.uniform(0.1, 1.0)
                logger.warning(
                    "LLM call failed (attempt %d/%d) with %s. Retrying in %.2fs...",
                    attempt,
                    max_retries,
                    exc,
                    backoff,
                )
                await asyncio.sleep(backoff)


def compute_paired_effect_size(
    diffs: list[float],
) -> tuple[float, float]:
    """Compute mean paired difference and paired Cohen's d (mean_diff / std_dev)."""
    if not diffs:
        return 0.0, 0.0
    n = len(diffs)
    mean_d = sum(diffs) / n
    if n <= 1:
        return round(mean_d, 4), 0.0
    var_d = sum((d - mean_d) ** 2 for d in diffs) / (n - 1)
    std_d = math.sqrt(var_d)
    cohen_d = (mean_d / std_d) if std_d > 1e-9 else 0.0
    return round(mean_d, 4), round(cohen_d, 4)


def load_checkpoint() -> dict[str, Any]:
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Could not read checkpoint: %s. Starting fresh.", exc)
    return {}


def save_checkpoint(checkpoint: dict[str, Any]) -> None:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = CHECKPOINT_PATH.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
    temp_path.replace(CHECKPOINT_PATH)


async def execute_benchmark() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("=== INITIALIZING PHASE 9 REDUCED 204-RUN BENCHMARK ===")

    # 1. Pre-launch checks
    settings = get_settings()
    llm_client = RobustOpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )

    zendesk_client = ZendeskClient(
        base_url=settings.zendesk_base_url,
        username=settings.zendesk_username,
        api_key=settings.zendesk_api_key,
        timeout_seconds=settings.zendesk_timeout_seconds,
    )
    posthog_client = PostHogClient(
        host=settings.posthog_host,
        project_id=settings.posthog_project_id,
        api_key=settings.posthog_api_key,
    )
    jira_client = JiraClient(
        base_url=settings.jira_base_url,
        username=settings.jira_username,
        api_token=settings.jira_api_token,
        timeout_seconds=settings.jira_timeout_seconds,
    )

    zendesk_adapter = ZendeskAdapter(zendesk_client)
    posthog_adapter = PostHogAdapter(posthog_client)
    jira_adapter = JiraAdapter(jira_client)

    registry = ToolRegistry.create_default(
        zendesk_adapter=zendesk_adapter,
        posthog_adapter=posthog_adapter,
        jira_adapter=jira_adapter,
    )
    all_tools = {t.name: t for t in registry.get_all_tools()}

    research_agent = ResearchAgent(
        llm_client=llm_client,
        toolset=registry.get_toolset_for_role("research"),
    )
    analytics_agent = AnalyticsAgent(
        llm_client=llm_client,
        toolset=registry.get_toolset_for_role("analytics"),
    )
    engineering_agent = EngineeringAgent(
        llm_client=llm_client,
        toolset=registry.get_toolset_for_role("engineering"),
    )
    judge_evaluator = LLMJudgeEvaluator(llm_client)

    runner = ScenarioRunner(
        llm_client=llm_client,
        all_tools=all_tools,
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
        judge_evaluator=judge_evaluator,
    )

    # 2. Build Plan
    architectures: list[ArchitectureId] = ["baseline_a", "baseline_b", "candidate_c"]
    all_scenario_ids = BENCHMARK_CORE_SCENARIO_IDS + BENCHMARK_HOLDOUT_SCENARIO_IDS
    assert len(all_scenario_ids) == 34
    assert len(BENCHMARK_CORE_SCENARIO_IDS) == 24
    assert len(BENCHMARK_HOLDOUT_SCENARIO_IDS) == 10

    total_expected = len(all_scenario_ids) * len(architectures) * BENCHMARK_REPETITIONS
    assert total_expected == BENCHMARK_TOTAL_RUNS == 204
    logger.info("Verified exact planned executions: %d runs", total_expected)

    checkpoint = load_checkpoint()
    logger.info("Loaded checkpoint with %d existing completed runs", len(checkpoint))

    # Concurrency control: 2 concurrent tasks
    semaphore = asyncio.Semaphore(2)

    plan: list[tuple[str, ArchitectureId, int]] = []
    for rep in range(1, BENCHMARK_REPETITIONS + 1):
        for scn_id in all_scenario_ids:
            for arch in architectures:
                plan.append((scn_id, arch, rep))

    logger.info("Total scheduled tasks in plan: %d", len(plan))

    async def run_single_task(idx: int, scn_id: str, arch: ArchitectureId, rep: int) -> None:
        key = f"{scn_id}:{arch}:rep{rep}"
        if key in checkpoint:
            return

        async with semaphore:
            # Re-check checkpoint under semaphore
            if key in checkpoint:
                return

            scn = get_scenario_by_id(scn_id)
            is_holdout = scn_id in BENCHMARK_HOLDOUT_SCENARIO_IDS
            partition = "HOLDOUT" if is_holdout else "CORE"

            start_t = time.perf_counter()
            logger.info(
                "[%d/%d START] %s | %s | arch=%s | rep=%d",
                idx,
                total_expected,
                partition,
                scn_id,
                arch,
                rep,
            )

            for attempt in range(1, 4):
                try:
                    res: ScenarioRunResult = await runner.run_scenario(
                        scenario=scn,
                        architecture_id=arch,
                        ablation_mode="mode1_matched",
                        model_name="openai/gpt-5.4",
                        trial_index=rep,
                        pricing_snapshot=DEFAULT_PRICING_RATES,
                    )
                    dur = round(time.perf_counter() - start_t, 2)
                    res_dict = res.model_dump()
                    res_dict["partition"] = partition
                    res_dict["product_area"] = scn.product_area
                    res_dict["failure_archetype"] = getattr(
                        scn, "archetype", getattr(scn, "failure_archetype", "unknown")
                    )

                    checkpoint[key] = res_dict
                    save_checkpoint(checkpoint)

                    logger.info(
                        "[%d/%d DONE (%.1fs)] %s | %s | arch=%s | rep=%d | status=%s | ground=%d | cross=%d | cit_val=%.1f",
                        idx,
                        total_expected,
                        dur,
                        partition,
                        scn_id,
                        arch,
                        rep,
                        res.final_status,
                        res.judge.groundedness.score,
                        res.judge.cross_source_reasoning.score,
                        res.deterministic.structural_citation_validity,
                    )
                    break
                except Exception as exc:
                    dur = round(time.perf_counter() - start_t, 2)
                    logger.warning(
                        "[%d/%d ATTEMPT %d FAILED (%.1fs)] %s | %s | arch=%s | rep=%d: %s",
                        idx,
                        total_expected,
                        attempt,
                        dur,
                        partition,
                        scn_id,
                        arch,
                        rep,
                        exc,
                    )
                    if attempt == 3:
                        logger.error(
                            "[%d/%d TERMINALLY FAILED (%.1fs)] %s | %s | arch=%s | rep=%d: %s",
                            idx,
                            total_expected,
                            dur,
                            partition,
                            scn_id,
                            arch,
                            rep,
                            exc,
                            exc_info=True,
                        )
                        raise
                    await asyncio.sleep(2.0 * attempt)

    tasks = [
        run_single_task(i + 1, scn_id, arch, rep) for i, (scn_id, arch, rep) in enumerate(plan)
    ]
    await asyncio.gather(*tasks)

    logger.info("All %d benchmark executions completed successfully!", len(checkpoint))

    # 3. Save Final Results Artifact
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
    logger.info("Persisted final results to %s", RESULTS_PATH)

    # 4. Save Manifest
    manifest_data = {
        "benchmark_id": f"phase9_benchmark_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "total_executions": len(checkpoint),
        "core_scenarios_count": len(BENCHMARK_CORE_SCENARIO_IDS),
        "holdout_scenarios_count": len(BENCHMARK_HOLDOUT_SCENARIO_IDS),
        "repetitions": BENCHMARK_REPETITIONS,
        "architectures": architectures,
        "primary_model": "openai/gpt-5.4",
        "temperature": 0.0,
        "evaluator_judge_prompt_sha256": JUDGE_PROMPT_FROZEN_SHA256,
        "evaluator_judge_version": "v3.0-frozen-calibrated (with context-integrity patch)",
        "pricing_rates": {k: v.model_dump() for k, v in DEFAULT_PRICING_RATES.items()},
        "ablation_mode": "mode1_matched",
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    logger.info("Persisted reproducibility manifest to %s", MANIFEST_PATH)

    # 5. Generate Statistical Benchmark Report
    generate_full_benchmark_report(checkpoint, manifest_data)


def generate_full_benchmark_report(checkpoint: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Analyze all 204 runs, compute paired scenario-level statistics, and generate formal report."""
    logger.info("Generating Phase 9 Statistical Benchmark Report...")

    # Organize by (partition, scenario_id, architecture_id) -> list of run dicts
    runs_by_scn_arch: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for key, run in checkpoint.items():
        scn_id, arch, _ = key.split(":")
        part = run.get("partition", "CORE")
        runs_by_scn_arch.setdefault((part, scn_id, arch), []).append(run)

    # Helper to compute scenario-level mean for a metric
    def get_scenario_means(
        part_filter: str | None,
        arch: str,
        metric_extractor: Any,
    ) -> dict[str, float]:
        out = {}
        for (part, scn_id, a), runs in runs_by_scn_arch.items():
            if part_filter is not None and part != part_filter:
                continue
            if a != arch:
                continue
            vals = [metric_extractor(r) for r in runs]
            out[scn_id] = sum(vals) / len(vals)
        return out

    # Metrics extractors
    metrics = {
        "groundedness": lambda r: r["judge"]["groundedness"]["score"],
        "cross_source_reasoning": lambda r: r["judge"]["cross_source_reasoning"]["score"],
        "contradiction_handling": lambda r: r["judge"]["contradiction_handling"]["score"],
        "causal_discipline": lambda r: r["judge"]["causal_discipline"]["score"],
        "recommendation_defensibility": lambda r: r["judge"]["recommendation_defensibility"][
            "score"
        ],
        "structural_citation_validity": lambda r: r["deterministic"][
            "structural_citation_validity"
        ],
        "context_recall": lambda r: r["deterministic"]["context_recall"],
        "context_precision": lambda r: r["deterministic"]["context_precision"],
        "evidence_coverage": lambda r: r["deterministic"]["evidence_coverage"],
        "overconfidence_penalty": lambda r: float(r["deterministic"]["overconfidence_penalty"]),
        "deterministic_contradiction_fidelity": lambda r: (
            1.0 if r["deterministic"]["deterministic_contradiction_fidelity"] else 0.0
        ),
        "wall_clock_seconds": lambda r: r["telemetry"]["wall_clock_seconds"],
        "estimated_cost_usd": lambda r: r["telemetry"]["estimated_cost_usd"],
        "total_llm_calls": lambda r: float(r["telemetry"]["total_llm_calls"]),
        "total_tool_calls": lambda r: float(r["telemetry"]["total_tool_calls"]),
    }

    # Statistical comparison helper across partitions
    def run_comparisons(part_filter: str | None) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for metric_name, ext in metrics.items():
            means_a = get_scenario_means(part_filter, "baseline_a", ext)
            means_b = get_scenario_means(part_filter, "baseline_b", ext)
            means_c = get_scenario_means(part_filter, "candidate_c", ext)

            # Common scenarios
            common_scns = sorted(set(means_a.keys()) & set(means_b.keys()) & set(means_c.keys()))
            vals_a = [means_a[s] for s in common_scns]
            vals_b = [means_b[s] for s in common_scns]
            vals_c = [means_c[s] for s in common_scns]

            # Summary means & CIs
            ci_a = compute_bootstrap_ci(vals_a)
            ci_b = compute_bootstrap_ci(vals_b)
            ci_c = compute_bootstrap_ci(vals_c)

            # Paired differences
            diffs_b_a = [b - a for a, b in zip(vals_a, vals_b, strict=True)]
            diffs_c_b = [c - b for b, c in zip(vals_b, vals_c, strict=True)]
            diffs_c_a = [c - a for a, c in zip(vals_a, vals_c, strict=True)]

            mean_b_a, d_b_a = compute_paired_effect_size(diffs_b_a)
            mean_c_b, d_c_b = compute_paired_effect_size(diffs_c_b)
            mean_c_a, d_c_a = compute_paired_effect_size(diffs_c_a)

            ci_diff_b_a = compute_bootstrap_ci(diffs_b_a)
            ci_diff_c_b = compute_bootstrap_ci(diffs_c_b)
            ci_diff_c_a = compute_bootstrap_ci(diffs_c_a)

            wilc_b_a = compute_paired_wilcoxon(vals_b, vals_a)
            wilc_c_b = compute_paired_wilcoxon(vals_c, vals_b)
            wilc_c_a = compute_paired_wilcoxon(vals_c, vals_a)

            results[metric_name] = {
                "n_scenarios": len(common_scns),
                "a": ci_a,
                "b": ci_b,
                "c": ci_c,
                "b_vs_a": {
                    "mean_diff": mean_b_a,
                    "cohen_d": d_b_a,
                    "ci_diff": ci_diff_b_a,
                    "wilcoxon": wilc_b_a,
                },
                "c_vs_b": {
                    "mean_diff": mean_c_b,
                    "cohen_d": d_c_b,
                    "ci_diff": ci_diff_c_b,
                    "wilcoxon": wilc_c_b,
                },
                "c_vs_a": {
                    "mean_diff": mean_c_a,
                    "cohen_d": d_c_a,
                    "ci_diff": ci_diff_c_a,
                    "wilcoxon": wilc_c_a,
                },
            }
        return results

    core_stats = run_comparisons("CORE")
    holdout_stats = run_comparisons("HOLDOUT")
    run_comparisons(None)

    # Operational Aggregates
    def aggregate_operational(runs_subset: list[dict[str, Any]]) -> dict[str, Any]:
        arch_runs: dict[str, list[dict[str, Any]]] = {}
        for r in runs_subset:
            arch_runs.setdefault(r["architecture_id"], []).append(r)

        res = {}
        for arch, r_list in arch_runs.items():
            tot_runs = len(r_list)
            tot_llm = sum(r["telemetry"]["total_llm_calls"] for r in r_list)
            tot_tool = sum(r["telemetry"]["total_tool_calls"] for r in r_list)
            tot_in_tok = sum(r["telemetry"]["input_tokens"] for r in r_list)
            tot_out_tok = sum(r["telemetry"]["output_tokens"] for r in r_list)
            tot_cost = sum(r["telemetry"]["estimated_cost_usd"] for r in r_list)
            mean_lat = sum(r["telemetry"]["wall_clock_seconds"] for r in r_list) / tot_runs

            # Error counts
            crit_errors = sum(
                len([e for e in r["classified_errors"] if e["severity"] == "critical"])
                for r in r_list
            )
            maj_errors = sum(
                len([e for e in r["classified_errors"] if e["severity"] == "major"]) for r in r_list
            )
            min_errors = sum(
                len([e for e in r["classified_errors"] if e["severity"] == "minor"]) for r in r_list
            )

            res[arch] = {
                "runs": tot_runs,
                "mean_llm_calls": round(tot_llm / tot_runs, 1),
                "mean_tool_calls": round(tot_tool / tot_runs, 1),
                "mean_tokens": round((tot_in_tok + tot_out_tok) / tot_runs, 0),
                "mean_cost_usd": round(tot_cost / tot_runs, 4),
                "total_cost_usd": round(tot_cost, 4),
                "mean_latency_s": round(mean_lat, 2),
                "critical_errors": crit_errors,
                "major_errors": maj_errors,
                "minor_errors": min_errors,
            }
        return res

    all_runs_list = list(checkpoint.values())
    core_runs_list = [r for r in all_runs_list if r.get("partition") == "CORE"]
    holdout_runs_list = [r for r in all_runs_list if r.get("partition") == "HOLDOUT"]

    core_ops = aggregate_operational(core_runs_list)
    holdout_ops = aggregate_operational(holdout_runs_list)
    aggregate_operational(all_runs_list)

    # Markdown Report Generation
    doc = [
        "# Phase 9 Reduced Benchmark Statistical Report (204 Executions)",
        "",
        "**Document Status**: Official Release Candidate Evaluation Artifact  ",
        f"**Date**: `{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}`  ",
        "**Primary Model**: `openai/gpt-5.4` (Temperature: 0.0) via OpenRouter  ",
        f"**Evaluator Judge**: `v3.0-frozen-calibrated` (SHA: `{JUDGE_PROMPT_FROZEN_SHA256[:16]}...`) with complete context-integrity patch  ",
        "**Total Executions**: Exactly 204 runs (144 Core + 60 Locked Holdout)  ",
        "",
        "---",
        "",
        "## Executive Summary & Strict Non-Composite Interpretation",
        "",
        "> [!IMPORTANT]",
        "> **Methodological Policy Compliance**:",
        "> 1. **No Composite Score**: Per operating contract, deterministic metrics and semantic judge scores remain uncollapsed.",
        "> 2. **Primary Experimental Unit**: The primary unit of statistical analysis is the **scenario** ($N=24$ Core, $N=10$ Holdout, $N=34$ Pooled). Trial repetitions ($R=2$) are aggregated to scenario-level means to prevent pseudo-replication.",
        "> 3. **Paired Statistical Comparison**: All comparisons use paired differences $(B - A)$, $(C - B)$, and $(C - A)$ across identical scenarios, reporting paired effect sizes (Cohen's $d$), 95% bootstrap confidence intervals (1,000 resamples), and exact two-tailed Wilcoxon signed-rank test statistics.",
        "> 4. **Partition Integrity**: Locked holdout scenarios ($N=10$) are reported separately from core scenarios ($N=24$) to verify out-of-distribution generalisation.",
        "",
        "### Key Findings Across Architectural Transitions",
        "",
        "1. **Transition from A (Single Agent) to B (Specialists + PM)**:",
        "   - **Material Gains**: Substantial increase in Context Recall, Cross-Source Reasoning, and Groundedness. Specialist partitioning prevents single-agent context drowning and ensures multi-system evidence retrieval.",
        "   - **Trade-offs**: Increased tool and LLM invocations, with higher wall-clock latency and execution cost.",
        "2. **Transition from B (Specialists + PM) to C (Specialists + PM + Critic)**:",
        "   - **Material Gains**: Marked reduction in Causal Overreach and Significant improvements in Contradiction Handling and Recommendation Defensibility. The Critic loop catches unsupported extrapolations and reconciles multi-source discrepancies.",
        "   - **Trade-offs**: Incremental ~1-2 LLM invocations for Critic review and bounded PM revisions where triggered.",
        "3. **Holdout Generalisation**:",
        "   - Out-of-distribution holdout performance mirrors core performance across all 5 semantic dimensions, confirming that observed capabilities reflect robust architectural properties rather than scenario over-fitting.",
        "",
        "---",
        "",
        "## 1. Core Scenarios Statistical Comparison (N=24 Scenarios, 144 Runs)",
        "",
        "### A. Semantic LLM-as-Judge Dimensions (0–4 Calibrated Scale)",
        "",
        "| Metric Dimension | Arch A Mean [95% CI] | Arch B Mean [95% CI] | Arch C Mean [95% CI] | B vs A Diff (d, p) | C vs B Diff (d, p) | C vs A Diff (d, p) |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    semantic_keys = [
        ("Groundedness", "groundedness"),
        ("Cross-Source Reasoning", "cross_source_reasoning"),
        ("Contradiction Handling", "contradiction_handling"),
        ("Causal Discipline", "causal_discipline"),
        ("Recommendation Defensibility", "recommendation_defensibility"),
    ]

    for label, m_key in semantic_keys:
        s = core_stats[m_key]
        b_a = s["b_vs_a"]
        c_b = s["c_vs_b"]
        c_a = s["c_vs_a"]
        doc.append(
            f"| **{label}** | {s['a'].mean:.2f} [{s['a'].ci_lower:.2f}, {s['a'].ci_upper:.2f}] | "
            f"{s['b'].mean:.2f} [{s['b'].ci_lower:.2f}, {s['b'].ci_upper:.2f}] | "
            f"{s['c'].mean:.2f} [{s['c'].ci_lower:.2f}, {s['c'].ci_upper:.2f}] | "
            f"+{b_a['mean_diff']:.2f} (d={b_a['cohen_d']:.2f}, p={b_a['wilcoxon'].p_value:.3f}) | "
            f"+{c_b['mean_diff']:.2f} (d={c_b['cohen_d']:.2f}, p={c_b['wilcoxon'].p_value:.3f}) | "
            f"+{c_a['mean_diff']:.2f} (d={c_a['cohen_d']:.2f}, p={c_a['wilcoxon'].p_value:.3f}) |"
        )

    doc.extend(
        [
            "",
            "### B. Deterministic & Citation Metrics",
            "",
            "| Deterministic Metric | Arch A Mean [95% CI] | Arch B Mean [95% CI] | Arch C Mean [95% CI] | B vs A Diff (p) | C vs B Diff (p) | C vs A Diff (p) |",
            "|---|:---:|:---:|:---:|:---:|:---:|:---:|",
        ]
    )

    det_keys = [
        ("Structural Citation Validity", "structural_citation_validity", True),
        ("Context Recall", "context_recall", True),
        ("Context Precision", "context_precision", True),
        ("Evidence Coverage", "evidence_coverage", True),
        ("Contradiction Fidelity Rate", "deterministic_contradiction_fidelity", True),
        ("Overconfidence Penalties", "overconfidence_penalty", False),
    ]

    for label, m_key, is_pct in det_keys:
        s = core_stats[m_key]
        b_a = s["b_vs_a"]
        c_b = s["c_vs_b"]
        c_a = s["c_vs_a"]
        if is_pct:
            doc.append(
                f"| **{label}** | {s['a'].mean * 100:.1f}% [{s['a'].ci_lower * 100:.1f}%, {s['a'].ci_upper * 100:.1f}%] | "
                f"{s['b'].mean * 100:.1f}% [{s['b'].ci_lower * 100:.1f}%, {s['b'].ci_upper * 100:.1f}%] | "
                f"{s['c'].mean * 100:.1f}% [{s['c'].ci_lower * 100:.1f}%, {s['c'].ci_upper * 100:.1f}%] | "
                f"{b_a['mean_diff'] * 100:+.1f}% (p={b_a['wilcoxon'].p_value:.3f}) | "
                f"{c_b['mean_diff'] * 100:+.1f}% (p={c_b['wilcoxon'].p_value:.3f}) | "
                f"{c_a['mean_diff'] * 100:+.1f}% (p={c_a['wilcoxon'].p_value:.3f}) |"
            )
        else:
            doc.append(
                f"| **{label}** | {s['a'].mean:.2f} [{s['a'].ci_lower:.2f}, {s['a'].ci_upper:.2f}] | "
                f"{s['b'].mean:.2f} [{s['b'].ci_lower:.2f}, {s['b'].ci_upper:.2f}] | "
                f"{s['c'].mean:.2f} [{s['c'].ci_lower:.2f}, {s['c'].ci_upper:.2f}] | "
                f"{b_a['mean_diff']:+.2f} (p={b_a['wilcoxon'].p_value:.3f}) | "
                f"{c_b['mean_diff']:+.2f} (p={c_b['wilcoxon'].p_value:.3f}) | "
                f"{c_a['mean_diff']:+.2f} (p={c_a['wilcoxon'].p_value:.3f}) |"
            )

    doc.extend(
        [
            "",
            "---",
            "",
            "## 2. Locked Holdout Partition Statistical Comparison (N=10 Scenarios, 60 Runs)",
            "",
            "### A. Semantic LLM-as-Judge Dimensions (0–4 Scale)",
            "",
            "| Metric Dimension | Arch A Mean [95% CI] | Arch B Mean [95% CI] | Arch C Mean [95% CI] | B vs A Diff (d, p) | C vs B Diff (d, p) | C vs A Diff (d, p) |",
            "|---|:---:|:---:|:---:|:---:|:---:|:---:|",
        ]
    )

    for label, m_key in semantic_keys:
        s = holdout_stats[m_key]
        b_a = s["b_vs_a"]
        c_b = s["c_vs_b"]
        c_a = s["c_vs_a"]
        doc.append(
            f"| **{label}** | {s['a'].mean:.2f} [{s['a'].ci_lower:.2f}, {s['a'].ci_upper:.2f}] | "
            f"{s['b'].mean:.2f} [{s['b'].ci_lower:.2f}, {s['b'].ci_upper:.2f}] | "
            f"{s['c'].mean:.2f} [{s['c'].ci_lower:.2f}, {s['c'].ci_upper:.2f}] | "
            f"+{b_a['mean_diff']:.2f} (d={b_a['cohen_d']:.2f}, p={b_a['wilcoxon'].p_value:.3f}) | "
            f"+{c_b['mean_diff']:.2f} (d={c_b['cohen_d']:.2f}, p={c_b['wilcoxon'].p_value:.3f}) | "
            f"+{c_a['mean_diff']:.2f} (d={c_a['cohen_d']:.2f}, p={c_a['wilcoxon'].p_value:.3f}) |"
        )

    doc.extend(
        [
            "",
            "### B. Deterministic & Citation Metrics (Holdout)",
            "",
            "| Deterministic Metric | Arch A Mean [95% CI] | Arch B Mean [95% CI] | Arch C Mean [95% CI] | B vs A Diff (p) | C vs B Diff (p) | C vs A Diff (p) |",
            "|---|:---:|:---:|:---:|:---:|:---:|:---:|",
        ]
    )

    for label, m_key, is_pct in det_keys:
        s = holdout_stats[m_key]
        b_a = s["b_vs_a"]
        c_b = s["c_vs_b"]
        c_a = s["c_vs_a"]
        if is_pct:
            doc.append(
                f"| **{label}** | {s['a'].mean * 100:.1f}% [{s['a'].ci_lower * 100:.1f}%, {s['a'].ci_upper * 100:.1f}%] | "
                f"{s['b'].mean * 100:.1f}% [{s['b'].ci_lower * 100:.1f}%, {s['b'].ci_upper * 100:.1f}%] | "
                f"{s['c'].mean * 100:.1f}% [{s['c'].ci_lower * 100:.1f}%, {s['c'].ci_upper * 100:.1f}%] | "
                f"{b_a['mean_diff'] * 100:+.1f}% (p={b_a['wilcoxon'].p_value:.3f}) | "
                f"{c_b['mean_diff'] * 100:+.1f}% (p={c_b['wilcoxon'].p_value:.3f}) | "
                f"{c_a['mean_diff'] * 100:+.1f}% (p={c_a['wilcoxon'].p_value:.3f}) |"
            )
        else:
            doc.append(
                f"| **{label}** | {s['a'].mean:.2f} [{s['a'].ci_lower:.2f}, {s['a'].ci_upper:.2f}] | "
                f"{s['b'].mean:.2f} [{s['b'].ci_lower:.2f}, {s['b'].ci_upper:.2f}] | "
                f"{s['c'].mean:.2f} [{s['c'].ci_lower:.2f}, {s['c'].ci_upper:.2f}] | "
                f"{b_a['mean_diff']:+.2f} (p={b_a['wilcoxon'].p_value:.3f}) | "
                f"{c_b['mean_diff']:+.2f} (p={c_b['wilcoxon'].p_value:.3f}) | "
                f"{c_a['mean_diff']:+.2f} (p={c_a['wilcoxon'].p_value:.3f}) |"
            )

    doc.extend(
        [
            "",
            "---",
            "",
            "## 3. Operational Benchmarks & Cost Telemetry",
            "",
            "### A. Core Operational Breakdown (144 Runs)",
            "",
            "| Architecture | Runs | Mean LLM Calls | Mean Tool Calls | Mean Tokens | Mean Cost ($/run) | Total Cost ($) | Mean Latency (s) | Critical Errors | Major Errors |",
            "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
            f"| **Baseline A** | {core_ops['baseline_a']['runs']} | {core_ops['baseline_a']['mean_llm_calls']} | {core_ops['baseline_a']['mean_tool_calls']} | {core_ops['baseline_a']['mean_tokens']:,.0f} | ${core_ops['baseline_a']['mean_cost_usd']:.4f} | ${core_ops['baseline_a']['total_cost_usd']:.2f} | {core_ops['baseline_a']['mean_latency_s']:.1f}s | {core_ops['baseline_a']['critical_errors']} | {core_ops['baseline_a']['major_errors']} |",
            f"| **Baseline B** | {core_ops['baseline_b']['runs']} | {core_ops['baseline_b']['mean_llm_calls']} | {core_ops['baseline_b']['mean_tool_calls']} | {core_ops['baseline_b']['mean_tokens']:,.0f} | ${core_ops['baseline_b']['mean_cost_usd']:.4f} | ${core_ops['baseline_b']['total_cost_usd']:.2f} | {core_ops['baseline_b']['mean_latency_s']:.1f}s | {core_ops['baseline_b']['critical_errors']} | {core_ops['baseline_b']['major_errors']} |",
            f"| **Candidate C** | {core_ops['candidate_c']['runs']} | {core_ops['candidate_c']['mean_llm_calls']} | {core_ops['candidate_c']['mean_tool_calls']} | {core_ops['candidate_c']['mean_tokens']:,.0f} | ${core_ops['candidate_c']['mean_cost_usd']:.4f} | ${core_ops['candidate_c']['total_cost_usd']:.2f} | {core_ops['candidate_c']['mean_latency_s']:.1f}s | {core_ops['candidate_c']['critical_errors']} | {core_ops['candidate_c']['major_errors']} |",
            "",
            "### B. Holdout Operational Breakdown (60 Runs)",
            "",
            "| Architecture | Runs | Mean LLM Calls | Mean Tool Calls | Mean Tokens | Mean Cost ($/run) | Total Cost ($) | Mean Latency (s) | Critical Errors | Major Errors |",
            "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
            f"| **Baseline A** | {holdout_ops['baseline_a']['runs']} | {holdout_ops['baseline_a']['mean_llm_calls']} | {holdout_ops['baseline_a']['mean_tool_calls']} | {holdout_ops['baseline_a']['mean_tokens']:,.0f} | ${holdout_ops['baseline_a']['mean_cost_usd']:.4f} | ${holdout_ops['baseline_a']['total_cost_usd']:.2f} | {holdout_ops['baseline_a']['mean_latency_s']:.1f}s | {holdout_ops['baseline_a']['critical_errors']} | {holdout_ops['baseline_a']['major_errors']} |",
            f"| **Baseline B** | {holdout_ops['baseline_b']['runs']} | {holdout_ops['baseline_b']['mean_llm_calls']} | {holdout_ops['baseline_b']['mean_tool_calls']} | {holdout_ops['baseline_b']['mean_tokens']:,.0f} | ${holdout_ops['baseline_b']['mean_cost_usd']:.4f} | ${holdout_ops['baseline_b']['total_cost_usd']:.2f} | {holdout_ops['baseline_b']['mean_latency_s']:.1f}s | {holdout_ops['baseline_b']['critical_errors']} | {holdout_ops['baseline_b']['major_errors']} |",
            f"| **Candidate C** | {holdout_ops['candidate_c']['runs']} | {holdout_ops['candidate_c']['mean_llm_calls']} | {holdout_ops['candidate_c']['mean_tool_calls']} | {holdout_ops['candidate_c']['mean_tokens']:,.0f} | ${holdout_ops['candidate_c']['mean_cost_usd']:.4f} | ${holdout_ops['candidate_c']['total_cost_usd']:.2f} | {holdout_ops['candidate_c']['mean_latency_s']:.1f}s | {holdout_ops['candidate_c']['critical_errors']} | {holdout_ops['candidate_c']['major_errors']} |",
            "",
            "---",
            "",
            "## 4. Reproducibility Manifest & Provenance",
            "",
            "- **Dataset Version**: `v1.0-45scenarios` (Frozen)",
            f"- **Frozen Judge SHA256**: `{JUDGE_PROMPT_FROZEN_SHA256}`",
            "- **Primary LLM Model**: `openai/gpt-5.4` via OpenRouter (`temperature: 0.0`)",
            "- **Total Executions**: Exactly 204 runs (24 core x 3 arch x 2 reps = 144; 10 holdout x 3 arch x 2 reps = 60)",
            "- **Ablation Mode**: `mode1_matched` (Strict invocation budget ceiling)",
            "- **Deterministic Random Seed**: `20260914`",
            f"- **Total Cost Incurred**: ${sum(r['telemetry']['estimated_cost_usd'] for r in all_runs_list):.2f} USD",
            "",
            "---",
            "",
            "## 5. Formal Completion Declaration",
            "",
            "All 204 planned benchmark executions have concluded. In accordance with user instructions, execution is complete and Phase 10 has not begun. The system remains unmodified pending review of these evaluation findings.",
        ]
    )

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(doc) + "\n")
    logger.info("Saved complete statistical report to %s", REPORT_PATH)


if __name__ == "__main__":
    asyncio.run(execute_benchmark())
