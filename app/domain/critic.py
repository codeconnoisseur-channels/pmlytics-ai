"""Critic domain schemas with provenance-safe references and zero Any."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CriticIssueCategory = Literal[
    "unsupported_claim",
    "causal_overreach",
    "missing_evidence",
    "contradiction",
    "segmentation_gap",
    "magnitude_gap",
    "alternative_explanation",
    "confidence_mismatch",
    "recommendation_mismatch",
]

CriticDecision = Literal["PASS", "REVISE"]


class CriticIssue(BaseModel):
    """Specific vulnerability identified in candidate recommendation with verified evidence provenance."""

    model_config = ConfigDict(frozen=True)

    category: CriticIssueCategory = Field(
        ...,
        description="Standardized critique classification.",
    )
    claim: str = Field(
        ...,
        description="The exact claim or section in the recommendation under challenge.",
        min_length=5,
    )
    problem: str = Field(
        ...,
        description="Detailed description of why the claim is unsupported, overstated, or contradictory.",
        min_length=10,
    )
    supporting_ledger_entry_ids: list[str] = Field(
        default_factory=list,
        description="Authoritative ledger entry IDs from evidence_ledger_entries supporting this critique. Must resolve 1:1 with state.",
    )
    required_change: str = Field(
        ...,
        description="Actionable instruction the PM must follow to resolve this issue.",
        min_length=10,
    )


class CriticReview(BaseModel):
    """Authoritative adversarial evaluation produced by Critic Agent."""

    model_config = ConfigDict(frozen=True)

    decision: CriticDecision = Field(
        ...,
        description="PASS if recommendation is defensible and grounded; REVISE if material flaws exist.",
    )
    issues: list[CriticIssue] = Field(
        default_factory=list,
        description="List of material issues identified (must be non-empty if decision is REVISE).",
    )
    overall_assessment: str = Field(
        ...,
        description="Summary of recommendation strengths, vulnerabilities, and epistemic quality.",
        min_length=10,
    )
    required_changes: list[str] = Field(
        default_factory=list,
        description="Consolidated required revisions for the PM.",
    )
