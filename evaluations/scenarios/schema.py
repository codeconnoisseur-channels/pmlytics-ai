"""Evaluation ground-truth schema for Pocket product investigation scenarios."""

from typing import Literal

from pydantic import BaseModel, Field

RecommendationType = Literal[
    "prioritise",
    "investigate_further",
    "experiment",
    "technical_remediation",
    "monitor",
    "deprioritise",
]


class ScenarioGroundTruth(BaseModel):
    """Hidden ground-truth definition used exclusively by evaluation runners."""

    scenario_id: str
    name: str
    product_area: str
    underlying_reality: str
    required_evidence_sources: list[Literal["zendesk", "posthog", "jira"]]
    expected_findings: list[str] = Field(..., min_length=1)
    contradictory_evidence: list[str] = Field(default_factory=list)
    known_traps: list[str] = Field(default_factory=list)
    acceptable_conclusions: list[str] = Field(..., min_length=1)
    unacceptable_conclusions: list[str] = Field(..., min_length=1)
    expected_recommendation_type: RecommendationType
    expected_product_interpretation: str
