"""Ground-truth schemas for Phase 9 evaluations."""

from typing import Literal

from app.domain.recommendation import RecommendationConfidence
from pydantic import BaseModel, ConfigDict, Field

EvaluationRecommendationType = Literal[
    "prioritise",
    "investigate_further",
    "experiment",
    "technical_remediation",
    "monitor",
    "deprioritise",
    "feature_fix",
    "workflow_change",
    "instrumentation",
    "policy_change",
    "no_action",
]

ScenarioSplit = Literal["dev", "val", "holdout"]
SourceDomain = Literal["zendesk", "posthog", "jira"]


class ExpectedEvidenceRecord(BaseModel):
    """Specific expected evidence record from support or engineering."""

    model_config = ConfigDict(frozen=True)
    source_type: SourceDomain
    source_reference: str
    expected_content_keywords: list[str] = Field(default_factory=list)
    is_mandatory: bool = True


class ExpectedAnalyticsObservation(BaseModel):
    """Canonical ground-truth analytics observation for deduplicated evaluation."""

    model_config = ConfigDict(frozen=True)
    obs_id: str  # e.g. "analytics:obs_transfer_pending_latency"
    metric: str  # e.g. "funnel_latency"
    event_filter: str  # e.g. "transfer_initiated -> transfer_completed"
    breakdown_segment: str  # e.g. "bank_code in ['Bank A', 'Bank B']"
    time_window: str  # e.g. "last_7_days"
    expected_observation: str  # e.g. "p95 latency > 45s, completion rate stable at 98.8%"
    is_mandatory: bool = True


class EvaluationScenario(BaseModel):
    """Strict ground-truth scenario model isolated from runtime agent state."""

    model_config = ConfigDict(frozen=True)
    scenario_id: str
    name: str
    version: str = "1.0"
    split: ScenarioSplit
    archetype: str
    product_area: str
    user_query: str

    # Ground Truth Expectations
    required_sources: list[SourceDomain]
    expected_support_tickets: list[str] = Field(default_factory=list)
    expected_jira_issues: list[str] = Field(default_factory=list)
    expected_analytics_observations: list[ExpectedAnalyticsObservation] = Field(
        default_factory=list
    )
    expected_findings: list[str] = Field(..., min_length=1)
    distractor_facts: list[str] = Field(default_factory=list)
    expected_contradictions: list[str] = Field(default_factory=list)
    causal_boundaries: list[str] = Field(default_factory=list)
    expected_affected_segments: list[str] = Field(default_factory=list)
    acceptable_recommendation_types: list[EvaluationRecommendationType]
    acceptable_conclusions: list[str] = Field(..., min_length=1)
    unacceptable_conclusions: list[str] = Field(..., min_length=1)
    expected_confidence_range: tuple[RecommendationConfidence, RecommendationConfidence]
    expected_open_questions: list[str] = Field(default_factory=list)

    # Failure / Safe Handling Expectations
    expected_failure_status: Literal["completed", "partial", "failed"] | None = None
    expected_disclosed_limitations: list[str] = Field(default_factory=list)

    # Explicit Quota Tags for Balanced 45-Scenario Verification
    has_contradiction: bool = False
    is_causal_trap: bool = False
    is_critic_true_positive: bool = False
    is_critic_true_negative: bool = False
    is_segmentation_trap: bool = False
    is_magnitude_trap: bool = False
    is_source_outage: bool = False
    is_adversarial_injection: bool = False
    is_single_source: bool = False
    is_multi_source: bool = False
    is_missing_evidence: bool = False
