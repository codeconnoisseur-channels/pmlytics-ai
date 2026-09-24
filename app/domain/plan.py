"""Domain models for investigation planning and task assignment."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SPECIALIST_SOURCE_MAP: dict[str, str] = {
    "research": "zendesk",
    "analytics": "posthog",
    "engineering": "jira",
}

SOURCE_SPECIALIST_MAP: dict[str, str] = {
    "zendesk": "research",
    "posthog": "analytics",
    "jira": "engineering",
}


class InvestigationTask(BaseModel):
    """Specific diagnostic investigation task assigned to a specialist agent."""

    model_config = ConfigDict(frozen=True)

    specialist: Literal["research", "analytics", "engineering"] = Field(
        ...,
        description="Target domain specialist role",
    )
    objective: str = Field(
        ...,
        min_length=5,
        description="Concrete domain investigation objective",
    )
    questions: list[str] = Field(
        default_factory=list,
        description="Targeted diagnostic questions to answer with domain evidence",
    )
    priority: Literal["required", "useful"] = Field(
        default="required",
        description="Priority of this task in the investigation",
    )


class InvestigationPlan(BaseModel):
    """Authoritative structured investigation plan formulated by the Planner."""

    model_config = ConfigDict(frozen=True)

    question_type: Literal[
        "diagnostic",
        "behavioural",
        "customer",
        "technical",
        "prioritisation",
        "comparative",
        "other",
    ] = Field(
        ...,
        description="Classification of the incoming product question",
    )
    objectives: list[str] = Field(
        ...,
        min_length=1,
        description="High-level research objectives addressing the user question",
    )
    tasks: list[InvestigationTask] = Field(
        ...,
        min_length=1,
        description="List of domain-specific tasks dispatched to specialist agents",
    )
    required_sources: list[Literal["zendesk", "posthog", "jira"]] = Field(
        ...,
        min_length=1,
        description="Specific external sources required for this investigation",
    )
    success_condition: str = Field(
        ...,
        min_length=5,
        description="Explicit evidentiary criteria required to answer the question",
    )

    @model_validator(mode="after")
    def validate_source_task_consistency(self) -> "InvestigationPlan":
        """Validate bidirectional consistency between required_sources and assigned tasks."""
        assigned_specialists = {task.specialist for task in self.tasks}
        task_mapped_sources = {SPECIALIST_SOURCE_MAP[role] for role in assigned_specialists}

        for source in self.required_sources:
            if source not in task_mapped_sources:
                raise ValueError(
                    f"Required source '{source}' has no corresponding task assigned to its specialist "
                    f"('{SOURCE_SPECIALIST_MAP[source]}')."
                )

        return self
