"""Frozen pricing snapshot and internal cost audit calculation."""

from typing import NamedTuple


class ModelPriceRate(NamedTuple):
    """Immutable pricing rate per 1,000,000 tokens."""

    input_cost_per_million: float
    output_cost_per_million: float


# Frozen snapshot effective date: 2026-09-01
PRICING_SNAPSHOT_VERSION = "2026-09-01-frozen"

PRICING_SNAPSHOT_RATES: dict[str, ModelPriceRate] = {
    "openai/gpt-5.4": ModelPriceRate(input_cost_per_million=2.50, output_cost_per_million=15.00),
    "anthropic/claude-sonnet-4.6": ModelPriceRate(
        input_cost_per_million=3.00, output_cost_per_million=15.00
    ),
}


def calculate_internal_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    """Calculate internal estimated cost from the frozen pricing snapshot.

    Used strictly as an audit / cross-check mechanism. Never substitutes for provider-reported cost.
    """
    rate = PRICING_SNAPSHOT_RATES.get(model)
    if not rate:
        # Check without provider prefix
        for key, r in PRICING_SNAPSHOT_RATES.items():
            if model.endswith(key.split("/")[-1]):
                rate = r
                break
    if not rate:
        return None

    cost_in = (prompt_tokens / 1_000_000.0) * rate.input_cost_per_million
    cost_out = (completion_tokens / 1_000_000.0) * rate.output_cost_per_million
    return round(cost_in + cost_out, 8)
