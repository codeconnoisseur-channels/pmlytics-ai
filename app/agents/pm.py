"""PM Agent synthesizing multi-agent investigation evidence into grounded ProductRecommendations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.agents.prompts.pm_prompt import (
    PM_REPORT_SHAPING_GUIDANCE,
    PM_REVISION_SYSTEM_PROMPT,
    PM_SYNTHESIS_SYSTEM_PROMPT,
)
from app.config.settings import get_model_for_role
from app.domain.critic import CriticReview
from app.domain.recommendation import ProductRecommendation
from app.integrations.llm.client import LLMClient, LLMMessage

if TYPE_CHECKING:
    from app.orchestration.state import InvestigationState

logger = logging.getLogger(__name__)


class PMAgent:
    """Product Manager Agent for grounded evidence synthesis and iterative revision."""

    def __init__(
        self,
        llm_client: LLMClient,
        model_name: str | None = None,
        revision_model_name: str | None = None,
    ) -> None:
        self.llm = llm_client
        self.model_name = model_name or get_model_for_role("pm")
        self.revision_model_name = revision_model_name or get_model_for_role("pm_revision")

    def _build_evidence_context(self, state: InvestigationState) -> str:
        """Format raw specialist findings, ledger entries, and limitations into context."""
        parts: list[str] = [
            f"INVESTIGATION QUERY: {state.user_query}",
            f"INVESTIGATION ID: {state.investigation_id}",
            f"ROUND: {state.round_index} (max {state.max_rounds})",
            "",
            "=== AUTHORITATIVE APPEND-ONLY EVIDENCE LEDGER ===",
        ]
        if not state.evidence_ledger_entries:
            parts.append("(No evidence entries retrieved)")
        else:
            for entry_id, entry in sorted(state.evidence_ledger_entries.items()):
                parts.append(
                    f"[{entry_id}] ({entry.source_type}) ref={entry.source_reference}\n"
                    f"  summary: {entry.data_summary}"
                )

        parts.append("\n=== CUSTOMER FINDINGS (SUPPORT) ===")
        if not state.customer_findings:
            parts.append("(None)")
        else:
            for cf in state.customer_findings:
                ev_ids = [e.ledger_entry_id for e in cf.evidence]
                parts.append(
                    f"- Finding: {cf.finding}\n"
                    f"  pattern: {cf.observed_pattern}\n"
                    f"  interpretations: {cf.interpretations}\n"
                    f"  evidence_ids: {ev_ids}\n"
                    f"  confidence: {cf.confidence.value}\n"
                    f"  limitations: {cf.limitations}"
                )

        parts.append("\n=== ANALYTICS FINDINGS (POSTHOG) ===")
        if not state.analytics_findings:
            parts.append("(None)")
        else:
            for af in state.analytics_findings:
                ev_ids = [e.ledger_entry_id for e in af.evidence]
                parts.append(
                    f"- Finding: {af.finding}\n"
                    f"  metric: {af.metric} = {af.value} (comparison: {af.comparison})\n"
                    f"  interpretations: {af.interpretations}\n"
                    f"  evidence_ids: {ev_ids}\n"
                    f"  confidence: {af.confidence.value}\n"
                    f"  limitations: {af.limitations}"
                )

        parts.append("\n=== ENGINEERING FINDINGS (JIRA) ===")
        if not state.engineering_findings:
            parts.append("(None)")
        else:
            for ef in state.engineering_findings:
                ev_ids = [e.ledger_entry_id for e in ef.evidence]
                parts.append(
                    f"- Finding: {ef.finding}\n"
                    f"  status: {ef.issue_status}, context: {ef.technical_context}\n"
                    f"  interpretations: {ef.interpretations}\n"
                    f"  evidence_ids: {ev_ids}\n"
                    f"  confidence: {ef.confidence.value}\n"
                    f"  limitations: {ef.limitations}"
                )

        parts.append("\n=== KNOWN INVESTIGATION LIMITATIONS & TOOL ERRORS ===")
        if state.limitations:
            for lim in state.limitations:
                parts.append(f"- Limitation: {lim}")
        if state.tool_errors:
            for err in state.tool_errors:
                src = err.attempted_source or "unknown_source"
                parts.append(f"- Tool Error ({src}, type={err.error_type}): {err.message}")
        if not state.limitations and not state.tool_errors:
            parts.append("(None)")

        if state.assessment and not state.assessment.sufficient_for_synthesis:
            parts.append("\n=== EVIDENTIARY GAPS & LIMITATIONS FROM ASSESSMENT ===")
            parts.append(
                "Assessment determined evidence is incomplete/insufficient for definitive synthesis."
            )
            if state.assessment.identified_gaps:
                parts.append("Identified Gaps:")
                for gap in state.assessment.identified_gaps:
                    parts.append(f"  - {gap}")
            if state.assessment.recommended_questions:
                parts.append("Unanswered Questions / Diagnostic Gaps:")
                for uq in state.assessment.recommended_questions:
                    parts.append(f"  - {uq}")
            parts.append(
                "MANDATORY INSTRUCTION: You must explicitly preserve these gaps, unanswered questions, and limitations "
                "in your recommendation's open_questions and risks fields. DO NOT present missing or unretrieved evidence as established fact."
            )

        return "\n".join(parts)

    def _collect_revision_evidence_ids(
        self,
        state: InvestigationState,
        previous_recommendation: ProductRecommendation,
        review: CriticReview,
    ) -> set[str]:
        """Construct targeted revision working set from:
        1. evidence IDs explicitly attached to the Critic issues;
        2. evidence IDs associated with challenged recommendation claims;
        3. relevant contradiction and limitation entries;
        4. evidence IDs cited in the current recommendation.
        Falls back to full ledger only if necessary.
        """
        valid_ledger_ids = set(state.evidence_ledger_entries.keys())
        target_ids: set[str] = set()

        # 1. Evidence IDs explicitly attached to the Critic issues
        for issue in review.issues:
            for ev_id in issue.supporting_ledger_entry_ids:
                if ev_id in valid_ledger_ids:
                    target_ids.add(ev_id)

        # 2. Evidence IDs cited in previous recommendation (to verify/preserve/adjust citations)
        prev_rec_ev_ids = {
            ev.ledger_entry_id
            for ev in previous_recommendation.evidence
            if ev.ledger_entry_id in valid_ledger_ids
        }
        target_ids.update(prev_rec_ev_ids)

        # Check if issue claim or problem explicitly names any valid ledger ID
        for issue in review.issues:
            for lid in valid_ledger_ids:
                if lid in issue.claim or lid in issue.problem:
                    target_ids.add(lid)

        # 3. Relevant contradiction and limitation entries
        for lid, entry in state.evidence_ledger_entries.items():
            for conf in previous_recommendation.conflicting_evidence:
                if lid in conf or (entry.source_reference and entry.source_reference in conf):
                    target_ids.add(lid)
            for lim in state.limitations:
                if lid in lim or (entry.source_reference and entry.source_reference in lim):
                    target_ids.add(lid)

        # If target_ids is empty, add all evidence IDs referenced in specialist findings
        if not target_ids:
            for cf in state.customer_findings:
                for ev in cf.evidence:
                    if ev.ledger_entry_id in valid_ledger_ids:
                        target_ids.add(ev.ledger_entry_id)
            for af in state.analytics_findings:
                for ev in af.evidence:
                    if ev.ledger_entry_id in valid_ledger_ids:
                        target_ids.add(ev.ledger_entry_id)
            for ef in state.engineering_findings:
                for ev in ef.evidence:
                    if ev.ledger_entry_id in valid_ledger_ids:
                        target_ids.add(ev.ledger_entry_id)

        # Fall back to complete ledger only if still empty
        if not target_ids:
            target_ids = set(valid_ledger_ids)

        return target_ids

    def _build_compact_revision_context(
        self,
        state: InvestigationState,
        target_evidence_ids: set[str],
    ) -> str:
        """Format targeted working set for PM revision without context explosion."""
        parts: list[str] = [
            f"INVESTIGATION QUERY: {state.user_query}",
            f"INVESTIGATION ID: {state.investigation_id}",
            "",
            "=== AUTHORITATIVE APPEND-ONLY EVIDENCE LEDGER (TARGETED WORKING SET) ===",
        ]
        for entry_id in sorted(target_evidence_ids):
            entry = state.evidence_ledger_entries.get(entry_id)
            if entry:
                parts.append(
                    f"[{entry_id}] ({entry.source_type}) ref={entry.source_reference}\n"
                    f"  summary: {entry.data_summary}"
                )

        parts.append("\n=== RELEVANT SPECIALIST FINDINGS SUMMARY ===")
        for cf in state.customer_findings:
            ev_ids = [
                e.ledger_entry_id for e in cf.evidence if e.ledger_entry_id in target_evidence_ids
            ]
            if ev_ids or not target_evidence_ids:
                parts.append(
                    f"- Customer Finding: {cf.finding} (pattern: {cf.observed_pattern}, ev: {ev_ids})"
                )
        for af in state.analytics_findings:
            ev_ids = [
                e.ledger_entry_id for e in af.evidence if e.ledger_entry_id in target_evidence_ids
            ]
            if ev_ids or not target_evidence_ids:
                parts.append(
                    f"- Analytics Finding: {af.finding} ({af.metric}={af.value}, ev: {ev_ids})"
                )
        for ef in state.engineering_findings:
            ev_ids = [
                e.ledger_entry_id for e in ef.evidence if e.ledger_entry_id in target_evidence_ids
            ]
            if ev_ids or not target_evidence_ids:
                parts.append(
                    f"- Engineering Finding: {ef.finding} (status: {ef.issue_status}, ev: {ev_ids})"
                )

        parts.append("\n=== KNOWN LIMITATIONS & TOOL ERRORS ===")
        if state.limitations:
            for lim in state.limitations:
                parts.append(f"- Limitation: {lim}")
        if state.tool_errors:
            for err in state.tool_errors:
                src = err.attempted_source or "unknown_source"
                parts.append(f"- Tool Error ({src}, type={err.error_type}): {err.message}")
        if not state.limitations and not state.tool_errors:
            parts.append("(None)")

        if state.assessment and not state.assessment.sufficient_for_synthesis:
            parts.append("\n=== EVIDENTIARY GAPS & LIMITATIONS FROM ASSESSMENT ===")
            parts.append(
                "Assessment determined evidence is incomplete/insufficient for definitive synthesis."
            )
            if state.assessment.identified_gaps:
                parts.append("Identified Gaps:")
                for gap in state.assessment.identified_gaps:
                    parts.append(f"  - {gap}")
            if state.assessment.recommended_questions:
                parts.append("Unanswered Questions / Diagnostic Gaps:")
                for uq in state.assessment.recommended_questions:
                    parts.append(f"  - {uq}")
            parts.append(
                "MANDATORY INSTRUCTION: You must explicitly preserve these gaps, unanswered questions, and limitations "
                "in your recommendation's open_questions and risks fields. DO NOT present missing or unretrieved evidence as established fact."
            )

        return "\n".join(parts)

    async def synthesize(
        self, state: InvestigationState
    ) -> tuple[ProductRecommendation | None, int]:
        """Synthesize initial ProductRecommendation with bounded repair loop.

        Returns:
            (recommendation, llm_calls_made)
            recommendation is None if repair loop fails (safe PM fallback without hallucination).
        """
        evidence_context = self._build_evidence_context(state)
        messages: list[LLMMessage] = [
            LLMMessage(
                role="system",
                content=PM_SYNTHESIS_SYSTEM_PROMPT + "\n" + PM_REPORT_SHAPING_GUIDANCE,
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Synthesize the following investigation evidence into a structured ProductRecommendation.\n\n"
                    f"{evidence_context}"
                ),
            ),
        ]

        repair_attempts = 0
        calls_made = 0
        recommendation: ProductRecommendation | None = None

        while repair_attempts <= 2:
            try:
                recommendation = await self.llm.complete_structured(
                    messages=messages,
                    model=self.model_name,
                    response_model=ProductRecommendation,
                    temperature=0.0,
                    role="pm",
                )
                if not isinstance(recommendation, ProductRecommendation):
                    raise TypeError(
                        "PM synthesis returned a response that does not satisfy the ProductRecommendation contract."
                    )
                calls_made += 1
                break
            except Exception as exc:
                calls_made += 1
                repair_attempts += 1
                logger.warning("PM synthesis failed (attempt %d/3): %s", calls_made, exc)
                if repair_attempts <= 2:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                f"SCHEMA / VALIDATION ERROR:\n{str(exc)}\n\n"
                                f"Please repair your synthesis to strictly satisfy all schema requirements, "
                                f"ensuring all evidence references cite valid ledger entry IDs."
                            ),
                        )
                    )

        return recommendation, calls_made

    async def revise(
        self,
        state: InvestigationState,
        previous_recommendation: ProductRecommendation,
        review: CriticReview,
    ) -> tuple[ProductRecommendation | None, int]:
        """Revise ProductRecommendation based on CriticReview feedback with targeted evidence selection.

        Returns:
            (revised_recommendation, llm_calls_made)
        """
        target_ids = self._collect_revision_evidence_ids(state, previous_recommendation, review)
        evidence_context = self._build_compact_revision_context(state, target_ids)
        critic_issues_text = "\n".join(
            f"- [{issue.category}] Claim: '{issue.claim}' | Problem: {issue.problem} "
            f"(supporting_ledger_ids={issue.supporting_ledger_entry_ids}, required_change: {issue.required_change})"
            for issue in review.issues
        )
        required_changes_text = "\n".join(f"- {chg}" for chg in review.required_changes)

        messages: list[LLMMessage] = [
            LLMMessage(
                role="system",
                content=PM_REVISION_SYSTEM_PROMPT + "\n" + PM_REPORT_SHAPING_GUIDANCE,
            ),
            LLMMessage(
                role="user",
                content=(
                    f"EVIDENCE WORKING SET (TARGETED LEDGER ENTRIES):\n{evidence_context}\n\n"
                    f"PREVIOUS CANDIDATE RECOMMENDATION:\n"
                    f"{previous_recommendation.model_dump_json(indent=2)}\n\n"
                    f"CRITIC REVIEW (Decision: {review.decision}):\n"
                    f"ISSUES IDENTIFIED:\n{critic_issues_text}\n\n"
                    f"REQUIRED CHANGES:\n{required_changes_text}\n\n"
                    f"Revise the ProductRecommendation addressing all Critic issues completely. "
                    f"Ensure observed facts cite valid ledger IDs and causal claims remain conservative."
                ),
            ),
        ]

        repair_attempts = 0
        calls_made = 0
        revised_recommendation: ProductRecommendation | None = None

        while repair_attempts <= 2:
            try:
                revised_recommendation = await self.llm.complete_structured(
                    messages=messages,
                    model=self.revision_model_name,
                    response_model=ProductRecommendation,
                    temperature=0.0,
                    role="pm_revision",
                )
                calls_made += 1
                break
            except Exception as exc:
                calls_made += 1
                repair_attempts += 1
                logger.warning("PM revision failed (attempt %d/3): %s", calls_made, exc)
                if repair_attempts <= 2:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                f"SCHEMA / VALIDATION ERROR:\n{str(exc)}\n\n"
                                f"Please repair your revised recommendation to satisfy all schema requirements, "
                                f"resolving the critic issues and citing only valid ledger entries."
                            ),
                        )
                    )

        return revised_recommendation, calls_made
