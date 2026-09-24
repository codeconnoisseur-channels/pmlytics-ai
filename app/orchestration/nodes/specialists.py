"""Specialist execution nodes with isolated failure handling and actual counter reporting."""

import logging

from app.agents.analytics import AnalyticsAgent, AnalyticsTask
from app.agents.engineering import EngineeringAgent, EngineeringTask
from app.agents.research import ResearchAgent, ResearchTask
from app.config.settings import get_settings
from app.domain.plan import InvestigationTask
from app.integrations.observability.tracer import async_span_context
from app.orchestration.fingerprint import compute_canonical_task_fingerprint
from app.orchestration.state import (
    GraphBudgetUsage,
    InvestigationState,
    InvestigationStateUpdate,
    SpecialistNodeUpdate,
)
from app.tools.base import ToolError

logger = logging.getLogger(__name__)


def _find_task_for_specialist(
    state: InvestigationState,
    role: str,
) -> InvestigationTask | None:
    """Find the first task assigned to this specialist role in the plan."""
    if not state.plan:
        return None
    for task in state.plan.tasks:
        if task.specialist == role:
            return task
    return None


def to_node_update_dict(update: SpecialistNodeUpdate) -> InvestigationStateUpdate:
    """Convert SpecialistNodeUpdate to a state update dictionary preserving Pydantic models."""
    res: InvestigationStateUpdate = {}
    if update.evidence_ledger_entries:
        res["evidence_ledger_entries"] = update.evidence_ledger_entries
    if update.customer_findings:
        res["customer_findings"] = update.customer_findings
    if update.analytics_findings:
        res["analytics_findings"] = update.analytics_findings
    if update.engineering_findings:
        res["engineering_findings"] = update.engineering_findings
    if update.tool_errors:
        res["tool_errors"] = update.tool_errors
    if update.limitations:
        res["limitations"] = update.limitations
    if update.executed_task_fingerprints:
        res["executed_task_fingerprints"] = update.executed_task_fingerprints
    if update.specialist_completions:
        res["specialist_completions"] = update.specialist_completions
    res["budget_usage"] = update.budget_usage
    return res


class ResearchNode:
    """Orchestration node coordinating the Research Agent (Zendesk)."""

    def __init__(self, agent: ResearchAgent) -> None:
        self.agent = agent

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        task_def = _find_task_for_specialist(state, "research")
        if task_def is None:
            logger.info("ResearchNode skipped: no research task assigned in plan")
            return to_node_update_dict(SpecialistNodeUpdate())

        cfg = get_settings()
        research_task = ResearchTask(
            user_question=state.user_query,
            objective=task_def.objective,
            specific_questions=task_def.questions,
            scope=state.scope,
            llm_call_budget=3 if cfg.investigation_profile == "standard" else None,
        )
        fp = compute_canonical_task_fingerprint(
            "research",
            task_def.objective,
            task_def.questions,
        )

        try:
            async with async_span_context(
                "research_agent", run_type="chain", inputs={"objective": task_def.objective}
            ):
                result = await self.agent.execute(
                    research_task,
                    round_index=state.round_index,
                    llm_budget_override=research_task.llm_call_budget,
                )
            entries_map = {e.ledger_entry_id: e for e in self.agent.ledger.entries}
            update = SpecialistNodeUpdate(
                evidence_ledger_entries=entries_map,
                customer_findings=result.findings,
                tool_errors=list(self.agent.ledger.failed_tool_attempts),
                limitations=result.limitations,
                executed_task_fingerprints={fp},
                specialist_completions={"research": result.investigation_complete},
                budget_usage=GraphBudgetUsage(
                    research_tool_calls=self.agent.tool_call_count,
                    research_llm_calls=self.agent.llm_call_count,
                ),
            )
            return to_node_update_dict(update)

        except Exception as exc:
            logger.exception("ResearchNode execution failure: %s", exc)
            err = ToolError(
                error_type="upstream_error",
                message=f"Research specialist failed during execution: {str(exc)}",
                attempted_source="zendesk",
            )
            update = SpecialistNodeUpdate(
                tool_errors=[err],
                limitations=[
                    f"Research specialist crashed ({type(exc).__name__}): {str(exc)}. "
                    "Customer support context is unavailable."
                ],
                executed_task_fingerprints={fp},
                specialist_completions={"research": False},
                budget_usage=GraphBudgetUsage(
                    research_tool_calls=self.agent.tool_call_count,
                    research_llm_calls=self.agent.llm_call_count,
                ),
            )
            return to_node_update_dict(update)


class AnalyticsNode:
    """Orchestration node coordinating the Analytics Agent (PostHog)."""

    def __init__(self, agent: AnalyticsAgent) -> None:
        self.agent = agent

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        task_def = _find_task_for_specialist(state, "analytics")
        if task_def is None:
            logger.info("AnalyticsNode skipped: no analytics task assigned in plan")
            return to_node_update_dict(SpecialistNodeUpdate())

        cfg = get_settings()
        analytics_task = AnalyticsTask(
            user_question=state.user_query,
            objective=task_def.objective,
            specific_questions=task_def.questions,
            scope=state.scope,
            llm_call_budget=3 if cfg.investigation_profile == "standard" else None,
        )
        fp = compute_canonical_task_fingerprint(
            "analytics",
            task_def.objective,
            task_def.questions,
        )

        try:
            async with async_span_context(
                "analytics_agent", run_type="chain", inputs={"objective": task_def.objective}
            ):
                result = await self.agent.execute(
                    analytics_task,
                    round_index=state.round_index,
                    llm_budget_override=analytics_task.llm_call_budget,
                )
            entries_map = {e.ledger_entry_id: e for e in self.agent.ledger.entries}
            update = SpecialistNodeUpdate(
                evidence_ledger_entries=entries_map,
                analytics_findings=result.findings,
                tool_errors=list(self.agent.ledger.failed_tool_attempts),
                limitations=result.limitations,
                executed_task_fingerprints={fp},
                specialist_completions={"analytics": result.investigation_complete},
                budget_usage=GraphBudgetUsage(
                    analytics_tool_calls=self.agent.tool_call_count,
                    analytics_llm_calls=self.agent.llm_call_count,
                ),
            )
            return to_node_update_dict(update)

        except Exception as exc:
            logger.exception("AnalyticsNode execution failure: %s", exc)
            err = ToolError(
                error_type="upstream_error",
                message=f"Analytics specialist failed during execution: {str(exc)}",
                attempted_source="posthog",
            )
            update = SpecialistNodeUpdate(
                tool_errors=[err],
                limitations=[
                    f"Analytics specialist crashed ({type(exc).__name__}): {str(exc)}. "
                    "Product analytics context is unavailable."
                ],
                executed_task_fingerprints={fp},
                specialist_completions={"analytics": False},
                budget_usage=GraphBudgetUsage(
                    analytics_tool_calls=self.agent.tool_call_count,
                    analytics_llm_calls=self.agent.llm_call_count,
                ),
            )
            return to_node_update_dict(update)


class EngineeringNode:
    """Orchestration node coordinating the Engineering Agent (Jira)."""

    def __init__(self, agent: EngineeringAgent) -> None:
        self.agent = agent

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        task_def = _find_task_for_specialist(state, "engineering")
        if task_def is None:
            logger.info("EngineeringNode skipped: no engineering task assigned in plan")
            return to_node_update_dict(SpecialistNodeUpdate())

        cfg = get_settings()
        engineering_task = EngineeringTask(
            user_question=state.user_query,
            objective=task_def.objective,
            specific_questions=task_def.questions,
            scope=state.scope,
            llm_call_budget=3 if cfg.investigation_profile == "standard" else None,
        )
        fp = compute_canonical_task_fingerprint(
            "engineering",
            task_def.objective,
            task_def.questions,
        )

        try:
            async with async_span_context(
                "engineering_agent", run_type="chain", inputs={"objective": task_def.objective}
            ):
                result = await self.agent.execute(
                    engineering_task,
                    round_index=state.round_index,
                    llm_budget_override=engineering_task.llm_call_budget,
                )
            entries_map = {e.ledger_entry_id: e for e in self.agent.ledger.entries}
            update = SpecialistNodeUpdate(
                evidence_ledger_entries=entries_map,
                engineering_findings=result.findings,
                tool_errors=list(self.agent.ledger.failed_tool_attempts),
                limitations=result.limitations,
                executed_task_fingerprints={fp},
                specialist_completions={"engineering": result.investigation_complete},
                budget_usage=GraphBudgetUsage(
                    engineering_tool_calls=self.agent.tool_call_count,
                    engineering_llm_calls=self.agent.llm_call_count,
                ),
            )
            return to_node_update_dict(update)

        except Exception as exc:
            logger.exception("EngineeringNode execution failure: %s", exc)
            err = ToolError(
                error_type="upstream_error",
                message=f"Engineering specialist failed during execution: {str(exc)}",
                attempted_source="jira",
            )
            update = SpecialistNodeUpdate(
                tool_errors=[err],
                limitations=[
                    f"Engineering specialist crashed ({type(exc).__name__}): {str(exc)}. "
                    "Technical engineering context is unavailable."
                ],
                executed_task_fingerprints={fp},
                specialist_completions={"engineering": False},
                budget_usage=GraphBudgetUsage(
                    engineering_tool_calls=self.agent.tool_call_count,
                    engineering_llm_calls=self.agent.llm_call_count,
                ),
            )
            return to_node_update_dict(update)
