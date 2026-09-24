"""Configuration, thresholds, and immutable pricing snapshots for Phase 9 evaluations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ModelPricing(BaseModel):
    """Token pricing rates per 1,000,000 tokens."""

    model_config = ConfigDict(frozen=True)
    input_cost_per_million: float
    output_cost_per_million: float


# Current OpenRouter verified pricing rates
DEFAULT_PRICING_RATES: dict[str, ModelPricing] = {
    "openai/gpt-5.4": ModelPricing(input_cost_per_million=2.50, output_cost_per_million=15.00),
    "anthropic/claude-sonnet-4.6": ModelPricing(
        input_cost_per_million=3.00, output_cost_per_million=15.00
    ),
}

# Model-specific provider routing configurations
MODEL_PROVIDER_ROUTING: dict[str, dict[str, object]] = {
    "openai/gpt-5.4": {
        "order": ["OpenAI"],
        "allow_fallbacks": False,
    },
    "anthropic/claude-sonnet-4.6": {
        "order": ["Anthropic"],
        "allow_fallbacks": False,
    },
}


class InvocationBudgetCeiling(BaseModel):
    """Budget limits for evaluation runs."""

    model_config = ConfigDict(frozen=True)
    max_llm_calls: int
    max_tool_calls: int


# Mode 1: Matched Invocation Budget (identical 25 LLM / 26 tool invocations across A, B, C)
MODE1_MATCHED_BUDGET = InvocationBudgetCeiling(max_llm_calls=25, max_tool_calls=26)

# Mode 2: Natural-Budget Operational Comparison
MODE2_NATURAL_BUDGETS: dict[str, InvocationBudgetCeiling] = {
    "baseline_a": InvocationBudgetCeiling(max_llm_calls=15, max_tool_calls=15),
    "baseline_b": InvocationBudgetCeiling(max_llm_calls=45, max_tool_calls=26),
    "candidate_c": InvocationBudgetCeiling(max_llm_calls=63, max_tool_calls=26),
}


class EvaluationThresholds(BaseModel):
    """Quality and regression acceptance gates."""

    model_config = ConfigDict(frozen=True)
    min_structural_citation_validity: float = 1.00  # Strict 100%
    min_context_recall: float = 0.85
    min_context_precision: float = 0.75
    min_groundedness_score: float = 3.20  # Native 0-4 scale
    min_cross_source_score: float = 3.00  # Native 0-4 scale
    min_contradiction_detection_rate: float = 0.80
    min_confidence_match_rate: float = 0.80
    max_overconfidence_penalty_count: int = 0
    min_critic_true_positive_rate: float = 0.80
    max_critic_false_positive_rate: float = 0.15
    min_judge_weighted_kappa_per_dimension: float = 0.75


EVALUATION_THRESHOLDS = EvaluationThresholds()

AblationMode = Literal["mode1_matched", "mode2_natural"]
ArchitectureId = Literal["baseline_a", "baseline_b", "candidate_c"]

# Reduced Benchmark Configuration (204 Planned Executions)
# 24 core scenarios x 3 architectures x 2 repetitions = 144
# 10 locked holdout scenarios x 3 architectures x 2 repetitions = 60
# Total = 204 runs
BENCHMARK_CORE_SCENARIO_IDS: list[str] = [
    # Transfers (6)
    "scn_001",
    "scn_002",
    "scn_003",
    "scn_004",
    "scn_005",
    "scn_009",
    # KYC (6)
    "scn_013",
    "scn_014",
    "scn_015",
    "scn_016",
    "scn_017",
    "scn_018",
    # Funding (6)
    "scn_024",
    "scn_025",
    "scn_026",
    "scn_027",
    "scn_028",
    "scn_030",
    # Bill Payments (6)
    "scn_035",
    "scn_036",
    "scn_037",
    "scn_038",
    "scn_039",
    "scn_041",
]

BENCHMARK_HOLDOUT_SCENARIO_IDS: list[str] = [
    "scn_011",
    "scn_012",
    "scn_022",
    "scn_023",
    "scn_031",
    "scn_033",
    "scn_034",
    "scn_042",
    "scn_044",
    "scn_045",
]

BENCHMARK_REPETITIONS: int = 2
BENCHMARK_TOTAL_RUNS: int = (
    len(BENCHMARK_CORE_SCENARIO_IDS) * 3 * BENCHMARK_REPETITIONS
    + len(BENCHMARK_HOLDOUT_SCENARIO_IDS) * 3 * BENCHMARK_REPETITIONS
)  # 144 + 60 = 204
