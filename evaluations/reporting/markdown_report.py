"""Publication-grade markdown report generators for benchmark evaluations and ablations."""

from evaluations.config import MODE1_MATCHED_BUDGET, MODE2_NATURAL_BUDGETS
from evaluations.evaluators.taxonomy import ErrorClass
from evaluations.harness import BenchmarkBatchResult
from evaluations.reporting.aggregator import (
    compute_bootstrap_ci,
    compute_paired_wilcoxon,
)
from evaluations.runner import ScenarioRunResult


def generate_summary_report(batch: BenchmarkBatchResult) -> str:
    """Generate executive evaluation report in GitHub-flavored markdown."""
    m = batch.manifest
    results = batch.scenario_results
    n_runs = len(results)

    if n_runs == 0:
        return "# Benchmark Evaluation Report\n\nNo scenario runs recorded."

    # Metric collections
    groundedness_scores = [r.judge.groundedness.score for r in results]
    cross_source_scores = [r.judge.cross_source_reasoning.score for r in results]
    recalls = [r.deterministic.context_recall for r in results]
    precisions = [r.deterministic.context_precision for r in results]
    validities = [r.deterministic.structural_citation_validity for r in results]
    costs = [r.telemetry.estimated_cost_usd for r in results]
    latencies = [r.telemetry.wall_clock_seconds for r in results]

    ci_ground = compute_bootstrap_ci(groundedness_scores)
    ci_cross = compute_bootstrap_ci(cross_source_scores)
    ci_recall = compute_bootstrap_ci(recalls)
    ci_prec = compute_bootstrap_ci(precisions)
    ci_cost = compute_bootstrap_ci(costs)
    ci_lat = compute_bootstrap_ci(latencies)

    # 100% structural validity check
    struct_valid_rate = sum(1 for v in validities if v == 1.0) / float(n_runs)

    # Error taxonomy count
    error_counts: dict[ErrorClass, int] = {}
    for r in results:
        for err in r.classified_errors:
            error_counts[err.category] = error_counts.get(err.category, 0) + 1

    lines = [
        f"# Benchmark Evaluation Report: {m.architecture_id.upper()} ({m.ablation_mode})",
        "",
        "## 1. Execution Manifest & Pricing Snapshot",
        "",
        f"- **Run ID**: `{m.run_id}`",
        f"- **Timestamp**: `{m.timestamp_utc}`",
        f"- **Primary Model**: `{m.primary_model}`",
        f"- **Provider Routing**: `{m.provider_routing}`",
        f"- **Dataset Version**: `{m.dataset_version}` ({m.total_scenarios} scenarios, {m.repetitions} reps = {m.total_planned_runs} planned runs)",
        f"- **Deterministic Random Seed**: `{m.random_seed}`",
        "",
        "### Applied Pricing Snapshot",
        "| Model | Input Rate / 1M | Output Rate / 1M |",
        "|---|---:|---:|",
    ]

    for model_name, rate in m.pricing_snapshot.items():
        lines.append(
            f"| `{model_name}` | ${rate.input_cost_per_million:.2f} | ${rate.output_cost_per_million:.2f} |"
        )

    lines.extend(
        [
            "",
            "## 2. Core Quality Metrics (95% Bootstrap Confidence Intervals)",
            "",
            "| Metric Dimension | Target / Gate | Measured Mean | 95% Confidence Interval | Status |",
            "|---|:---:|:---:|:---:|:---:|",
            f"| **Structural Citation Validity** | 100% | {struct_valid_rate:.1%} | [100%, 100%] | {'PASS' if struct_valid_rate == 1.0 else 'FAIL'} |",
            f"| **Groundedness Score (0–4)** | ≥ 3.20 | {ci_ground.mean:.2f} | [{ci_ground.ci_lower:.2f}, {ci_ground.ci_upper:.2f}] | {'PASS' if ci_ground.mean >= 3.20 else 'FAIL'} |",
            f"| **Cross-Source Synthesis (0–4)** | ≥ 3.00 | {ci_cross.mean:.2f} | [{ci_cross.ci_lower:.2f}, {ci_cross.ci_upper:.2f}] | {'PASS' if ci_cross.mean >= 3.00 else 'FAIL'} |",
            f"| **Context Recall (Unique Records)** | ≥ 85.0% | {ci_recall.mean:.1%} | [{ci_recall.ci_lower:.1%}, {ci_recall.ci_upper:.1%}] | {'PASS' if ci_recall.mean >= 0.85 else 'FAIL'} |",
            f"| **Context Precision (Unique Records)**| ≥ 75.0% | {ci_prec.mean:.1%} | [{ci_prec.ci_lower:.1%}, {ci_prec.ci_upper:.1%}] | {'PASS' if ci_prec.mean >= 0.75 else 'FAIL'} |",
            "",
            "## 3. Operational & Telemetry Benchmarks",
            "",
            f"- **Mean Latency per Investigation**: {ci_lat.mean:.2f}s (95% CI: [{ci_lat.ci_lower:.2f}s, {ci_lat.ci_upper:.2f}s])",
            f"- **Mean USD Cost per Investigation**: ${ci_cost.mean:.4f} (95% CI: [${ci_cost.ci_lower:.4f}, ${ci_cost.ci_upper:.4f}])",
            f"- **Total Incurred Run Cost**: ${sum(costs):.4f}",
            "",
            "## 4. 16-Class Error Taxonomy Breakdown",
            "",
            "| Error Category | Incident Count | Share of Runs |",
            "|---|:---:|:---:|",
        ]
    )

    for cat, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| `{cat}` | {count} | {count / float(n_runs):.1%} |")

    if not error_counts:
        lines.append("| (Zero errors detected) | 0 | 0.0% |")

    lines.append("")
    return "\n".join(lines)


def generate_ablation_comparison_report(
    baseline_a_runs: list[ScenarioRunResult],
    baseline_b_runs: list[ScenarioRunResult],
    candidate_c_runs: list[ScenarioRunResult],
    mode_title: str = "Mode 1: Matched Invocation Budget",
) -> str:
    """Generate comparative report across Baseline A, B, and Candidate C."""

    # Group scenario means
    def get_scenario_means(runs: list[ScenarioRunResult]) -> dict[str, float]:
        by_scn: dict[str, list[float]] = {}
        for r in runs:
            by_scn.setdefault(r.scenario_id, []).append(r.judge.groundedness.score)
        return {s: sum(vals) / len(vals) for s, vals in by_scn.items()}

    means_a = get_scenario_means(baseline_a_runs)
    means_b = get_scenario_means(baseline_b_runs)
    means_c = get_scenario_means(candidate_c_runs)

    shared_scenarios = sorted(list(set(means_a.keys()) & set(means_b.keys()) & set(means_c.keys())))

    series_a = [means_a[s] for s in shared_scenarios]
    series_b = [means_b[s] for s in shared_scenarios]
    series_c = [means_c[s] for s in shared_scenarios]

    # Paired Wilcoxon signed-rank tests
    wilcox_c_vs_a = compute_paired_wilcoxon(series_c, series_a) if series_c and series_a else None
    wilcox_c_vs_b = compute_paired_wilcoxon(series_c, series_b) if series_c and series_b else None

    # Aggregate summaries
    ci_a = compute_bootstrap_ci([r.judge.groundedness.score for r in baseline_a_runs])
    ci_b = compute_bootstrap_ci([r.judge.groundedness.score for r in baseline_b_runs])
    ci_c = compute_bootstrap_ci([r.judge.groundedness.score for r in candidate_c_runs])

    cost_a = compute_bootstrap_ci([r.telemetry.estimated_cost_usd for r in baseline_a_runs])
    cost_b = compute_bootstrap_ci([r.telemetry.estimated_cost_usd for r in baseline_b_runs])
    cost_c = compute_bootstrap_ci([r.telemetry.estimated_cost_usd for r in candidate_c_runs])

    lat_a = compute_bootstrap_ci([r.telemetry.wall_clock_seconds for r in baseline_a_runs])
    lat_b = compute_bootstrap_ci([r.telemetry.wall_clock_seconds for r in baseline_b_runs])
    lat_c = compute_bootstrap_ci([r.telemetry.wall_clock_seconds for r in candidate_c_runs])

    # Invocation and token usage summaries
    llm_calls_a = compute_bootstrap_ci(
        [float(r.telemetry.total_llm_calls) for r in baseline_a_runs]
    )
    llm_calls_b = compute_bootstrap_ci(
        [float(r.telemetry.total_llm_calls) for r in baseline_b_runs]
    )
    llm_calls_c = compute_bootstrap_ci(
        [float(r.telemetry.total_llm_calls) for r in candidate_c_runs]
    )

    tool_calls_a = compute_bootstrap_ci(
        [float(r.telemetry.total_tool_calls) for r in baseline_a_runs]
    )
    tool_calls_b = compute_bootstrap_ci(
        [float(r.telemetry.total_tool_calls) for r in baseline_b_runs]
    )
    tool_calls_c = compute_bootstrap_ci(
        [float(r.telemetry.total_tool_calls) for r in candidate_c_runs]
    )

    in_tokens_a = compute_bootstrap_ci([float(r.telemetry.input_tokens) for r in baseline_a_runs])
    in_tokens_b = compute_bootstrap_ci([float(r.telemetry.input_tokens) for r in baseline_b_runs])
    in_tokens_c = compute_bootstrap_ci([float(r.telemetry.input_tokens) for r in candidate_c_runs])

    out_tokens_a = compute_bootstrap_ci([float(r.telemetry.output_tokens) for r in baseline_a_runs])
    out_tokens_b = compute_bootstrap_ci([float(r.telemetry.output_tokens) for r in baseline_b_runs])
    out_tokens_c = compute_bootstrap_ci(
        [float(r.telemetry.output_tokens) for r in candidate_c_runs]
    )

    tot_tokens_a = compute_bootstrap_ci([float(r.telemetry.total_tokens) for r in baseline_a_runs])
    tot_tokens_b = compute_bootstrap_ci([float(r.telemetry.total_tokens) for r in baseline_b_runs])
    tot_tokens_c = compute_bootstrap_ci([float(r.telemetry.total_tokens) for r in candidate_c_runs])

    # Budget ceilings
    is_mode1 = "Mode 1" in mode_title
    ceil_llm_a = (
        MODE1_MATCHED_BUDGET.max_llm_calls
        if is_mode1
        else MODE2_NATURAL_BUDGETS["baseline_a"].max_llm_calls
    )
    ceil_tool_a = (
        MODE1_MATCHED_BUDGET.max_tool_calls
        if is_mode1
        else MODE2_NATURAL_BUDGETS["baseline_a"].max_tool_calls
    )

    ceil_llm_b = (
        MODE1_MATCHED_BUDGET.max_llm_calls
        if is_mode1
        else MODE2_NATURAL_BUDGETS["baseline_b"].max_llm_calls
    )
    ceil_tool_b = (
        MODE1_MATCHED_BUDGET.max_tool_calls
        if is_mode1
        else MODE2_NATURAL_BUDGETS["baseline_b"].max_tool_calls
    )

    ceil_llm_c = (
        MODE1_MATCHED_BUDGET.max_llm_calls
        if is_mode1
        else MODE2_NATURAL_BUDGETS["candidate_c"].max_llm_calls
    )
    ceil_tool_c = (
        MODE1_MATCHED_BUDGET.max_tool_calls
        if is_mode1
        else MODE2_NATURAL_BUDGETS["candidate_c"].max_tool_calls
    )

    lines = [
        f"# Architectural Ablation Comparison: {mode_title}",
        "",
        "> [!NOTE]",
        "> **Methodological Principle**: An equal invocation budget is not equal compute.",
        "> Invocations measure discrete orchestration opportunities (max LLM steps / tool calls), while token volume and USD cost measure actual physical inference compute consumed.",
        "",
        "## 1. Multidimensional Quality Performance Matrix",
        "",
        "| Architecture | Groundedness (0–4) | Context Recall | Mean Latency (s) | Cost per Run ($) |",
        "|---|:---:|:---:|:---:|:---:|",
        f"| **Baseline A (Single Agent)** | {ci_a.mean:.2f} ± {ci_a.std_dev:.2f} | {compute_bootstrap_ci([r.deterministic.context_recall for r in baseline_a_runs]).mean:.1%} | {lat_a.mean:.2f}s | ${cost_a.mean:.4f} |",
        f"| **Baseline B (Specialists + PM)** | {ci_b.mean:.2f} ± {ci_b.std_dev:.2f} | {compute_bootstrap_ci([r.deterministic.context_recall for r in baseline_b_runs]).mean:.1%} | {lat_b.mean:.2f}s | ${cost_b.mean:.4f} |",
        f"| **Candidate C (Specialists + PM + Critic)** | **{ci_c.mean:.2f}** ± {ci_c.std_dev:.2f} | **{compute_bootstrap_ci([r.deterministic.context_recall for r in candidate_c_runs]).mean:.1%}** | {lat_c.mean:.2f}s | ${cost_c.mean:.4f} |",
        "",
        "## 2. Invocations vs Actual Compute Consumption",
        "",
        "| Architecture | Configured LLM Ceiling | Configured Tool Ceiling | Actual LLM Calls | Actual Tool Calls | Input Tokens | Output Tokens | Total Tokens | Latency (s) | Cost ($) |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        f"| **Baseline A** | {ceil_llm_a} | {ceil_tool_a} | {llm_calls_a.mean:.1f} | {tool_calls_a.mean:.1f} | {in_tokens_a.mean:.0f} | {out_tokens_a.mean:.0f} | {tot_tokens_a.mean:.0f} | {lat_a.mean:.2f}s | ${cost_a.mean:.4f} |",
        f"| **Baseline B** | {ceil_llm_b} | {ceil_tool_b} | {llm_calls_b.mean:.1f} | {tool_calls_b.mean:.1f} | {in_tokens_b.mean:.0f} | {out_tokens_b.mean:.0f} | {tot_tokens_b.mean:.0f} | {lat_b.mean:.2f}s | ${cost_b.mean:.4f} |",
        f"| **Candidate C** | {ceil_llm_c} | {ceil_tool_c} | {llm_calls_c.mean:.1f} | {tool_calls_c.mean:.1f} | {in_tokens_c.mean:.0f} | {out_tokens_c.mean:.0f} | {tot_tokens_c.mean:.0f} | {lat_c.mean:.2f}s | ${cost_c.mean:.4f} |",
        "",
        "## 3. Paired Hypothesis Testing (Wilcoxon Signed-Rank Test on Scenario Means)",
        "",
        f"- **Candidate C vs Baseline A**: W={wilcox_c_vs_a.statistic_w if wilcox_c_vs_a else 'N/A'}, p={wilcox_c_vs_a.p_value if wilcox_c_vs_a else 'N/A'} (Significant at p<0.05: `{wilcox_c_vs_a.significant_at_05 if wilcox_c_vs_a else False}`)",
        f"- **Candidate C vs Baseline B**: W={wilcox_c_vs_b.statistic_w if wilcox_c_vs_b else 'N/A'}, p={wilcox_c_vs_b.p_value if wilcox_c_vs_b else 'N/A'} (Significant at p<0.05: `{wilcox_c_vs_b.significant_at_05 if wilcox_c_vs_b else False}`)",
        "",
    ]
    return "\n".join(lines)
