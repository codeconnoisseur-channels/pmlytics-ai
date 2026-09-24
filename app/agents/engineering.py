"""Engineering Agent for technical context and defect investigation via Jira tools."""

from app.agents.base import BaseSpecialistAgent, SpecialistTask
from app.agents.prompts.engineering_prompt import ENGINEERING_AGENT_SYSTEM_PROMPT
from app.config.settings import get_model_for_role
from app.domain.specialists import EngineeringFinding
from app.integrations.llm.client import LLMClient
from app.tools.registry import RoleBoundToolset


class EngineeringTask(SpecialistTask):
    """Investigation task specification for the Engineering Agent."""


class EngineeringAgent(BaseSpecialistAgent[EngineeringTask, EngineeringFinding]):
    """Specialist agent investigating technical context and issues in Mock Jira."""

    def __init__(
        self,
        toolset: RoleBoundToolset,
        llm_client: LLMClient,
        model_name: str | None = None,
        tool_call_budget: int = 8,
        llm_call_budget: int = 12,
    ) -> None:
        model = model_name or get_model_for_role("engineering")
        super().__init__(
            role="engineering",
            toolset=toolset,
            llm_client=llm_client,
            model_name=model,
            system_prompt=ENGINEERING_AGENT_SYSTEM_PROMPT,
            finding_type=EngineeringFinding,
            tool_call_budget=tool_call_budget,
            llm_call_budget=llm_call_budget,
        )
