"""Product recommendation domain schemas with epistemic separation and zero Any."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.evidence import Evidence

RecommendationType = Literal[
    "prioritise",
    "investigate_further",
    "experiment",
    "technical_remediation",
    "monitor",
    "deprioritise",
]

RecommendationConfidence = Literal["high", "medium", "low"]


class ProductRecommendation(BaseModel):
    """Authoritative structured product decision artifact synthesized by PM Agent."""

    model_config = ConfigDict(frozen=True)

    problem_statement: str = Field(
        ...,
        description="Concise synthesis of the verified product problem.",
        min_length=10,
    )
    why_it_matters: str = Field(
        ...,
        description="Customer, business, or product impact statement.",
        min_length=10,
    )
    affected_users: str = Field(
        ...,
        description="Specific population, cohort, or transaction segment affected.",
        min_length=5,
    )
    factual_observations: list[str] = Field(
        ...,
        description="Directly observed facts verified by source evidence.",
        min_length=1,
    )
    inferences: list[str] = Field(
        ...,
        description="Reasoned interpretations logically derived from facts.",
        min_length=1,
    )
    hypotheses: list[str] = Field(
        default_factory=list,
        description="Plausible explanations requiring further evidentiary validation.",
    )
    evidence: list[Evidence] = Field(
        ...,
        description="Directly cited evidence items referencing authoritative ledger entry IDs.",
        min_length=1,
    )
    likely_causes: list[str] = Field(
        default_factory=list,
        description="Plausible contributors qualified conservatively ('associated with', 'plausible contributor').",
    )
    conflicting_evidence: list[str] = Field(
        default_factory=list,
        description="Explicitly documented contradictory or divergent evidence across sources.",
    )
    recommendation: str = Field(
        ...,
        description="Defensible, concrete next product decision.",
        min_length=10,
    )
    recommendation_type: RecommendationType = Field(
        ...,
        description="Standardized product action categorization.",
    )
    success_metrics: list[str] = Field(
        ...,
        description="Measurable metrics to evaluate recommendation impact.",
        min_length=1,
    )
    risks: list[str] = Field(
        ...,
        description="Identified risks, false assumptions, or unintended side effects.",
        min_length=1,
    )
    confidence: RecommendationConfidence = Field(
        ...,
        description="Calibrated confidence level proportional to corroboration and data completeness.",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Remaining unknowns or unaddressed diagnostic dimensions.",
    )
