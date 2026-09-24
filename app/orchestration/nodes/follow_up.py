"""Targeted follow-up node executing bounded single-specialist investigations."""

import logging
from typing import Literal

from app.agents.analytics import AnalyticsAgent, AnalyticsTask
from app.agents.engineering import EngineeringAgent, EngineeringTask
from app.agents.research import ResearchAgent, ResearchTask
from app.orchestration.fingerprint import compute_canonical_task_fingerprint
from app.orchestration.nodes.router import ROLE_LIMITS
from app.orchestration.nodes.specialists import to_node_update_dict
from app.orchestration.state import (
    GraphBudgetUsage,
    InvestigationState,
    InvestigationStateUpdate,
    SpecialistNodeUpdate,
)
from app.tools.base import ToolError

logger = logging.getLogger(__name__)


class TargetedFollowUpNode:
    """Orchestration node coordinating a single targeted follow-up round."""

    def __init__(
        self,
        research_agent: ResearchAgent,
        analytics_agent: AnalyticsAgent,
        engineering_agent: EngineeringAgent,
    ) -> None:
        self.research = research_agent
        self.analytics = analytics_agent
        self.engineering = engineering_agent

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        assessment = state.assessment
        if not assessment or not assessment.recommended_specialist:
            logger.warning("TargetedFollowUpNode called without valid assessment recommendation")
            return {"round_index": state.round_index + 1}

        role = assessment.recommended_specialist
        objective = (
            assessment.recommended_objective or f"Follow-up on gap: {assessment.recommended_gap}"
        )
        questions = assessment.recommended_questions or []
        fp = compute_canonical_task_fingerprint(role, objective, questions)

        limits = ROLE_LIMITS[role]
        if role == "research":
            used_tools = state.budget_usage.research_tool_calls
            used_llm = state.budget_usage.research_llm_calls
        elif role == "analytics":
            used_tools = state.budget_usage.analytics_tool_calls
            used_llm = state.budget_usage.analytics_llm_calls
        else:
            used_tools = state.budget_usage.engineering_tool_calls
            used_llm = state.budget_usage.engineering_llm_calls

        remaining_tools = max(0, limits["tools"] - used_tools)
        remaining_llm = max(0, limits["llm"] - used_llm)

        logger.info(
            "Executing follow-up for '%s' with remaining budgets: tools=%d, llm=%d",
            role,
            remaining_tools,
            remaining_llm,
        )

        follow_up_round = state.round_index + 1

        try:
            if role == "research":
                task_r = ResearchTask(
                    user_question=state.user_query,
                    objective=objective,
                    specific_questions=questions,
                    scope=state.scope,
                )
                res = await self.research.execute(
                    task_r,
                    round_index=follow_up_round,
                    tool_budget_override=remaining_tools,
                    llm_budget_override=remaining_llm,
                )
                update = SpecialistNodeUpdate(
                    evidence_ledger_entries={
                        e.ledger_entry_id: e for e in self.research.ledger.entries
                    },
                    customer_findings=res.findings,
                    limitations=res.limitations,
                    executed_task_fingerprints={fp},
                    specialist_completions={role: res.investigation_complete},
                    budget_usage=GraphBudgetUsage(
                        research_tool_calls=self.research.tool_call_count,
                        research_llm_calls=self.research.llm_call_count,
                    ),
                )
            elif role == "analytics":
                task_a = AnalyticsTask(
                    user_question=state.user_query,
                    objective=objective,
                    specific_questions=questions,
                    scope=state.scope,
                )
                res_a = await self.analytics.execute(
                    task_a,
                    round_index=follow_up_round,
                    tool_budget_override=remaining_tools,
                    llm_budget_override=remaining_llm,
                )
                update = SpecialistNodeUpdate(
                    evidence_ledger_entries={
                        e.ledger_entry_id: e for e in self.analytics.ledger.entries
                    },
                    analytics_findings=res_a.findings,
                    limitations=res_a.limitations,
                    executed_task_fingerprints={fp},
                    specialist_completions={role: res_a.investigation_complete},
                    budget_usage=GraphBudgetUsage(
                        analytics_tool_calls=self.analytics.tool_call_count,
                        analytics_llm_calls=self.analytics.llm_call_count,
                    ),
                )
            else:
                task_e = EngineeringTask(
                    user_question=state.user_query,
                    objective=objective,
                    specific_questions=questions,
                    scope=state.scope,
                )
                res_e = await self.engineering.execute(
                    task_e,
                    round_index=follow_up_round,
                    tool_budget_override=remaining_tools,
                    llm_budget_override=remaining_llm,
                )
                update = SpecialistNodeUpdate(
                    evidence_ledger_entries={
                        e.ledger_entry_id: e for e in self.engineering.ledger.entries
                    },
                    engineering_findings=res_e.findings,
                    limitations=res_e.limitations,
                    executed_task_fingerprints={fp},
                    specialist_completions={role: res_e.investigation_complete},
                    budget_usage=GraphBudgetUsage(
                        engineering_tool_calls=self.engineering.tool_call_count,
                        engineering_llm_calls=self.engineering.llm_call_count,
                    ),
                )

            data = to_node_update_dict(update)
            data["round_index"] = follow_up_round
            return data

        except Exception as exc:
            logger.exception("Follow-up execution failed for '%s': %s", role, exc)
            source: Literal["zendesk", "posthog", "jira"] | None = (
                "zendesk" if role == "research" else ("posthog" if role == "analytics" else "jira")
            )
            err = ToolError(
                error_type="upstream_error",
                message=f"Follow-up execution failure on '{role}': {str(exc)}",
                attempted_source=source,
            )
            update = SpecialistNodeUpdate(
                tool_errors=[err],
                limitations=[
                    f"Follow-up execution on '{role}' failed ({type(exc).__name__}): {str(exc)}"
                ],
                executed_task_fingerprints={fp},
                specialist_completions={role: False},
            )
            data = to_node_update_dict(update)
            data["round_index"] = follow_up_round
            return data
