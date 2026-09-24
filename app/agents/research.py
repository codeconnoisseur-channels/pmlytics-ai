"""Research Agent for customer support evidence investigation via Zendesk tools."""

from app.agents.base import BaseSpecialistAgent, SpecialistTask
from app.agents.prompts.research_prompt import RESEARCH_AGENT_SYSTEM_PROMPT
from app.config.settings import get_model_for_role
from app.domain.specialists import CustomerFinding
from app.integrations.llm.client import LLMClient
from app.tools.registry import RoleBoundToolset


class ResearchTask(SpecialistTask):
    """Investigation task specification for the Research Agent."""


class ResearchAgent(BaseSpecialistAgent[ResearchTask, CustomerFinding]):
    """Specialist agent investigating customer support tickets in Mock Zendesk."""

    def __init__(
        self,
        toolset: RoleBoundToolset,
        llm_client: LLMClient,
        model_name: str | None = None,
        tool_call_budget: int = 10,
        llm_call_budget: int = 15,
    ) -> None:
        model = model_name or get_model_for_role("research")
        super().__init__(
            role="research",
            toolset=toolset,
            llm_client=llm_client,
            model_name=model,
            system_prompt=RESEARCH_AGENT_SYSTEM_PROMPT,
            finding_type=CustomerFinding,
            tool_call_budget=tool_call_budget,
            llm_call_budget=llm_call_budget,
        )
