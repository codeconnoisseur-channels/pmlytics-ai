"""Typed schemas for synthetic scenario data generation."""

from pydantic import BaseModel, Field


class JiraSeedIssue(BaseModel):
    """Seed definition for a Jira issue to inject."""

    key: str = Field(..., pattern=r"^[A-Z]+-[0-9]+$")
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    components: list[str] = Field(default_factory=list)
    comments: list[str] = Field(default_factory=list)


class InjectionTimeline(BaseModel):
    """Timeline specification establishing chronological ordering of scenario evidence."""

    start_time_iso: str
    end_time_iso: str
    jira_logged_offset_hours: float = Field(
        ...,
        description="Hours from start_time when Jira issue is logged (e.g. 0.0).",
    )
    analytics_degradation_offset_hours: float = Field(
        ...,
        description="Hours from start_time when PostHog metric movement begins.",
    )
    ticket_spike_offset_hours: float = Field(
        ...,
        description="Hours from start_time when customer Zendesk tickets surge.",
    )


class SegmentConstraint(BaseModel):
    """Defines which demographic, banking, or transactional segment is affected."""

    destination_bank: str | None = None
    source_bank: str | None = None
    user_type: str | None = None
    amount_bracket: str | None = None
    amount_brackets: list[str] = Field(default_factory=list)
    category: str | None = None
    app_version: str | None = None


class ScenarioSeedConfig(BaseModel):
    """Configuration governing synthetic generation of scenario-specific evidence."""

    scenario_id: str
    name: str
    target_tickets_count: int = Field(..., gt=0)
    target_events_count: int = Field(..., gt=0)
    jira_issues: list[JiraSeedIssue]
    injection_timeline: InjectionTimeline
    target_segment: SegmentConstraint
    noise_ratio: float = Field(default=0.25, ge=0.0, le=1.0)
