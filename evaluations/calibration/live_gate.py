"""Explicit approval and preflight controls for any paid evaluation call."""

import os

from pydantic import BaseModel, ConfigDict, Field

PAID_EVALUATION_ENV = "PMLYTICS_ALLOW_PAID_EVALUATIONS"


class PaidEvaluationPreflight(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_count: int = Field(ge=1)
    model_name: str
    estimated_input_tokens: int = Field(ge=0)
    maximum_output_tokens: int = Field(ge=0)
    estimated_maximum_cost_usd: float = Field(ge=0)
    approved_maximum_cost_usd: float = Field(gt=0)
    cache_hits: int = Field(ge=0)
    provider_calls_required: int = Field(ge=0)


def calculate_preflight(
    *,
    case_count: int,
    cache_hits: int,
    model_name: str,
    estimated_input_tokens_per_case: int,
    maximum_output_tokens_per_case: int,
    input_cost_per_million: float,
    output_cost_per_million: float,
    approved_maximum_cost_usd: float,
) -> PaidEvaluationPreflight:
    if cache_hits > case_count:
        raise ValueError("Cache hits cannot exceed selected cases")
    provider_calls = case_count - cache_hits
    input_tokens = provider_calls * estimated_input_tokens_per_case
    output_tokens = provider_calls * maximum_output_tokens_per_case
    estimated_cost = (
        input_tokens / 1_000_000 * input_cost_per_million
        + output_tokens / 1_000_000 * output_cost_per_million
    )
    return PaidEvaluationPreflight(
        case_count=case_count,
        model_name=model_name,
        estimated_input_tokens=input_tokens,
        maximum_output_tokens=output_tokens,
        estimated_maximum_cost_usd=round(estimated_cost, 6),
        approved_maximum_cost_usd=approved_maximum_cost_usd,
        cache_hits=cache_hits,
        provider_calls_required=provider_calls,
    )


def require_paid_evaluation_opt_in(
    *,
    live: bool,
    preflight: PaidEvaluationPreflight,
) -> None:
    """Fail closed unless paid execution and its maximum spend are explicit."""
    if not live:
        raise PermissionError("Paid evaluation is disabled. Pass an explicit live opt-in.")
    if os.getenv(PAID_EVALUATION_ENV, "").lower() != "true":
        raise PermissionError(
            f"Paid evaluation is disabled. Set {PAID_EVALUATION_ENV}=true for this command."
        )
    if preflight.provider_calls_required == 0:
        return
    if preflight.estimated_maximum_cost_usd > preflight.approved_maximum_cost_usd:
        raise PermissionError(
            "Estimated maximum provider cost exceeds the explicitly approved budget"
        )
