"""Single scenario execution runner orchestrating SUT execution, deterministic checks, and judging."""

import logging
import time
import uuid

from app.agents.analytics import AnalyticsAgent
from app.agents.engineering import EngineeringAgent
from app.agents.research import ResearchAgent
from app.integrations.llm.client import LLMClient
from app.orchestration.graph import create_investigation_graph
from app.orchestration.state import InvestigationState
from app.tools.base import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from evaluations.baselines.single_agent import SingleAgentBaseline
from evaluations.baselines.specialist_no_critic import SpecialistNoCriticBaseline
from evaluations.config import AblationMode, ArchitectureId, ModelPricing
from evaluations.evaluators.deterministic import (
    DeterministicMetrics,
    evaluate_deterministic_metrics,
)
from evaluations.evaluators.judge import EvaluationJudgeReport, LLMJudgeEvaluator
from evaluations.evaluators.taxonomy import ClassifiedError, classify_investigation_errors
from evaluations.evaluators.telemetry import RunTelemetry, calculate_cost_from_snapshot
from evaluations.ground_truth.schema import EvaluationScenario

logger = logging.getLogger(__name__)


class ScenarioRunResult(BaseModel):
    """Immutable comprehensive record of a single scenario trial execution."""

    model_config = ConfigDict(frozen=True)

    scenario_id: str
    run_id: str
    trial_index: int
    architecture_id: ArchitectureId
    ablation_mode: AblationMode
    model_name: str

    final_status: str
    deterministic: DeterministicMetrics
    judge: EvaluationJudgeReport
    telemetry: RunTelemetry
    classified_errors: list[ClassifiedError] = Field(default_factory=list)
    passed_all_gates: bool = False


class ScenarioRunner:
    """Executes a single evaluation scenario against a specified architecture and evaluates outcomes."""

    def __init__(
        self,
        llm_client: LLMClient,
        all_tools: dict[str, BaseTool],
        research_agent: ResearchAgent,
        analytics_agent: AnalyticsAgent,
        engineering_agent: EngineeringAgent,
        judge_evaluator: LLMJudgeEvaluator | None = None,
    ) -> None:
        self.llm = llm_client
        self.tools = all_tools
        self.research_agent = research_agent
        self.analytics_agent = analytics_agent
        self.engineering_agent = engineering_agent
        self.judge = judge_evaluator or LLMJudgeEvaluator(llm_client)

    async def run_scenario(
        self,
        scenario: EvaluationScenario,
        architecture_id: ArchitectureId = "candidate_c",
        ablation_mode: AblationMode = "mode1_matched",
        model_name: str = "openai/gpt-5.4",
        trial_index: int = 1,
        pricing_snapshot: dict[str, ModelPricing] | None = None,
    ) -> ScenarioRunResult:
        """Execute one scenario trial and return structured evaluation artifact."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        investigation_id = f"inv_{scenario.scenario_id}_{architecture_id}_{trial_index}"

        start_time = time.perf_counter()

        # 1. Execute SUT
        final_state: InvestigationState
        if architecture_id == "baseline_a":
            baseline_a = SingleAgentBaseline(
                llm_client=self.llm,
                tools=self.tools,
                model_name=model_name,
            )
            final_state = await baseline_a.execute(
                user_query=scenario.user_query,
                investigation_id=investigation_id,
                mode=ablation_mode,
            )
        elif architecture_id == "baseline_b":
            baseline_b = SpecialistNoCriticBaseline(
                llm_client=self.llm,
                research_agent=self.research_agent,
                analytics_agent=self.analytics_agent,
                engineering_agent=self.engineering_agent,
                model_name=model_name,
            )
            final_state = await baseline_b.execute(
                user_query=scenario.user_query,
                investigation_id=investigation_id,
                mode=ablation_mode,
            )
        else:
            # Candidate C: Full LangGraph pipeline with Critic
            candidate_graph = create_investigation_graph(
                llm_client=self.llm,
                research_agent=self.research_agent,
                analytics_agent=self.analytics_agent,
                engineering_agent=self.engineering_agent,
                planner_model=model_name,
                assessment_model=model_name,
                pm_model=model_name,
                critic_model=model_name,
            )
            initial_state = InvestigationState(
                investigation_id=investigation_id,
                user_query=scenario.user_query,
            )
            final_dict = await candidate_graph.ainvoke(initial_state)
            final_state = InvestigationState.model_validate(final_dict)

        elapsed_seconds = round(time.perf_counter() - start_time, 3)

        # 2. Compute Telemetry & Cost
        budget = final_state.budget_usage
        total_tool_calls = (
            budget.research_tool_calls + budget.analytics_tool_calls + budget.engineering_tool_calls
        )
        total_llm_calls = (
            budget.planner_llm_calls
            + budget.research_llm_calls
            + budget.analytics_llm_calls
            + budget.engineering_llm_calls
            + budget.assessment_llm_calls
            + budget.pm_llm_calls
            + budget.critic_llm_calls
        )

        # Approximate token telemetry from LLM calls if provider doesn't stream exact tokens
        est_input_tokens = total_llm_calls * 1200
        est_output_tokens = total_llm_calls * 350
        cost_usd = calculate_cost_from_snapshot(
            model_id=model_name,
            input_tokens=est_input_tokens,
            output_tokens=est_output_tokens,
            pricing_snapshot=pricing_snapshot,
        )

        telemetry = RunTelemetry(
            model_id=model_name,
            wall_clock_seconds=elapsed_seconds,
            total_llm_calls=total_llm_calls,
            total_tool_calls=total_tool_calls,
            input_tokens=est_input_tokens,
            output_tokens=est_output_tokens,
            total_tokens=est_input_tokens + est_output_tokens,
            estimated_cost_usd=cost_usd,
        )

        # 3. Run Deterministic Evaluation
        deterministic = evaluate_deterministic_metrics(final_state, scenario)

        # 4. Run LLM-as-Judge Evaluation
        judge_report = await self.judge.evaluate(final_state, scenario)

        # 5. Classify Errors
        errors = classify_investigation_errors(
            state=final_state,
            scenario=scenario,
            deterministic=deterministic,
            judge_identified_flaws=judge_report.identified_flaws,
        )

        # Gate pass determination
        passed = (
            deterministic.structural_citation_validity == 1.0
            and deterministic.confidence_matched_expected_range
            and deterministic.overconfidence_penalty == 0
            and judge_report.overall_mean_score >= 3.0
            and len([e for e in errors if e.severity == "critical"]) == 0
        )

        return ScenarioRunResult(
            scenario_id=scenario.scenario_id,
            run_id=run_id,
            trial_index=trial_index,
            architecture_id=architecture_id,
            ablation_mode=ablation_mode,
            model_name=model_name,
            final_status=final_state.status,
            deterministic=deterministic,
            judge=judge_report,
            telemetry=telemetry,
            classified_errors=errors,
            passed_all_gates=passed,
        )
