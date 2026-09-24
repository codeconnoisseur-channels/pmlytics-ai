"""Critic Agent evaluating candidate ProductRecommendations against verified evidence."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.agents.prompts.critic_prompt import CRITIC_SYSTEM_PROMPT
from app.config.settings import get_model_for_role
from app.domain.critic import CriticReview
from app.domain.recommendation import ProductRecommendation
from app.integrations.llm.client import LLMClient, LLMMessage

if TYPE_CHECKING:
    from app.orchestration.state import InvestigationState

logger = logging.getLogger(__name__)


class CriticAgent:
    """Critic Agent performing adversarial epistemic reviews of candidate recommendations."""

    def __init__(self, llm_client: LLMClient, model_name: str | None = None) -> None:
        self.llm = llm_client
        self.model_name = model_name or get_model_for_role("critic")

    def _build_review_context(
        self,
        state: InvestigationState,
        candidate_recommendation: ProductRecommendation,
    ) -> str:
        """Format independent context for critic review."""
        valid_ledger_ids = sorted(state.evidence_ledger_entries.keys())
        ledger_text: list[str] = [
            f"VALID AUTHORITATIVE LEDGER ENTRY IDS: {valid_ledger_ids}",
            "",
            "=== AUTHORITATIVE EVIDENCE LEDGER ENTRIES ===",
        ]
        for entry_id, entry in sorted(state.evidence_ledger_entries.items()):
            ledger_text.append(
                f"[{entry_id}] ({entry.source_type}) ref={entry.source_reference}\n"
                f"  summary: {entry.data_summary}"
            )

        findings_text: list[str] = ["\n=== SPECIALIST FINDINGS SUMMARY ==="]
        if state.customer_findings:
            findings_text.append("CUSTOMER (SUPPORT):")
            for cf in state.customer_findings:
                ev_ids = [e.ledger_entry_id for e in cf.evidence]
                findings_text.append(f"- {cf.finding} (ev: {ev_ids})")
        if state.analytics_findings:
            findings_text.append("ANALYTICS (POSTHOG):")
            for af in state.analytics_findings:
                ev_ids = [e.ledger_entry_id for e in af.evidence]
                findings_text.append(f"- {af.metric} ({af.value}): {af.finding} (ev: {ev_ids})")
        if state.engineering_findings:
            findings_text.append("ENGINEERING (JIRA):")
            for ef in state.engineering_findings:
                ev_ids = [e.ledger_entry_id for e in ef.evidence]
                findings_text.append(f"- {ef.finding} (ev: {ev_ids})")

        rec_text = candidate_recommendation.model_dump_json(indent=2)
        joined_ledger = "\n".join(ledger_text)
        joined_findings = "\n".join(findings_text)

        return (
            f"USER QUERY: {state.user_query}\n"
            f"INVESTIGATION SUFFICIENT_FOR_SYNTHESIS: {state.sufficient_for_synthesis}\n\n"
            f"{joined_ledger}\n\n"
            f"{joined_findings}\n\n"
            f"=== CANDIDATE PRODUCT RECOMMENDATION UNDER REVIEW ===\n"
            f"{rec_text}"
        )

    def _validate_critic_review(
        self,
        review: CriticReview,
        state: InvestigationState,
    ) -> None:
        """Validate CriticReview consistency and provenance locally."""
        valid_ids = set(state.evidence_ledger_entries.keys())
        for issue in review.issues:
            for ledger_id in issue.supporting_ledger_entry_ids:
                if ledger_id not in valid_ids:
                    raise ValueError(
                        f"Critic issue '{issue.category}' referenced invalid ledger ID '{ledger_id}'. "
                        f"Allowed IDs: {sorted(valid_ids)}"
                    )

        if not review.issues and review.decision != "PASS":
            raise ValueError(
                f"Inconsistent CriticReview: decision '{review.decision}' but zero issues reported. "
                f"Decision must be 'PASS' when issues list is empty."
            )

        if review.issues and review.decision != "REVISE":
            raise ValueError(
                f"Inconsistent CriticReview: decision '{review.decision}' but {len(review.issues)} "
                f"issues were reported. Decision must be 'REVISE' when issues exist."
            )

    async def review(
        self,
        state: InvestigationState,
        candidate_recommendation: ProductRecommendation,
    ) -> tuple[CriticReview, int]:
        """Perform adversarial review with bounded repair loop (max 3 calls)."""
        review_context = self._build_review_context(state, candidate_recommendation)
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=CRITIC_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=(
                    f"Critique the following candidate recommendation against the verified evidence ledger.\n\n"
                    f"{review_context}"
                ),
            ),
        ]

        repair_attempts = 0
        calls_made = 0
        review: CriticReview | None = None

        while repair_attempts <= 2:
            try:
                calls_made += 1
                candidate = await self.llm.complete_structured(
                    messages=messages,
                    model=self.model_name,
                    response_model=CriticReview,
                    temperature=0.0,
                    role="critic",
                )
                self._validate_critic_review(candidate, state)
                review = candidate
                break
            except Exception as exc:
                repair_attempts += 1
                logger.warning("Critic review failed (attempt %d/3): %s", calls_made, exc)
                if repair_attempts <= 2:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                f"VALIDATION ERROR:\n{str(exc)}\n\n"
                                f"Please repair your CriticReview to satisfy all consistency and provenance rules: "
                                f"only reference valid ledger IDs in supporting_ledger_entry_ids, "
                                f"and ensure decision=='PASS' if issues is empty, or decision=='REVISE' if issues exist."
                            ),
                        )
                    )

        if review is None:
            logger.error(
                "Critic review failed after %d calls; emitting safe conservative REVISE", calls_made
            )
            from app.domain.critic import CriticIssue

            review = CriticReview(
                decision="REVISE",
                issues=[
                    CriticIssue(
                        category="missing_evidence",
                        claim="Candidate recommendation under review",
                        problem="Critic verification could not be completed reliably due to structured generation failure.",
                        supporting_ledger_entry_ids=[],
                        required_change="Verify all evidence claims manually or review investigation limitations.",
                    )
                ],
                overall_assessment="Automated critic review encountered generation error; conservative revision requested.",
                required_changes=[
                    "Disclose that critic verification was incomplete due to review generation error."
                ],
            )

        return review, calls_made
