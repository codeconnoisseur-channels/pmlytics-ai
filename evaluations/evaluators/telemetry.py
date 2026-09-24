"""Telemetry, token accounting, and snapshot-based cost calculation for evaluation runs."""

from pydantic import BaseModel, ConfigDict, Field

from evaluations.config import DEFAULT_PRICING_RATES, ModelPricing


class RunTelemetry(BaseModel):
    """Resource usage, latency, and cost telemetry for an evaluation execution."""

    model_config = ConfigDict(frozen=True)
    model_id: str
    wall_clock_seconds: float = 0.0
    total_llm_calls: int = 0
    total_tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    node_latencies: dict[str, float] = Field(default_factory=dict)


def calculate_cost_from_snapshot(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    pricing_snapshot: dict[str, ModelPricing] | None = None,
) -> float:
    """Calculate exact USD cost from an immutable pricing snapshot."""
    rates = pricing_snapshot or DEFAULT_PRICING_RATES
    model_rate = rates.get(model_id)

    if not model_rate:
        # Fallback to default pricing lookup if model rate not in snapshot
        model_rate = DEFAULT_PRICING_RATES.get(
            model_id, ModelPricing(input_cost_per_million=2.50, output_cost_per_million=15.00)
        )

    cost_in = (input_tokens / 1_000_000.0) * model_rate.input_cost_per_million
    cost_out = (output_tokens / 1_000_000.0) * model_rate.output_cost_per_million
    return round(cost_in + cost_out, 6)
