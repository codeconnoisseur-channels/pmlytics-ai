"""Baseline A: Single generalist ReAct agent with direct access to all 8 domain tools."""

import logging
from typing import Any, Literal

from app.agents.ledger import EvidenceLedger
from app.config.settings import get_model_for_role
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.integrations.llm.client import LLMClient, LLMMessage
from app.orchestration.state import GraphBudgetUsage, InvestigationState
from app.tools.base import BaseTool, ToolError
from pydantic import BaseModel, Field

from evaluations.config import MODE1_MATCHED_BUDGET, MODE2_NATURAL_BUDGETS, AblationMode

logger = logging.getLogger(__name__)

SINGLE_AGENT_SYSTEM_PROMPT = """You are a generalist Senior Product Analyst with direct access to Customer Support (Zendesk), Product Analytics (PostHog), and Engineering (Jira) tools.

Your task is to investigate product issues by calling relevant domain tools, recording evidence, and synthesizing a grounded ProductRecommendation.

Available tools:
- search_tickets, get_ticket, get_ticket_comments
- query_analytics
- search_issues, get_issue, get_issue_comments, get_linked_issues

You must not invent ticket IDs, metrics, or issue keys. Every fact in your recommendation must be grounded in actual tool responses.
"""


class SingleAgentAction(BaseModel):
    """Next action taken by the single agent."""

    action_type: str = Field(..., description="'tool_call' or 'finish'")
    tool_name: str | None = None
    tool_input: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""


class SingleAgentBaseline:
    """Baseline A executing a single unspecialized agent with all 8 domain tools."""

    def __init__(
        self,
        llm_client: LLMClient,
        tools: dict[str, BaseTool] | list[BaseTool],
        model_name: str | None = None,
    ) -> None:
        self.llm = llm_client
        if isinstance(tools, list):
            self.tools = {t.name: t for t in tools}
        else:
            self.tools = tools
        self.model_name = model_name or get_model_for_role("pm")

    async def execute(
        self,
        user_query: str,
        investigation_id: str,
        mode: AblationMode = "mode1_matched",
    ) -> InvestigationState:
        """Execute the single generalist agent loop."""
        budget_limit = (
            MODE1_MATCHED_BUDGET if mode == "mode1_matched" else MODE2_NATURAL_BUDGETS["baseline_a"]
        )

        ledger = EvidenceLedger(role="single_agent")
        tool_errors: list[ToolError] = []
        limitations: list[str] = []
        llm_call_count = 0
        tool_call_count = 0

        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=SINGLE_AGENT_SYSTEM_PROMPT),
            LLMMessage(role="user", content=f"Investigate this product issue:\n{user_query}"),
        ]

        # ReAct execution loop
        while (
            llm_call_count < budget_limit.max_llm_calls - 1
            and tool_call_count < budget_limit.max_tool_calls
        ):
            llm_call_count += 1
            try:
                action = await self.llm.complete_structured(
                    messages=messages,
                    response_model=SingleAgentAction,
                    model=self.model_name,
                    temperature=0.0,
                )
            except Exception as e:
                logger.warning("Single agent action parsing error: %s", e)
                break

            if action.action_type == "finish" or not action.tool_name:
                break

            tool_name = action.tool_name
            tool = self.tools.get(tool_name)
            if not tool:
                messages.append(
                    LLMMessage(
                        role="user",
                        content=f"Tool '{tool_name}' does not exist. Choose from: {list(self.tools.keys())}",
                    )
                )
                continue

            tool_call_count += 1
            try:
                from app.agents.base import TOOL_INPUT_SCHEMAS

                schema_cls = TOOL_INPUT_SCHEMAS.get(tool_name)
                input_data = (
                    schema_cls.model_validate(action.tool_input) if schema_cls else BaseModel()
                )
                result = await tool.run(input_data)
                if result.success and result.data is not None:
                    ledger.record_tool_result(result)
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=f"Tool '{tool_name}' result: {result.data}",
                        )
                    )
                else:
                    if result.error:
                        tool_errors.append(result.error)
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=f"Tool '{tool_name}' failed: {result.error.message if result.error else 'Unknown error'}",
                        )
                    )
            except Exception as e:
                logger.warning("Tool execution error in single agent: %s", e)
                messages.append(LLMMessage(role="user", content=f"Tool error: {e}"))

        # Final Synthesis step
        llm_call_count += 1
        evidence_summary = "\n".join(
            f"[{entry.ledger_entry_id}] ({entry.source_type}) {entry.source_reference}: {entry.data_summary}"
            for entry in ledger.entries
        )

        synthesis_prompt: list[LLMMessage] = [
            LLMMessage(
                role="system",
                content="You are a Senior Product Manager synthesizing your findings into a final ProductRecommendation.",
            ),
            LLMMessage(
                role="user",
                content=(
                    f"User Query: {user_query}\n\n"
                    f"Evidence Retrieved:\n{evidence_summary if evidence_summary else '(None)'}\n\n"
                    f"Generate a grounded ProductRecommendation."
                ),
            ),
        ]

        recommendation: ProductRecommendation | None = None
        try:
            raw_rec = await self.llm.complete_structured(
                messages=synthesis_prompt,
                response_model=ProductRecommendation,
                model=self.model_name,
                temperature=0.0,
            )
            # Link citations to actual ledger IDs where possible
            valid_cites: list[Evidence] = []
            for entry in ledger.entries:
                valid_cites.append(
                    Evidence(
                        ledger_entry_id=entry.ledger_entry_id,
                        source_type=entry.source_type,
                        source_reference=entry.source_reference,
                        finding=entry.data_summary,
                        support=entry.data_summary,
                        confidence=EvidenceConfidence.HIGH,
                    )
                )
            if valid_cites:
                recommendation = raw_rec.model_copy(update={"evidence": valid_cites})
            else:
                recommendation = raw_rec
        except Exception as e:
            logger.warning("Single agent final synthesis failed: %s", e)
            limitations.append("Failed to synthesize valid ProductRecommendation schema.")

        status: Literal["completed", "partial", "failed"] = (
            "completed"
            if recommendation and not tool_errors
            else ("partial" if recommendation else "failed")
        )

        return InvestigationState(
            investigation_id=investigation_id,
            user_query=user_query,
            status=status,
            sufficient_for_synthesis=bool(recommendation),
            evidence_ledger_entries={e.ledger_entry_id: e for e in ledger.entries},
            recommendation=recommendation,
            tool_errors=tool_errors,
            limitations=limitations,
            budget_usage=GraphBudgetUsage(
                planner_llm_calls=0,
                research_tool_calls=tool_call_count,
                analytics_tool_calls=0,
                engineering_tool_calls=0,
                research_llm_calls=0,
                analytics_llm_calls=0,
                engineering_llm_calls=0,
                assessment_llm_calls=0,
                pm_llm_calls=llm_call_count,
                critic_llm_calls=0,
            ),
        )
