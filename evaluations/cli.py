"""Command line interface for executing benchmarks, ablations, and regression tests."""

import argparse
import asyncio
import logging
import sys

from app.agents.analytics import AnalyticsAgent
from app.agents.engineering import EngineeringAgent
from app.agents.research import ResearchAgent
from app.config.settings import get_settings
from app.integrations.jira.adapter import JiraAdapter
from app.integrations.llm.client import OpenRouterClient
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.zendesk.adapter import ZendeskAdapter
from app.tools.registry import ToolRegistry

from evaluations.calibration.live_gate import (
    calculate_preflight,
    require_paid_evaluation_opt_in,
)
from evaluations.config import (
    DEFAULT_PRICING_RATES,
    MODE1_MATCHED_BUDGET,
    MODE2_NATURAL_BUDGETS,
)
from evaluations.dataset.loader import get_scenarios
from evaluations.evaluators.judge import LLMJudgeEvaluator
from evaluations.harness import EvaluationHarness
from evaluations.reporting.markdown_report import (
    generate_ablation_comparison_report,
    generate_summary_report,
)
from evaluations.reporting.regression import evaluate_regression_gates
from evaluations.runner import ScenarioRunner

logger = logging.getLogger("evaluations.cli")


async def main_async() -> int:
    """Async CLI entry point."""
    parser = argparse.ArgumentParser(description="PMLytics AI Evaluation Runner")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly allow paid provider execution for this command",
    )
    parser.add_argument(
        "--max-provider-cost-usd",
        type=float,
        default=0.0,
        help="Maximum provider spend approved for this command",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=0,
        help="Maximum investigation runs approved for this command",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Run single batch
    run_parser = subparsers.add_parser("run", help="Run an evaluation batch")
    run_parser.add_argument(
        "--architecture", choices=["baseline_a", "baseline_b", "candidate_c"], default="candidate_c"
    )
    run_parser.add_argument(
        "--mode", choices=["mode1_matched", "mode2_natural"], default="mode1_matched"
    )
    run_parser.add_argument("--split", choices=["dev", "val", "holdout", "all"], default="val")
    run_parser.add_argument("--model", default="openai/gpt-5.4")
    run_parser.add_argument("--reps", type=int, default=3)

    # 2. Regression gate
    subparsers.add_parser(
        "regression", help="Run automated regression gates against validation set"
    )

    # 3. Ablation comparison
    subparsers.add_parser(
        "ablate", help="Run Mode 1 matched invocation budget comparison across A, B, and C"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    if args.command == "run":
        selected_scenarios = get_scenarios(args.split)
        planned_runs = len(selected_scenarios) * args.reps
        selected_model = args.model
        max_calls_per_run = (
            MODE1_MATCHED_BUDGET.max_llm_calls
            if args.mode == "mode1_matched"
            else max(budget.max_llm_calls for budget in MODE2_NATURAL_BUDGETS.values())
        )
    elif args.command == "regression":
        planned_runs = len(get_scenarios("val"))
        selected_model = "openai/gpt-5.4"
        max_calls_per_run = MODE1_MATCHED_BUDGET.max_llm_calls
    else:
        planned_runs = len(get_scenarios("val")) * 3 * 3
        selected_model = "openai/gpt-5.4"
        max_calls_per_run = MODE1_MATCHED_BUDGET.max_llm_calls

    if args.max_runs <= 0 or planned_runs > args.max_runs:
        raise PermissionError(
            f"Planned evaluation runs ({planned_runs}) exceed the explicit --max-runs approval "
            f"({args.max_runs})."
        )
    pricing = DEFAULT_PRICING_RATES.get(selected_model)
    if pricing is None:
        raise ValueError(f"No checked-in pricing snapshot exists for {selected_model}")
    preflight = calculate_preflight(
        case_count=planned_runs,
        cache_hits=0,
        model_name=selected_model,
        estimated_input_tokens_per_case=max_calls_per_run * 1200,
        maximum_output_tokens_per_case=max_calls_per_run * 350,
        input_cost_per_million=pricing.input_cost_per_million,
        output_cost_per_million=pricing.output_cost_per_million,
        approved_maximum_cost_usd=args.max_provider_cost_usd,
    )
    print(preflight.model_dump_json(indent=2))
    require_paid_evaluation_opt_in(live=args.live, preflight=preflight)

    settings = get_settings()
    llm_client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )

    # Setup adapters and tool registry
    from app.integrations.jira.client import JiraClient
    from app.integrations.posthog.client import PostHogClient
    from app.integrations.zendesk.client import ZendeskClient

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

    harness = EvaluationHarness(runner=runner)

    if args.command == "run":
        scenarios = get_scenarios(args.split)
        print(
            f"Executing {len(scenarios)} scenarios across {args.reps} repetitions ({args.architecture}, {args.mode})..."
        )
        batch = await harness.run_batch(
            scenarios=scenarios,
            architecture_id=args.architecture,
            ablation_mode=args.mode,
            model_name=args.model,
            repetitions=args.reps,
        )
        report = generate_summary_report(batch)
        print("\n" + report)
        return 0

    elif args.command == "regression":
        scenarios = get_scenarios("val")
        print(f"Running regression check on validation set ({len(scenarios)} scenarios)...")
        batch = await harness.run_batch(
            scenarios=scenarios,
            architecture_id="candidate_c",
            ablation_mode="mode1_matched",
            model_name="openai/gpt-5.4",
            repetitions=1,
        )
        gate_report = evaluate_regression_gates(batch.scenario_results)
        print("\n=== REGRESSION GATE RESULTS ===")
        print(f"Passed: {gate_report.passed}")
        for k, v in gate_report.measured_values.items():
            print(f"  {k}: {v}")
        if gate_report.failed_reasons:
            print("Failed reasons:")
            for r in gate_report.failed_reasons:
                print(f"  - {r}")
        return 0 if gate_report.passed else 1

    elif args.command == "ablate":
        scenarios = get_scenarios("val")
        print(
            f"Running Mode 1 Matched Invocation Ablation (A vs B vs C) across {len(scenarios)} validation scenarios..."
        )
        batch_a = await harness.run_batch(scenarios, "baseline_a", "mode1_matched", repetitions=3)
        batch_b = await harness.run_batch(scenarios, "baseline_b", "mode1_matched", repetitions=3)
        batch_c = await harness.run_batch(scenarios, "candidate_c", "mode1_matched", repetitions=3)

        report = generate_ablation_comparison_report(
            baseline_a_runs=batch_a.scenario_results,
            baseline_b_runs=batch_b.scenario_results,
            candidate_c_runs=batch_c.scenario_results,
            mode_title="Mode 1: Matched Invocation Budget (25 LLM / 26 Tool Invocations)",
        )
        print("\n" + report)
        return 0

    return 0


def main() -> None:
    """CLI entrypoint."""
    sys.exit(asyncio.run(main_async()))


if __name__ == "__main__":
    main()
