"""LangGraph assembly coordinating multi-agent product discovery investigations."""

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.agents.analytics import AnalyticsAgent
from app.agents.engineering import EngineeringAgent
from app.agents.research import ResearchAgent
from app.domain.plan import SOURCE_SPECIALIST_MAP
from app.integrations.llm.client import LLMClient
from app.orchestration.nodes.assessment import AssessmentNode
from app.orchestration.nodes.critic_node import CriticNode
from app.orchestration.nodes.finalize import finalize_investigation_node
from app.orchestration.nodes.follow_up import TargetedFollowUpNode
from app.orchestration.nodes.planner import PlannerNode
from app.orchestration.nodes.pm_revision import PMRevisionNode
from app.orchestration.nodes.pm_synthesis import PMSynthesisNode
from app.orchestration.nodes.router import (
    evaluate_critic_edge,
    evaluate_follow_up_edge,
    evaluate_pm_revision_edge,
    evaluate_pm_synthesis_edge,
)
from app.orchestration.nodes.specialists import AnalyticsNode, EngineeringNode, ResearchNode
from app.orchestration.state import InvestigationState


def fan_out_to_specialists(state: InvestigationState) -> list[str]:
    """Conditional fan-out determining which specialists execute concurrently in Round 0."""
    if not state.plan or not state.plan.required_sources:
        return ["research", "analytics", "engineering"]

    targets: list[str] = []
    for source in state.plan.required_sources:
        role = SOURCE_SPECIALIST_MAP.get(source)
        if role and role not in targets:
            targets.append(role)

    return targets if targets else ["research", "analytics", "engineering"]


def create_investigation_graph(
    llm_client: LLMClient,
    research_agent: ResearchAgent,
    analytics_agent: AnalyticsAgent,
    engineering_agent: EngineeringAgent,
    planner_model: str | None = None,
    assessment_model: str | None = None,
    pm_model: str | None = None,
    pm_revision_model: str | None = None,
    critic_model: str | None = None,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> Any:
    """Build and compile the authoritative LangGraph StateGraph with Phase 8 PM & Critic loop."""
    builder = StateGraph(InvestigationState)

    # Instantiate node workers
    planner_worker = PlannerNode(llm_client, model_name=planner_model)
    research_worker = ResearchNode(research_agent)
    analytics_worker = AnalyticsNode(analytics_agent)
    engineering_worker = EngineeringNode(engineering_agent)
    assessment_worker = AssessmentNode(llm_client, model_name=assessment_model)
    follow_up_worker = TargetedFollowUpNode(
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
    )
    pm_synthesis_worker = PMSynthesisNode(llm_client, model_name=pm_model)
    critic_worker = CriticNode(llm_client, model_name=critic_model)
    pm_revision_worker = PMRevisionNode(llm_client, model_name=pm_revision_model or pm_model)

    # Register nodes
    builder.add_node("planner", planner_worker)
    builder.add_node("research", research_worker)
    builder.add_node("analytics", analytics_worker)
    builder.add_node("engineering", engineering_worker)
    builder.add_node("assessment", assessment_worker)
    builder.add_node("targeted_follow_up", follow_up_worker)
    builder.add_node("pm_synthesis", pm_synthesis_worker)
    builder.add_node("critic", critic_worker)
    builder.add_node("pm_revision", pm_revision_worker)
    builder.add_node("finalize", finalize_investigation_node)

    # Edges
    builder.add_edge(START, "planner")

    # Native parallel fan-out from planner to active specialists
    builder.add_conditional_edges(
        "planner",
        fan_out_to_specialists,
        ["research", "analytics", "engineering"],
    )

    # Fan-in join barrier from specialists to assessment
    builder.add_edge("research", "assessment")
    builder.add_edge("analytics", "assessment")
    builder.add_edge("engineering", "assessment")

    # Conditional edge from assessment to either follow-up or PM synthesis (or finalize if no usable evidence)
    builder.add_conditional_edges(
        "assessment",
        evaluate_follow_up_edge,
        {
            "targeted_follow_up": "targeted_follow_up",
            "pm_synthesis": "pm_synthesis",
            "finalize": "finalize",
        },
    )

    # Re-assess after follow-up (second pass evaluates round 1 evidence)
    builder.add_edge("targeted_follow_up", "assessment")

    # Conditional edge from pm_synthesis to critic or finalize
    builder.add_conditional_edges(
        "pm_synthesis",
        evaluate_pm_synthesis_edge,
        {
            "critic": "critic",
            "finalize": "finalize",
        },
    )

    # Conditional edge from critic to finalize (if PASS or max revisions) or pm_revision
    builder.add_conditional_edges(
        "critic",
        evaluate_critic_edge,
        {
            "finalize": "finalize",
            "pm_revision": "pm_revision",
        },
    )

    # Every revised candidate returns to the Critic before it can be finalized.
    builder.add_conditional_edges(
        "pm_revision",
        evaluate_pm_revision_edge,
        {
            "finalize": "finalize",
            "critic": "critic",
        },
    )

    # Terminate after finalize
    builder.add_edge("finalize", END)

    return builder.compile(checkpointer=checkpointer)
