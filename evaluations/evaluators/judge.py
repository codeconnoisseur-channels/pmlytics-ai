"""Calibrated LLM-as-Judge semantic evaluator with bounded repair loop."""

import logging
from typing import Literal

from app.agents.ledger import EvidenceLedgerEntry
from app.config.settings import get_model_for_role
from app.domain.recommendation import ProductRecommendation
from app.integrations.llm.client import LLMClient, LLMMessage
from app.orchestration.state import InvestigationState
from pydantic import BaseModel, ConfigDict, Field

from evaluations.evaluators.prompts.judge_prompt import JUDGE_SYSTEM_PROMPT
from evaluations.ground_truth.schema import EvaluationScenario

logger = logging.getLogger(__name__)


class JudgeDimensionScore(BaseModel):
    """Calibrated score and justification for one evaluation dimension."""

    model_config = ConfigDict(frozen=True)
    score: int = Field(..., ge=0, le=4)
    reasoning: str = Field(..., min_length=5)


class ClaimEvidenceAudit(BaseModel):
    """Claim-level supporting analysis for a material assertion in the candidate output."""

    model_config = ConfigDict(frozen=True)
    claim_text: str
    field_location: str  # e.g. 'problem_statement', 'factual_observations', 'inferences', 'hypotheses', 'recommendation'
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    support_classification: Literal[
        "FULLY_SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "UNSUPPORTED_ADDITION",
        "CONTRADICTED",
    ]
    causal_classification: (
        Literal[
            "DIRECT_CAUSAL_EVIDENCE",
            "LEGITIMATE_INFERENCE",
            "EVIDENCE_INFORMED_HYPOTHESIS",
            "UNSUPPORTED_CAUSAL_ASSERTION",
            "POST_HOC_FALLACY",
            "NOT_APPLICABLE",
        ]
        | None
    ) = None
    detected_contradiction: str | None = None
    score_rationale: str


class EvaluationJudgeReport(BaseModel):
    """Structured report produced by the calibrated LLM Judge."""

    model_config = ConfigDict(frozen=True)
    groundedness: JudgeDimensionScore
    cross_source_reasoning: JudgeDimensionScore
    contradiction_handling: JudgeDimensionScore
    causal_discipline: JudgeDimensionScore
    recommendation_defensibility: JudgeDimensionScore
    claim_audits: list[ClaimEvidenceAudit] = Field(default_factory=list)
    identified_flaws: list[str] = Field(default_factory=list)
    overall_mean_score: float = 0.0


JUDGE_IMPLEMENTATION_VERSION = "v3.0-context-integrity-patch"


def extract_evidence_support_excerpt(
    entry: EvidenceLedgerEntry, state: InvestigationState | None = None
) -> str:
    """Extract full factual support text from an evidence ledger entry's typed payload or state citations."""
    support_parts: list[str] = []

    # 0. Check direct support attribute if present on entry (e.g. entry.support)
    direct_support = getattr(entry, "support", None)
    if direct_support and isinstance(direct_support, str) and direct_support not in support_parts:
        support_parts.append(direct_support)

    # 1. Extract from typed payload if available
    payload = getattr(entry, "typed_payload", None)
    if payload is not None:
        from app.domain.analytics import AnalyticsQueryResult
        from app.domain.jira import JiraComment, JiraIssue
        from app.domain.zendesk import ZendeskComment, ZendeskTicket
        from app.tools.analytics import QueryAnalyticsOutput
        from app.tools.engineering import GetIssueCommentsOutput, GetIssueOutput
        from app.tools.support import GetTicketCommentsOutput, GetTicketOutput

        if (
            isinstance(payload, ZendeskTicket)
            and payload.description
            or isinstance(payload, JiraIssue)
            and payload.description
        ):
            if payload.description not in support_parts:
                support_parts.append(payload.description)
        elif isinstance(payload, QueryAnalyticsOutput):
            val = str(payload.result.value) if payload.result.value is not None else ""
            if val and val not in support_parts:
                support_parts.append(val)
        elif isinstance(payload, AnalyticsQueryResult):
            val = str(payload.value) if payload.value is not None else ""
            if val and val not in support_parts:
                support_parts.append(val)
        elif isinstance(payload, GetTicketOutput) and payload.ticket.description:
            if payload.ticket.description not in support_parts:
                support_parts.append(payload.ticket.description)
        elif isinstance(payload, GetIssueOutput) and payload.issue.description:
            if payload.issue.description not in support_parts:
                support_parts.append(payload.issue.description)
        elif (
            isinstance(payload, GetTicketCommentsOutput)
            and payload.comments
            or isinstance(payload, GetIssueCommentsOutput)
            and payload.comments
        ):
            comment_text = "; ".join(c.body for c in payload.comments)
            if comment_text and comment_text not in support_parts:
                support_parts.append(comment_text)
        elif (
            isinstance(payload, list)
            and payload
            and isinstance(payload[0], (ZendeskComment, JiraComment))
        ):
            comment_text = "; ".join(c.body for c in payload)
            if comment_text and comment_text not in support_parts:
                support_parts.append(comment_text)

    # 2. Extract from specialist findings in state
    if state:
        all_findings = []
        if state.customer_findings:
            all_findings.extend(state.customer_findings)
        if state.analytics_findings:
            all_findings.extend(state.analytics_findings)
        if state.engineering_findings:
            all_findings.extend(state.engineering_findings)
        for finding in all_findings:
            for ev in getattr(finding, "evidence", []):
                if (
                    getattr(ev, "ledger_entry_id", None) == entry.ledger_entry_id
                    and getattr(ev, "support", None)
                    and ev.support not in support_parts
                ):
                    support_parts.append(ev.support)

    # 3. Extract from candidate recommendation evidence citations if matching entry ID
    if state and state.recommendation and state.recommendation.evidence:
        for ev in state.recommendation.evidence:
            if (
                ev.ledger_entry_id == entry.ledger_entry_id
                and ev.support
                and ev.support not in support_parts
            ):
                support_parts.append(ev.support)

    return " | ".join(support_parts)


class LLMJudgeEvaluator:
    """Calibrated semantic evaluator auditing recommendations against evidence ledger."""

    def __init__(self, llm_client: LLMClient, model_name: str | None = None) -> None:
        self.llm = llm_client
        self.model_name = model_name or get_model_for_role(
            "critic"
        )  # Use critic-tier model default

    def _assemble_judge_context(
        self,
        state: InvestigationState,
        scenario: EvaluationScenario,
        rec: ProductRecommendation,
    ) -> str:
        """Construct the evaluation payload for the judge strictly from evidence ledger and query (no ground truth)."""
        ledger_lines: list[str] = []
        for eid, entry in state.evidence_ledger_entries.items():
            support_text = extract_evidence_support_excerpt(entry, state)
            entry_str = (
                f"- [{eid}] ({entry.source_type}) {entry.source_reference}:\n"
                f"  Finding/Summary: {entry.data_summary}"
            )
            if support_text:
                entry_str += f"\n  Support Excerpt: {support_text}"
            if entry.retrieved_at:
                entry_str += f"\n  Retrieved At: {entry.retrieved_at.isoformat()}"
            ledger_lines.append(entry_str)

        joined_ledger = "\n".join(ledger_lines) if ledger_lines else "(No evidence ledger entries)"

        return (
            f"=== INVESTIGATION QUESTION ===\n"
            f"User Query: {scenario.user_query}\n"
            f"Product Area: {scenario.product_area}\n\n"
            f"=== VERIFIED EVIDENCE LEDGER AVAILABLE TO AGENT ===\n"
            f"{joined_ledger}\n\n"
            f"=== FINAL SUT PRODUCT RECOMMENDATION UNDER EVALUATION ===\n"
            f"{rec.model_dump_json(indent=2)}\n\n"
            f"Evaluate the recommendation across all 5 dimensions on the 0-4 scale according to the rubric."
        )

    async def evaluate(
        self,
        state: InvestigationState,
        scenario: EvaluationScenario,
    ) -> EvaluationJudgeReport:
        """Run the LLM-as-Judge evaluation with bounded self-repair."""
        rec = state.recommendation
        if not rec:
            # Fallback report when no recommendation was synthesized
            zero_score = JudgeDimensionScore(
                score=0, reasoning="No recommendation synthesized by SUT."
            )
            return EvaluationJudgeReport(
                groundedness=zero_score,
                cross_source_reasoning=zero_score,
                contradiction_handling=zero_score,
                causal_discipline=zero_score,
                recommendation_defensibility=zero_score,
                identified_flaws=["NO_RECOMMENDATION_PRODUCED"],
                overall_mean_score=0.0,
            )

        context = self._assemble_judge_context(state, scenario, rec)
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=JUDGE_SYSTEM_PROMPT),
            LLMMessage(role="user", content=context),
        ]

        # Bounded repair loop (max 2 repair attempts, max 3 LLM calls total)
        for attempt in range(3):
            try:
                response = await self.llm.complete_structured(
                    messages=messages,
                    response_model=EvaluationJudgeReport,
                    model=self.model_name,
                    temperature=0.0,
                )
                mean_score = round(
                    (
                        response.groundedness.score
                        + response.cross_source_reasoning.score
                        + response.contradiction_handling.score
                        + response.causal_discipline.score
                        + response.recommendation_defensibility.score
                    )
                    / 5.0,
                    2,
                )
                return response.model_copy(update={"overall_mean_score": mean_score})
            except Exception as e:
                logger.warning("Judge evaluation attempt %d failed: %s", attempt + 1, e)
                messages.append(
                    LLMMessage(
                        role="user",
                        content=f"Schema validation error: {e}. Output strictly valid JSON matching EvaluationJudgeReport.",
                    )
                )

        # Fail-closed fallback
        err_score = JudgeDimensionScore(
            score=1, reasoning="Judge structured parsing failed after retries."
        )
        return EvaluationJudgeReport(
            groundedness=err_score,
            cross_source_reasoning=err_score,
            contradiction_handling=err_score,
            causal_discipline=err_score,
            recommendation_defensibility=err_score,
            identified_flaws=["JUDGE_PARSE_FAILURE"],
            overall_mean_score=1.0,
        )
