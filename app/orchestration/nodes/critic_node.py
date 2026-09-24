"""Critic node reviewing candidate ProductRecommendations against the evidence ledger."""

import logging

from app.agents.critic import CriticAgent
from app.domain.critic import CriticReview
from app.integrations.llm.client import LLMClient
from app.integrations.observability.tracer import async_span_context
from app.orchestration.state import (
    GraphBudgetUsage,
    InvestigationState,
    InvestigationStateUpdate,
)
from app.orchestration.validation import validate_critic_provenance

logger = logging.getLogger(__name__)


class CriticNode:
    """Orchestration node performing adversarial critique on candidate recommendations."""

    def __init__(self, llm_client: LLMClient, model_name: str | None = None) -> None:
        self.critic_agent = CriticAgent(llm_client=llm_client, model_name=model_name)

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        """Run critic evaluation on candidate recommendation."""
        logger.info("Executing Critic node for investigation '%s'", state.investigation_id)

        if state.recommendation is None:
            logger.warning(
                "Critic called with no candidate recommendation -> emitting fallback REVISE"
            )
            from app.domain.critic import CriticIssue

            fallback_review = CriticReview(
                decision="REVISE",
                issues=[
                    CriticIssue(
                        category="missing_evidence",
                        claim="Candidate recommendation",
                        problem="Candidate recommendation is missing or failed synthesis.",
                        supporting_ledger_entry_ids=[],
                        required_change="Produce a valid candidate ProductRecommendation.",
                    )
                ],
                overall_assessment="Cannot critique absent recommendation.",
                required_changes=["Provide a complete candidate recommendation for critique."],
            )
            return {
                "critic_reviews": [fallback_review],
                "budget_usage": GraphBudgetUsage(critic_llm_calls=0),
            }

        async with async_span_context(
            "critic", run_type="chain", inputs={"investigation_id": state.investigation_id}
        ):
            review, calls_made = await self.critic_agent.review(state, state.recommendation)

        # Validate critic provenance invariants
        try:
            validate_critic_provenance(review, state)
        except Exception as exc:
            logger.error("Critic review failed provenance validation: %s", exc)
            # Filter out invalid ledger references safely
            valid_ids = set(state.evidence_ledger_entries.keys())
            sanitized_issues = [
                issue.model_copy(
                    update={
                        "supporting_ledger_entry_ids": [
                            lid for lid in issue.supporting_ledger_entry_ids if lid in valid_ids
                        ]
                    }
                )
                for issue in review.issues
            ]
            review = review.model_copy(update={"issues": sanitized_issues})

        logger.info(
            "Critic review completed with decision: %s (%d issues, %d LLM calls)",
            review.decision,
            len(review.issues),
            calls_made,
        )

        return {
            "critic_reviews": [review],
            "budget_usage": GraphBudgetUsage(critic_llm_calls=calls_made),
        }
