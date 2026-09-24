"""Baseline B: Specialist agents + PM synthesis without Critic review."""

import logging
from typing import Any

from app.agents.analytics import AnalyticsAgent
from app.agents.engineering import EngineeringAgent
from app.agents.research import ResearchAgent
from app.integrations.llm.client import LLMClient
from app.orchestration.graph import fan_out_to_specialists
from app.orchestration.nodes.assessment import AssessmentNode
from app.orchestration.nodes.finalize import finalize_investigation_node
from app.orchestration.nodes.follow_up import TargetedFollowUpNode
from app.orchestration.nodes.planner import PlannerNode
from app.orchestration.nodes.pm_synthesis import PMSynthesisNode
from app.orchestration.nodes.router import evaluate_follow_up_edge
from app.orchestration.nodes.specialists import AnalyticsNode, EngineeringNode, ResearchNode
from app.orchestration.state import InvestigationState
from langgraph.graph import END, START, StateGraph

from evaluations.config import AblationMode

logger = logging.getLogger(__name__)


def create_specialist_no_critic_graph(
    llm_client: LLMClient,
    research_agent: ResearchAgent,
    analytics_agent: AnalyticsAgent,
    engineering_agent: EngineeringAgent,
    planner_model: str | None = None,
    assessment_model: str | None = None,
    pm_model: str | None = None,
) -> Any:
    """Compile StateGraph with specialists and PM synthesis, directly bypassing Critic."""
    builder = StateGraph(InvestigationState)

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

    builder.add_node("planner", planner_worker)
    builder.add_node("research", research_worker)
    builder.add_node("analytics", analytics_worker)
    builder.add_node("engineering", engineering_worker)
    builder.add_node("assessment", assessment_worker)
    builder.add_node("targeted_follow_up", follow_up_worker)
    builder.add_node("pm_synthesis", pm_synthesis_worker)
    builder.add_node("finalize", finalize_investigation_node)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner",
        fan_out_to_specialists,
        ["research", "analytics", "engineering"],
    )

    builder.add_edge("research", "assessment")
    builder.add_edge("analytics", "assessment")
    builder.add_edge("engineering", "assessment")

    builder.add_conditional_edges(
        "assessment",
        evaluate_follow_up_edge,
        {
            "targeted_follow_up": "targeted_follow_up",
            "pm_synthesis": "pm_synthesis",
            "finalize": "finalize",
        },
    )

    builder.add_edge("targeted_follow_up", "assessment")

    # In Baseline B, PM synthesis routes directly to finalize (No Critic)
    builder.add_edge("pm_synthesis", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()


class SpecialistNoCriticBaseline:
    """Baseline B orchestrator executing specialists + PM without Critic."""

    def __init__(
        self,
        llm_client: LLMClient,
        research_agent: ResearchAgent,
        analytics_agent: AnalyticsAgent,
        engineering_agent: EngineeringAgent,
        model_name: str | None = None,
    ) -> None:
        self.graph = create_specialist_no_critic_graph(
            llm_client=llm_client,
            research_agent=research_agent,
            analytics_agent=analytics_agent,
            engineering_agent=engineering_agent,
            planner_model=model_name,
            assessment_model=model_name,
            pm_model=model_name,
        )

    async def execute(
        self,
        user_query: str,
        investigation_id: str,
        mode: AblationMode = "mode1_matched",
    ) -> InvestigationState:
        """Execute Baseline B pipeline."""
        initial_state = InvestigationState(
            investigation_id=investigation_id,
            user_query=user_query,
        )

        final_dict = await self.graph.ainvoke(initial_state)
        return InvestigationState.model_validate(final_dict)
