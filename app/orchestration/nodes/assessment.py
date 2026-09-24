"""Assessment node evaluating evidence sufficiency with bounded repair loops."""

import json
import logging

from app.config.settings import get_model_for_role, get_settings
from app.integrations.llm.client import LLMClient, LLMMessage
from app.orchestration.prompts import ASSESSMENT_SYSTEM_PROMPT
from app.orchestration.state import (
    EvidenceAssessment,
    GraphBudgetUsage,
    InvestigationState,
    InvestigationStateUpdate,
)
from app.orchestration.validation import (
    ProvenanceValidationError,
    validate_investigation_evidence,
)
from app.tools.base import ToolError

logger = logging.getLogger(__name__)


class AssessmentNode:
    """Orchestration node responsible for evaluating evidentiary sufficiency."""

    def __init__(self, llm_client: LLMClient, model_name: str | None = None) -> None:
        self.llm = llm_client
        self.model_name = model_name or get_model_for_role("assessment")

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        """Evaluate aggregated evidence against plan objectives."""
        cfg = get_settings()
        is_standard = cfg.investigation_profile == "standard"
        max_repairs = 0 if is_standard else 2

        # 1. Enforce graph-level tripartite provenance invariant
        try:
            validate_investigation_evidence(state)
        except ProvenanceValidationError as pve:
            logger.error("Graph provenance validation failed before assessment: %s", pve)
            prov_error = ToolError(
                error_type="upstream_error",
                message=str(pve),
                attempted_source=None,
            )
            prov_assessment = EvidenceAssessment(
                sufficient_for_synthesis=False,
                has_blocking_gaps=True,
                identified_gaps=[f"Provenance violation detected: {str(pve)}"],
            )
            return {
                "assessment": prov_assessment,
                "tool_errors": [prov_error],
                "sufficient_for_synthesis": False,
            }

        # 2. Build compact summary of gathered findings for evaluation
        summary_payload = {
            "user_query": state.user_query,
            "objectives": state.plan.objectives if state.plan else [],
            "customer_findings": [
                {
                    "finding": f.finding,
                    "observed_pattern": f.observed_pattern,
                    "interpretations": f.interpretations,
                    "confidence": f.confidence.value,
                    "evidence_count": len(f.evidence),
                }
                for f in state.customer_findings
            ],
            "analytics_findings": [
                {
                    "metric": f.metric,
                    "value": f.value,
                    "finding": f.finding,
                    "interpretations": f.interpretations,
                    "confidence": f.confidence.value,
                    "evidence_count": len(f.evidence),
                }
                for f in state.analytics_findings
            ],
            "engineering_findings": [
                {
                    "finding": f.finding,
                    "issue_status": f.issue_status,
                    "technical_context": f.technical_context,
                    "interpretations": f.interpretations,
                    "confidence": f.confidence.value,
                    "evidence_count": len(f.evidence),
                }
                for f in state.engineering_findings
            ],
            "tool_errors": [
                {"error_type": e.error_type, "message": e.message, "source": e.attempted_source}
                for e in state.tool_errors
            ],
            "limitations": state.limitations,
        }

        user_content_parts = [
            "AGGREGATED INVESTIGATION EVIDENCE:",
            json.dumps(summary_payload, default=str, indent=2),
            "",
            "Evaluate whether the evidence is sufficient for PM synthesis or if blocking gaps remain.",
            "Return a direct JSON object matching this schema instance (do NOT return JSON Schema definitions with 'properties' or 'type'):",
            "```json",
            "{",
            '  "sufficient_for_synthesis": true,',
            '  "has_blocking_gaps": false,',
            '  "identified_gaps": [],',
            '  "contradictions_identified": [],',
            '  "confidence": "high",',
            '  "recommended_specialist": null,',
            '  "recommended_gap": null,',
            '  "recommended_objective": null,',
            '  "recommended_questions": []',
            "}",
            "```",
        ]

        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=ASSESSMENT_SYSTEM_PROMPT),
            LLMMessage(role="user", content="\n".join(user_content_parts)),
        ]

        repair_attempts = 0
        calls_made = 0
        assessment: EvidenceAssessment | None = None
        last_error_msg = ""

        while repair_attempts <= max_repairs:
            calls_made += 1
            try:
                raw_assessment = await self.llm.complete_structured(
                    messages=messages,
                    model=self.model_name,
                    response_model=EvidenceAssessment,
                    temperature=0.0,
                    role="planner",
                )

                # Standard profile invariant: suppress specialist follow-up
                if is_standard:
                    if (
                        raw_assessment.recommended_specialist is not None
                        or raw_assessment.recommended_gap is not None
                    ):
                        logger.info(
                            "Standard mode: suppressing recommended specialist follow-up in Assessment"
                        )
                        raw_assessment = raw_assessment.model_copy(
                            update={"recommended_specialist": None, "recommended_gap": None}
                        )
                else:
                    # Validate gap binding rule in Deep mode: recommended_gap must be in identified_gaps if provided
                    if raw_assessment.recommended_specialist is not None:
                        if not raw_assessment.recommended_gap:
                            raise ValueError(
                                "recommended_gap must be specified when recommending a follow-up specialist."
                            )
                        if raw_assessment.recommended_gap not in raw_assessment.identified_gaps:
                            raise ValueError(
                                f"recommended_gap '{raw_assessment.recommended_gap}' is not present in identified_gaps: "
                                f"{raw_assessment.identified_gaps}."
                            )

                assessment = raw_assessment
                break

            except Exception as exc:
                repair_attempts += 1
                last_error_msg = str(exc)
                logger.warning(
                    "Assessment structured evaluation failed (attempt %d/%d): %s",
                    calls_made,
                    max_repairs + 1,
                    exc,
                )
                if repair_attempts <= max_repairs:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                f"VALIDATION ERROR IN OUTPUT:\n{str(exc)}\n\n"
                                f"Return a direct JSON object instance (not a JSON Schema definition). "
                                f"Ensure sufficient_for_synthesis, has_blocking_gaps, identified_gaps, "
                                f"contradictions_identified, and confidence are valid fields."
                            ),
                        )
                    )

        if assessment is None:
            logger.error(
                "Assessment failed after %d calls; using deterministic fallback assessment",
                calls_made,
            )
            assessment = EvidenceAssessment(
                sufficient_for_synthesis=False,
                has_blocking_gaps=True,
                identified_gaps=[
                    f"Assessment evaluation failed after {calls_made} attempts: {last_error_msg}"
                ],
            )
            fallback_error = ToolError(
                error_type="upstream_error",
                message=f"Assessment failed structured completion: {last_error_msg}",
                attempted_source=None,
            )
            return {
                "assessment": assessment,
                "tool_errors": [fallback_error],
                "sufficient_for_synthesis": False,
                "budget_usage": GraphBudgetUsage(assessment_llm_calls=calls_made),
            }

        return {
            "assessment": assessment,
            "sufficient_for_synthesis": assessment.sufficient_for_synthesis,
            "budget_usage": GraphBudgetUsage(assessment_llm_calls=calls_made),
        }
