"""Analytics Agent for behavioral telemetry investigation via PostHog query_analytics."""

from app.agents.base import BaseSpecialistAgent, SpecialistTask
from app.agents.prompts.analytics_prompt import ANALYTICS_AGENT_SYSTEM_PROMPT
from app.config.settings import get_model_for_role
from app.domain.specialists import AnalyticsFinding
from app.integrations.llm.client import LLMClient
from app.tools.registry import RoleBoundToolset


class AnalyticsTask(SpecialistTask):
    """Investigation task specification for the Analytics Agent."""


class AnalyticsAgent(BaseSpecialistAgent[AnalyticsTask, AnalyticsFinding]):
    """Specialist agent investigating product telemetry in PostHog."""

    def __init__(
        self,
        toolset: RoleBoundToolset,
        llm_client: LLMClient,
        model_name: str | None = None,
        tool_call_budget: int = 8,
        llm_call_budget: int = 12,
    ) -> None:
        model = model_name or get_model_for_role("analytics")
        super().__init__(
            role="analytics",
            toolset=toolset,
            llm_client=llm_client,
            model_name=model,
            system_prompt=ANALYTICS_AGENT_SYSTEM_PROMPT,
            finding_type=AnalyticsFinding,
            tool_call_budget=tool_call_budget,
            llm_call_budget=llm_call_budget,
        )
