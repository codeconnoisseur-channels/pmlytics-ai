"""PM revision node addressing Critic review feedback."""

import logging

from app.agents.pm import PMAgent
from app.domain.provenance import source_references_match
from app.domain.recommendation import ProductRecommendation
from app.integrations.llm.client import LLMClient
from app.integrations.observability.tracer import async_span_context
from app.orchestration.state import (
    GraphBudgetUsage,
    InvestigationState,
    InvestigationStateUpdate,
)

logger = logging.getLogger(__name__)


def validate_revised_recommendation(
    rec: ProductRecommendation, state: InvestigationState
) -> list[str]:
    """Pure deterministic validation of revised ProductRecommendation before acceptance.

    Returns a list of error strings. If empty, the revised recommendation is valid.
    """
    errors: list[str] = []

    # 1. ProductRecommendation schema validity & required recommendation fields
    if not rec.problem_statement or len(rec.problem_statement.strip()) < 10:
        errors.append("problem_statement is missing or shorter than 10 characters")
    if not rec.why_it_matters or len(rec.why_it_matters.strip()) < 10:
        errors.append("why_it_matters is missing or shorter than 10 characters")
    if not rec.affected_users or len(rec.affected_users.strip()) < 5:
        errors.append("affected_users is missing or shorter than 5 characters")
    if not rec.recommendation or len(rec.recommendation.strip()) < 10:
        errors.append("recommendation is missing or shorter than 10 characters")
    if not rec.factual_observations:
        errors.append("factual_observations cannot be empty")
    if not rec.inferences:
        errors.append("inferences cannot be empty")
    if not rec.evidence:
        errors.append("evidence citations cannot be empty")
    if not rec.success_metrics:
        errors.append("success_metrics cannot be empty")
    if not rec.risks:
        errors.append("risks cannot be empty")
    if rec.confidence not in ("high", "medium", "low"):
        errors.append(f"Invalid confidence '{rec.confidence}'; must be high, medium, or low")
    valid_types = {
        "prioritise",
        "investigate_further",
        "experiment",
        "technical_remediation",
        "monitor",
        "deprioritise",
    }
    if rec.recommendation_type not in valid_types:
        errors.append(f"Invalid recommendation_type '{rec.recommendation_type}'")

    # 2. Valid ledger-entry IDs & Citation resolution (no fabricated evidence identifiers)
    ledger_entries = state.evidence_ledger_entries
    for idx, ev in enumerate(rec.evidence):
        if not ev.ledger_entry_id or ev.ledger_entry_id not in ledger_entries:
            errors.append(
                f"Evidence[{idx}] cites unknown or fabricated ledger_entry_id: '{ev.ledger_entry_id}'"
            )
            continue
        entry = ledger_entries[ev.ledger_entry_id]
        if ev.source_type != entry.source_type:
            errors.append(
                f"Evidence[{idx}] source_type '{ev.source_type}' does not match ledger entry '{entry.source_type}'"
            )
        if not source_references_match(
            entry.source_type, entry.source_reference, ev.source_reference
        ):
            errors.append(
                f"Evidence[{idx}] source_reference '{ev.source_reference}' does not match ledger entry '{entry.source_reference}'"
            )

    # 3. Valid epistemic separation
    facts_set = {f.strip().lower() for f in rec.factual_observations if f}
    inferences_set = {i.strip().lower() for i in rec.inferences if i}
    hypotheses_set = {h.strip().lower() for h in rec.hypotheses if h}
    fact_inf_overlap = facts_set & inferences_set
    if fact_inf_overlap:
        errors.append(
            f"Epistemic violation: identical claims in facts and inferences: {fact_inf_overlap}"
        )
    fact_hyp_overlap = facts_set & hypotheses_set
    if fact_hyp_overlap:
        errors.append(
            f"Epistemic violation: identical claims in facts and hypotheses: {fact_hyp_overlap}"
        )

    # 4. Preserved contradiction and limitation structure
    if (state.limitations or (state.assessment and state.assessment.identified_gaps)) and not (
        rec.open_questions or rec.risks
    ):
        errors.append(
            "Preservation violation: known limitations exist but open_questions and risks are both empty"
        )

    return errors


class PMRevisionNode:
    """Orchestration node running PM revision in response to Critic feedback."""

    def __init__(self, llm_client: LLMClient, model_name: str | None = None) -> None:
        self.pm_agent = PMAgent(
            llm_client=llm_client,
            model_name=model_name,
            revision_model_name=model_name,
        )

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        """Run PM revision addressing latest CriticReview feedback."""
        next_revision = state.revision_count + 1
        logger.info(
            "Executing PM revision node (revision %d/%d) for investigation '%s'",
            next_revision,
            state.max_revisions,
            state.investigation_id,
        )

        if not state.critic_reviews:
            logger.warning("PM revision called without prior critic review; skipping")
            return {
                "revision_count": next_revision,
            }

        latest_review = state.critic_reviews[-1]
        if latest_review.decision == "PASS" or not state.recommendation:
            logger.info(
                "PM revision unnecessary (decision=%s, has_rec=%s)",
                latest_review.decision,
                bool(state.recommendation),
            )
            return {
                "revision_count": next_revision,
            }

        async with async_span_context(
            "pm_revision",
            run_type="chain",
            inputs={"revision": next_revision, "investigation_id": state.investigation_id},
        ):
            revised_rec, calls_made = await self.pm_agent.revise(
                state=state,
                previous_recommendation=state.recommendation,
                review=latest_review,
            )

        budget_update = GraphBudgetUsage(pm_llm_calls=calls_made)
        update: InvestigationStateUpdate = {
            "revision_count": next_revision,
            "budget_usage": budget_update,
        }

        if revised_rec is not None:
            val_errors = validate_revised_recommendation(revised_rec, state)
            if not val_errors:
                update["recommendation"] = revised_rec
                logger.info(
                    "PM revision succeeded deterministic validation; updated candidate recommendation"
                )
            else:
                logger.error(
                    "PM revision failed deterministic validation (%d errors: %s); failing closed and retaining prior candidate",
                    len(val_errors),
                    "; ".join(val_errors),
                )
                update["limitations"] = [
                    f"PM revision {next_revision} failed deterministic validation ({'; '.join(val_errors)}); prior recommendation retained."
                ]
        else:
            logger.warning(
                "PM revision failed to satisfy schema after %d calls; retaining prior candidate",
                calls_made,
            )
            update["limitations"] = [
                f"PM revision {next_revision} failed to produce an improved schema-compliant recommendation."
            ]

        return update
