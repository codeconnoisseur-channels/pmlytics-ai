"""Planner node formulating investigation plans with strictly bounded repair loops."""

import logging

from app.config.settings import get_model_for_role
from app.domain.plan import InvestigationPlan
from app.integrations.llm.client import LLMClient, LLMMessage
from app.integrations.observability.tracer import async_span_context
from app.orchestration.prompts import PLANNER_SYSTEM_PROMPT
from app.orchestration.state import (
    GraphBudgetUsage,
    InvestigationState,
    InvestigationStateUpdate,
)
from app.tools.base import ToolError

logger = logging.getLogger(__name__)


class PlannerNode:
    """Orchestration node responsible for formulating investigation plans."""

    def __init__(self, llm_client: LLMClient, model_name: str | None = None) -> None:
        self.llm = llm_client
        self.model_name = model_name or get_model_for_role("planner")

    async def __call__(self, state: InvestigationState) -> InvestigationStateUpdate:
        """Execute plan formulation with at most 2 repair attempts (max 3 LLM calls)."""
        async with async_span_context(
            "planner", run_type="chain", inputs={"user_query": state.user_query}
        ):
            return await self._execute_plan(state)

    async def _execute_plan(self, state: InvestigationState) -> InvestigationStateUpdate:
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=PLANNER_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=(
                    f"USER PRODUCT QUESTION:\n"
                    f"{state.user_query}\n\n"
                    f"TIME SCOPE:\n{state.scope.describe()}\n\n"
                    f"Formulate a structured InvestigationPlan assigning concrete tasks to relevant specialists."
                ),
            ),
        ]

        repair_attempts = 0
        calls_made = 0
        plan: InvestigationPlan | None = None
        last_error_msg = ""

        while repair_attempts <= 2:
            try:
                plan = await self.llm.complete_structured(
                    messages=messages,
                    model=self.model_name,
                    response_model=InvestigationPlan,
                    temperature=0.0,
                    role="planner",
                )
                calls_made += 1
                break
            except Exception as exc:
                calls_made += 1
                repair_attempts += 1
                last_error_msg = str(exc)
                logger.warning(
                    "Planner structured generation failed (attempt %d/3): %s",
                    calls_made,
                    exc,
                )
                if repair_attempts <= 2:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                f"SCHEMA VALIDATION ERROR:\n{str(exc)}\n\n"
                                f"Please repair the plan to satisfy all schema requirements, ensuring "
                                f"every required_source has a corresponding specialist task assigned."
                            ),
                        )
                    )

        if plan is None:
            logger.error("Planner failed after %d attempts; emitting fallback plan", calls_made)
            # Create deterministic fallback plan targeting all three domains to avoid total graph stall
            from app.domain.plan import InvestigationTask

            plan = InvestigationPlan(
                question_type="diagnostic",
                objectives=[f"Investigate: {state.user_query}"],
                tasks=[
                    InvestigationTask(
                        specialist="research",
                        objective=f"Search customer support tickets for: {state.user_query}",
                        questions=[state.user_query],
                        priority="required",
                    ),
                    InvestigationTask(
                        specialist="analytics",
                        objective=f"Analyze user metrics and funnels related to: {state.user_query}",
                        questions=[state.user_query],
                        priority="required",
                    ),
                    InvestigationTask(
                        specialist="engineering",
                        objective=f"Inspect engineering issues and bugs related to: {state.user_query}",
                        questions=[state.user_query],
                        priority="required",
                    ),
                ],
                required_sources=["zendesk", "posthog", "jira"],
                success_condition="Collect evidence across customer, behavioral, and engineering domains.",
            )
            fallback_error = ToolError(
                error_type="upstream_error",
                message=f"Planner failed structured generation after {calls_made} calls: {last_error_msg}",
                attempted_source=None,
            )
            return {
                "plan": plan,
                "tool_errors": [fallback_error],
                "limitations": [
                    f"Planner required fallback due to structured output errors: {last_error_msg}"
                ],
                "budget_usage": GraphBudgetUsage(planner_llm_calls=calls_made),
            }

        return {
            "plan": plan,
            "budget_usage": GraphBudgetUsage(planner_llm_calls=calls_made),
        }
