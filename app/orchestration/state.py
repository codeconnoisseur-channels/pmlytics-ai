"""Strictly typed investigation state schema and reducers with zero Any."""

from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field

from app.agents.ledger import EvidenceLedgerEntry as EvidenceLedgerEntry
from app.domain.critic import CriticReview
from app.domain.investigation_scope import InvestigationScope
from app.domain.plan import InvestigationPlan
from app.domain.recommendation import ProductRecommendation
from app.domain.specialists import AnalyticsFinding, CustomerFinding, EngineeringFinding
from app.tools.base import ToolError

# -----------------------------------------------------------------------------
# Provenance Errors & Reducer Functions (Strictly Typed, Zero Any)
# -----------------------------------------------------------------------------


class ProvenanceValidationError(ValueError):
    """Raised when evidence in graph state violates the tripartite ledger invariant."""


class ProvenanceCollisionError(ProvenanceValidationError):
    """Raised when an incoming evidence entry collides with an existing ledger entry ID."""


def merge_evidence_ledger_entries(
    left: dict[str, EvidenceLedgerEntry],
    right: dict[str, EvidenceLedgerEntry],
) -> dict[str, EvidenceLedgerEntry]:
    """Merges role-scoped ledger entries across parallel branches without collisions.

    Fails closed: raises ProvenanceCollisionError if an incoming entry ID already exists.
    """
    merged = dict(left)
    for entry_id, entry in right.items():
        if entry_id in merged:
            raise ProvenanceCollisionError(
                f"Evidence ledger collision detected for entry ID '{entry_id}'. "
                f"Existing entry from source '{merged[entry_id].source_reference}', "
                f"incoming entry from source '{entry.source_reference}'. Reducer is fail-closed."
            )
        merged[entry_id] = entry
    return merged


def merge_specialist_completions(
    left: dict[str, bool],
    right: dict[str, bool],
) -> dict[str, bool]:
    """Merges specialist completion statuses across parallel branches and rounds."""
    merged = dict(left)
    merged.update(right)
    return merged


def append_customer_findings(
    left: list[CustomerFinding],
    right: list[CustomerFinding],
) -> list[CustomerFinding]:
    return left + right


def append_analytics_findings(
    left: list[AnalyticsFinding],
    right: list[AnalyticsFinding],
) -> list[AnalyticsFinding]:
    return left + right


def append_engineering_findings(
    left: list[EngineeringFinding],
    right: list[EngineeringFinding],
) -> list[EngineeringFinding]:
    return left + right


def append_tool_errors(
    left: list[ToolError],
    right: list[ToolError],
) -> list[ToolError]:
    return left + right


def append_unique_strings(
    left: list[str],
    right: list[str],
) -> list[str]:
    seen = set(left)
    result = list(left)
    for item in right:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def merge_task_fingerprints(
    left: set[str],
    right: set[str],
) -> set[str]:
    return left | right


def append_critic_reviews(
    left: list[CriticReview],
    right: list[CriticReview],
) -> list[CriticReview]:
    """Appends critic review rounds preserving history across revision cycles."""
    return left + right


class GraphBudgetUsage(BaseModel):
    """Accurate ledger of tool and LLM invocations derived directly from actual specialist counters."""

    planner_llm_calls: int = 0
    assessment_llm_calls: int = 0
    research_tool_calls: int = 0
    research_llm_calls: int = 0
    analytics_tool_calls: int = 0
    analytics_llm_calls: int = 0
    engineering_tool_calls: int = 0
    engineering_llm_calls: int = 0
    pm_llm_calls: int = 0
    critic_llm_calls: int = 0

    @property
    def total_tool_calls(self) -> int:
        return self.research_tool_calls + self.analytics_tool_calls + self.engineering_tool_calls

    @property
    def total_llm_calls(self) -> int:
        return (
            self.planner_llm_calls
            + self.assessment_llm_calls
            + self.research_llm_calls
            + self.analytics_llm_calls
            + self.engineering_llm_calls
            + self.pm_llm_calls
            + self.critic_llm_calls
        )


def update_graph_budget(
    left: GraphBudgetUsage,
    right: GraphBudgetUsage | dict[str, int],
) -> GraphBudgetUsage:
    r = right if isinstance(right, GraphBudgetUsage) else GraphBudgetUsage.model_validate(right)
    return GraphBudgetUsage(
        planner_llm_calls=left.planner_llm_calls + r.planner_llm_calls,
        assessment_llm_calls=left.assessment_llm_calls + r.assessment_llm_calls,
        research_tool_calls=left.research_tool_calls + r.research_tool_calls,
        research_llm_calls=left.research_llm_calls + r.research_llm_calls,
        analytics_tool_calls=left.analytics_tool_calls + r.analytics_tool_calls,
        analytics_llm_calls=left.analytics_llm_calls + r.analytics_llm_calls,
        engineering_tool_calls=left.engineering_tool_calls + r.engineering_tool_calls,
        engineering_llm_calls=left.engineering_llm_calls + r.engineering_llm_calls,
        pm_llm_calls=left.pm_llm_calls + r.pm_llm_calls,
        critic_llm_calls=left.critic_llm_calls + r.critic_llm_calls,
    )


class EvidenceAssessment(BaseModel):
    """Structured assessment produced by assessment_node."""

    sufficient_for_synthesis: bool = Field(
        ...,
        description="True ONLY if all primary questions have corroborated evidence with no critical gaps.",
    )
    has_blocking_gaps: bool = Field(
        ...,
        description="True if critical evidentiary questions remain completely unanswered.",
    )
    identified_gaps: list[str] = Field(default_factory=list)
    recommended_specialist: Literal["research", "analytics", "engineering"] | None = None
    recommended_gap: str | None = Field(
        default=None,
        description="The exact gap from identified_gaps that this follow-up addresses.",
    )
    recommended_objective: str | None = None
    recommended_questions: list[str] = Field(default_factory=list)


class InvestigationState(BaseModel):
    """The strictly typed state of the LangGraph investigation."""

    investigation_id: str
    user_query: str
    scope: InvestigationScope = Field(default_factory=InvestigationScope)
    round_index: int = 0
    max_rounds: int = 1
    status: Literal["in_progress", "completed", "partial", "failed"] = "in_progress"
    sufficient_for_synthesis: bool = False

    plan: InvestigationPlan | None = None

    evidence_ledger_entries: Annotated[
        dict[str, EvidenceLedgerEntry],
        merge_evidence_ledger_entries,
    ] = Field(default_factory=dict)

    customer_findings: Annotated[
        list[CustomerFinding],
        append_customer_findings,
    ] = Field(default_factory=list)

    analytics_findings: Annotated[
        list[AnalyticsFinding],
        append_analytics_findings,
    ] = Field(default_factory=list)

    engineering_findings: Annotated[
        list[EngineeringFinding],
        append_engineering_findings,
    ] = Field(default_factory=list)

    tool_errors: Annotated[
        list[ToolError],
        append_tool_errors,
    ] = Field(default_factory=list)

    limitations: Annotated[
        list[str],
        append_unique_strings,
    ] = Field(default_factory=list)

    executed_task_fingerprints: Annotated[
        set[str],
        merge_task_fingerprints,
    ] = Field(default_factory=set)

    specialist_completions: Annotated[
        dict[str, bool],
        merge_specialist_completions,
    ] = Field(default_factory=dict)

    budget_usage: Annotated[
        GraphBudgetUsage,
        update_graph_budget,
    ] = Field(default_factory=GraphBudgetUsage)

    assessment: EvidenceAssessment | None = None
    recommendation: ProductRecommendation | None = None
    critic_reviews: Annotated[
        list[CriticReview],
        append_critic_reviews,
    ] = Field(default_factory=list)
    revision_count: int = 0
    max_revisions: int = 2

    @property
    def pm_revision_count(self) -> int:
        return self.revision_count

    @property
    def errors(self) -> list[ToolError]:
        return self.tool_errors


class SpecialistNodeUpdate(BaseModel):
    """Strongly typed partial state update returned by a specialist node."""

    evidence_ledger_entries: dict[str, EvidenceLedgerEntry] = Field(default_factory=dict)
    customer_findings: list[CustomerFinding] = Field(default_factory=list)
    analytics_findings: list[AnalyticsFinding] = Field(default_factory=list)
    engineering_findings: list[EngineeringFinding] = Field(default_factory=list)
    tool_errors: list[ToolError] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    executed_task_fingerprints: set[str] = Field(default_factory=set)
    specialist_completions: dict[str, bool] = Field(default_factory=dict)
    budget_usage: GraphBudgetUsage = Field(default_factory=GraphBudgetUsage)


class InvestigationStateUpdate(TypedDict, total=False):
    """Strongly typed partial state update dictionary returned by any graph node."""

    investigation_id: str
    user_query: str
    scope: InvestigationScope
    round_index: int
    max_rounds: int
    status: Literal["in_progress", "completed", "partial", "failed"]
    sufficient_for_synthesis: bool
    plan: InvestigationPlan | None
    evidence_ledger_entries: dict[str, EvidenceLedgerEntry]
    customer_findings: list[CustomerFinding]
    analytics_findings: list[AnalyticsFinding]
    engineering_findings: list[EngineeringFinding]
    tool_errors: list[ToolError]
    limitations: list[str]
    executed_task_fingerprints: set[str]
    specialist_completions: dict[str, bool]
    budget_usage: GraphBudgetUsage
    assessment: EvidenceAssessment | None
    recommendation: ProductRecommendation | None
    critic_reviews: list[CriticReview]
    revision_count: int
    max_revisions: int
