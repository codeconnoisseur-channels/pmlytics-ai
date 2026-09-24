"""Specialist agent domain finding schemas and output envelopes."""

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.domain.evidence import BaseSpecialistFinding

TFinding = TypeVar("TFinding", bound=BaseSpecialistFinding)


class CustomerFinding(BaseSpecialistFinding):
    """Customer experience finding derived from support tickets."""

    model_config = ConfigDict(frozen=True)

    observed_pattern: str = Field(
        ...,
        min_length=3,
        description="Recurring customer behavior or complaint pattern",
    )
    affected_users: str | None = Field(
        default=None,
        description="Identified user segment or cohort experiencing this pattern",
    )
    frequency_context: str | None = Field(
        default=None,
        description="Contextual frequency of occurrence within retrieved sample",
    )


class AnalyticsFinding(BaseSpecialistFinding):
    """Behavioral metric finding derived from PostHog event telemetry."""

    model_config = ConfigDict(frozen=True)

    metric: str = Field(
        ...,
        min_length=2,
        description="Quantitative metric evaluated (e.g. 'funnel_conversion_rate', 'p95_duration_ms')",
    )
    value: str = Field(
        ...,
        min_length=1,
        description="Observed metric value (e.g. '17.4%', '13,610,000 ms')",
    )
    comparison: str | None = Field(
        default=None,
        description="Baseline comparison value or historical benchmark",
    )
    segment: str | None = Field(
        default=None,
        description="User segment or transaction cohort evaluated",
    )
    time_period: str | None = Field(
        default=None,
        description="Time period or window of observation",
    )


class EngineeringFinding(BaseSpecialistFinding):
    """Technical context finding derived from Jira issues and engineering notes."""

    model_config = ConfigDict(frozen=True)

    issue_status: str | None = Field(
        default=None,
        description="Current workflow status of relevant Jira issue(s)",
    )
    technical_context: str = Field(
        ...,
        min_length=3,
        description="Technical explanation or defect mechanism",
    )
    relationship_to_problem: str = Field(
        ...,
        min_length=3,
        description="Plausible connection between technical behavior and the product question",
    )
    is_active_incident: bool = Field(
        default=False,
        description="Whether this represents an active unresolved defect vs historical context",
    )


class SpecialistResult(BaseModel, Generic[TFinding]):
    """Standardized top-level output container for any specialist agent execution."""

    model_config = ConfigDict(frozen=True)

    agent_role: Literal["research", "analytics", "engineering"] = Field(
        ...,
        description="Role of the specialist agent that performed this investigation",
    )
    findings: list[TFinding] = Field(
        default_factory=list,
        description="Structured domain findings grounded in verified evidence",
    )
    overall_facts: list[str] = Field(
        default_factory=list,
        description="Observed facts verified across the domain investigation",
    )
    overall_interpretations: list[str] = Field(
        default_factory=list,
        description="Domain-level interpretations drawn from observed facts",
    )
    overall_hypotheses: list[str] = Field(
        default_factory=list,
        description="Working hypotheses proposed for cross-domain synthesis",
    )
    contradictions: list[str] = Field(
        default_factory=list,
        description="Conflicting evidence or contradictory signals observed within the domain",
    )
    unanswered_questions: list[str] = Field(
        default_factory=list,
        description="Questions or data gaps that could not be resolved from available data",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Data coverage, sample size, or query constraints of this investigation",
    )
    tool_call_count: int = Field(
        ...,
        ge=0,
        description="Total actual tool invocations executed during this investigation",
    )
    llm_call_count: int = Field(
        ...,
        ge=0,
        description="Total LLM API calls executed during this investigation",
    )
    investigation_complete: bool = Field(
        ...,
        description="Whether the investigation achieved its objective within budget",
    )
