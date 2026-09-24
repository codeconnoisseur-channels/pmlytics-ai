"""PM synthesis node generating candidate ProductRecommendations."""

import logging

from app.agents.pm import PMAgent
from app.integrations.llm.client import LLMClient
from app.integrations.observability.tracer import async_span_context
from app.orchestration.state import (
    GraphBudgetUsage,
    InvestigationState,
    InvestigationStateUpdate,
)

logger = logging.getLogger(__name__)


class PMSynthesisNode:
    """Orchestration node running PM synthesis on the aggregated investigation state."""

    def __init__(self, llm_client: LLMClient, model_name: str | None = None) -> None:
        self.pm_agent = PMAgent(llm_client=llm_client, model_name=model_name)

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        """Run PM synthesis with budget tracking and safe fallback."""
        logger.info("Executing PM synthesis node for investigation '%s'", state.investigation_id)

        async with async_span_context(
            "pm_synthesis", run_type="chain", inputs={"investigation_id": state.investigation_id}
        ):
            recommendation, calls_made = await self.pm_agent.synthesize(state)

        budget_update = GraphBudgetUsage(pm_llm_calls=calls_made)
        update: InvestigationStateUpdate = {
            "budget_usage": budget_update,
        }

        if recommendation is not None:
            update["recommendation"] = recommendation
            logger.info(
                "PM synthesis produced candidate recommendation: '%s'",
                recommendation.recommendation[:50],
            )
        else:
            logger.warning(
                "PM synthesis failed to produce a valid recommendation after %d attempts; safe fallback engaged",
                calls_made,
            )
            update["limitations"] = [
                "PM synthesis could not generate a schema-compliant recommendation from the available evidence."
            ]

        return update
