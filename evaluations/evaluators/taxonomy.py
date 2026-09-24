"""16-class error taxonomy classifier for failed or flawed evaluation investigations."""

from typing import Literal

from app.orchestration.state import InvestigationState
from pydantic import BaseModel, ConfigDict

from evaluations.evaluators.deterministic import DeterministicMetrics
from evaluations.ground_truth.schema import EvaluationScenario

ErrorClass = Literal[
    "PLANNING_ERROR",
    "TOOL_SELECTION_ERROR",
    "TOOL_ARGUMENT_ERROR",
    "RETRIEVAL_MISS",
    "IRRELEVANT_RETRIEVAL",
    "DATA_INTERPRETATION_ERROR",
    "CROSS_SOURCE_REASONING_ERROR",
    "CONTRADICTION_MISS",
    "CAUSAL_OVERREACH",
    "SEGMENTATION_ERROR",
    "UNSUPPORTED_CLAIM",
    "RECOMMENDATION_ERROR",
    "CRITIC_MISS",
    "CRITIC_FALSE_POSITIVE",
    "REVISION_FAILURE",
    "SYSTEM_FAILURE",
]


class ClassifiedError(BaseModel):
    """Detailed error taxonomy classification."""

    model_config = ConfigDict(frozen=True)
    category: ErrorClass
    description: str
    severity: Literal["critical", "material", "minor"]


def classify_investigation_errors(
    state: InvestigationState,
    scenario: EvaluationScenario,
    deterministic: DeterministicMetrics,
    judge_identified_flaws: list[str] | None = None,
) -> list[ClassifiedError]:
    """Classify defects in an investigation run against the 16 formal error categories."""
    errors: list[ClassifiedError] = []
    flaws = [f.lower() for f in (judge_identified_flaws or [])]

    # 1. System Failure
    if state.status == "failed":
        errors.append(
            ClassifiedError(
                category="SYSTEM_FAILURE",
                description="Investigation terminated in failed state.",
                severity="critical",
            )
        )
        return errors

    # 2. Tool / Infrastructure Errors
    if state.tool_errors and not scenario.is_source_outage:
        errors.append(
            ClassifiedError(
                category="TOOL_ARGUMENT_ERROR",
                description=f"Tool errors occurred during execution: {[e.message for e in state.tool_errors]}",
                severity="material",
            )
        )

    # 3. Source Selection & Planning
    if deterministic.source_selection_recall < 1.0:
        errors.append(
            ClassifiedError(
                category="TOOL_SELECTION_ERROR",
                description=f"Failed to query required sources: {scenario.required_sources}",
                severity="critical",
            )
        )

    # 4. Retrieval Miss
    if deterministic.context_recall < 0.5:
        errors.append(
            ClassifiedError(
                category="RETRIEVAL_MISS",
                description=f"Context recall was critically low: {deterministic.context_recall:.1%}",
                severity="critical",
            )
        )
    elif deterministic.context_recall < 0.85:
        errors.append(
            ClassifiedError(
                category="RETRIEVAL_MISS",
                description=f"Missed some required ground truth evidence: {deterministic.context_recall:.1%}",
                severity="material",
            )
        )

    # 5. Irrelevant Retrieval
    if deterministic.context_precision < 0.5 and deterministic.unique_retrieved_records_count > 3:
        errors.append(
            ClassifiedError(
                category="IRRELEVANT_RETRIEVAL",
                description=f"Low retrieval precision ({deterministic.context_precision:.1%}) indicates excess noise.",
                severity="minor",
            )
        )

    # 6. Unsupported Citations / Hallucinations
    if deterministic.hallucinated_citations > 0:
        errors.append(
            ClassifiedError(
                category="UNSUPPORTED_CLAIM",
                description=f"Found {deterministic.hallucinated_citations} hallucinated or unretrieved citation references.",
                severity="critical",
            )
        )

    # 7. Contradiction Miss
    if scenario.has_contradiction and any("contradiction" in flaw for flaw in flaws):
        errors.append(
            ClassifiedError(
                category="CONTRADICTION_MISS",
                description="Failed to surface or reconcile the known contradiction in the scenario data.",
                severity="critical",
            )
        )

    # 8. Causal Overreach
    if scenario.is_causal_trap and any("causal" in flaw for flaw in flaws):
        errors.append(
            ClassifiedError(
                category="CAUSAL_OVERREACH",
                description="Unjustified causal assertion made or fell into scenario causality trap.",
                severity="critical",
            )
        )

    # 9. Segmentation Error
    if scenario.is_segmentation_trap and any("segment" in flaw for flaw in flaws):
        errors.append(
            ClassifiedError(
                category="SEGMENTATION_ERROR",
                description="Failed to correctly identify or isolate the affected user cohort.",
                severity="material",
            )
        )

    # 10. Critic False Positive
    if scenario.is_critic_true_negative and state.revision_count > 0:
        errors.append(
            ClassifiedError(
                category="CRITIC_FALSE_POSITIVE",
                description="Critic rejected a sound recommendation requiring unnecessary revision.",
                severity="minor",
            )
        )

    # 11. Critic Miss
    if scenario.is_critic_true_positive and state.revision_count == 0:
        errors.append(
            ClassifiedError(
                category="CRITIC_MISS",
                description="Critic passed a recommendation containing known flaws or unsupported assertions.",
                severity="critical",
            )
        )

    # 12. Recommendation Error
    if state.recommendation:
        rec_type = state.recommendation.recommendation_type
        if rec_type not in scenario.acceptable_recommendation_types:
            errors.append(
                ClassifiedError(
                    category="RECOMMENDATION_ERROR",
                    description=f"Recommendation action '{rec_type}' not in acceptable types {scenario.acceptable_recommendation_types}",
                    severity="material",
                )
            )

    return errors
