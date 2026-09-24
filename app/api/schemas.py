"""Typed Pydantic schemas for the PMLytics AI API."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.investigation_scope import InvestigationScope


class InvestigationCreateRequest(BaseModel):
    """Payload for launching a new product investigation."""

    model_config = ConfigDict(extra="forbid")

    user_query: str = Field(
        ...,
        description="The product question to investigate. Must be non-empty after trimming.",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional context for the investigation.",
    )
    scope: InvestigationScope = Field(
        default_factory=InvestigationScope,
        description="Optional PM-selected primary and comparison time windows.",
    )

    @field_validator("user_query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("user_query must be non-empty after trimming whitespace.")
        if len(trimmed) > 2000:
            raise ValueError(
                f"user_query length ({len(trimmed)}) exceeds the maximum allowed length of 2000 characters."
            )
        return trimmed


class InvestigationSummaryResponse(BaseModel):
    """Initial acceptance response for an asynchronous investigation."""

    model_config = ConfigDict(frozen=True)

    investigation_id: str
    status: str
    created_at: datetime
    status_url: str
    events_url: str
    result_url: str


class InvestigationRenameRequest(BaseModel):
    """User-managed label for investigation history."""

    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=120)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        trimmed = " ".join(value.split())
        if not trimmed:
            raise ValueError("display_name must be non-empty after trimming whitespace.")
        return trimmed


class InvestigationStatusResponse(BaseModel):
    """Lightweight lifecycle progress summary for an investigation."""

    model_config = ConfigDict(frozen=True)

    investigation_id: str
    user_query: str
    display_name: str | None = None
    status: str
    current_stage: str
    active_agent: str | None
    revision_count: int
    elapsed_seconds: float
    created_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    scope: InvestigationScope = Field(default_factory=InvestigationScope)


class EvidenceSupportingRecordSchema(BaseModel):
    """Sanitized source record supporting an evidence summary."""

    model_config = ConfigDict(frozen=True)

    record_id: str
    record_type: Literal["ticket", "comment", "issue", "metric"]
    source_reference: str
    title: str
    excerpt: str
    status: str | None = None
    occurred_at: datetime | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class EvidenceLedgerItemSchema(BaseModel):
    """Attributable evidence item from the authoritative ledger, scrubbed of credentials and raw payloads."""

    model_config = ConfigDict(frozen=True)

    ledger_entry_id: str
    source_type: Literal["zendesk", "posthog", "jira"]
    source_reference: str
    finding: str
    support_excerpt: str
    confidence: Literal["high", "medium", "low"]
    retrieved_at: datetime
    supporting_records: list[EvidenceSupportingRecordSchema] = Field(default_factory=list)


class StructuredFindingSchema(BaseModel):
    """An individual finding explicitly categorized by epistemic type."""

    model_config = ConfigDict(frozen=True)

    statement: str
    epistemic_type: Literal["fact", "inference", "hypothesis"]
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Authoritative ledger entry IDs directly supporting this statement.",
    )


class StructuredEvidenceCitationSchema(BaseModel):
    """Direct citation embedded in the final recommendation."""

    model_config = ConfigDict(frozen=True)

    ledger_entry_id: str
    source: Literal["zendesk", "posthog", "jira"]
    source_reference: str
    finding: str
    support: str
    confidence: Literal["high", "medium", "low"]


class ProductRecommendationSchema(BaseModel):
    """Full typed synthesis produced by PM and reviewed by Critic."""

    model_config = ConfigDict(frozen=True)

    problem_statement: str
    why_it_matters: str
    affected_users: str
    factual_observations: list[StructuredFindingSchema]
    inferences: list[StructuredFindingSchema]
    hypotheses: list[StructuredFindingSchema]
    recommendation: str
    recommendation_type: str
    confidence: Literal["high", "medium", "low"]
    success_metrics: list[str]
    risks: list[str]
    likely_causes: list[str] = Field(default_factory=list)
    conflicting_evidence: list[str] = Field(default_factory=list)
    disclosed_limitations: list[str] = Field(default_factory=list)
    evidence_citations: list[StructuredEvidenceCitationSchema] = Field(default_factory=list)


class CriticReviewSchema(BaseModel):
    """Outcome of adversarial review and revision tracking."""

    model_config = ConfigDict(frozen=True)

    status: Literal["PASS", "REVISE"]
    revisions_completed: int
    critique_summary: str
    issues_addressed: list[str] = Field(default_factory=list)


class TelemetrySummarySchema(BaseModel):
    """Sanitized telemetry summary capturing token usage and provider cost without leaking secrets."""

    model_config = ConfigDict(frozen=True)

    investigation_id: str
    trace_id: str | None = None
    llm_calls: int = 0
    total_tokens: int = 0
    provider_reported_cost: float | None = None
    internally_estimated_cost: float | None = None


class InvestigationDetailResponse(BaseModel):
    """Complete synthesized investigation result with evidence ledger and telemetry."""

    model_config = ConfigDict(frozen=True)

    investigation_id: str
    user_query: str
    status: str
    duration_seconds: float
    scope: InvestigationScope = Field(default_factory=InvestigationScope)
    recommendation: ProductRecommendationSchema
    evidence_ledger: dict[str, EvidenceLedgerItemSchema]
    critic_review: CriticReviewSchema
    telemetry_summary: TelemetrySummarySchema


class HealthResponse(BaseModel):
    """Sanitized system health status."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok", "degraded"]
    process: str = "healthy"
    investigation_service_initialized: bool
    active_investigations_count: int
    dependencies: dict[str, bool]


class ErrorResponse(BaseModel):
    """Standardized API error contract."""

    model_config = ConfigDict(frozen=True)

    error_code: str
    message: str
    details: dict[str, Any] | None = None
