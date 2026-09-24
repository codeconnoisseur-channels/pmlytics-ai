"""Base specialist agent execution engine with hard dual budgets and grounded synthesis."""

import json
import logging
import re
from abc import ABC
from typing import Any, Generic, Literal, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field

from app.agents.ledger import EvidenceLedger
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.investigation_scope import InvestigationScope
from app.domain.specialists import SpecialistResult, TFinding
from app.integrations.llm.client import LLMClient, LLMMessage
from app.tools.analytics import QueryAnalyticsInput
from app.tools.base import ToolError, ToolResult
from app.tools.engineering import (
    GetIssueCommentsInput,
    GetIssueInput,
    GetLinkedIssuesInput,
    SearchIssuesInput,
)
from app.tools.registry import RoleBoundToolset
from app.tools.support import (
    GetTicketCommentsInput,
    GetTicketInput,
    SearchTicketsInput,
)

logger = logging.getLogger(__name__)

TOOL_INPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "search_tickets": SearchTicketsInput,
    "get_ticket": GetTicketInput,
    "get_ticket_comments": GetTicketCommentsInput,
    "query_analytics": QueryAnalyticsInput,
    "search_issues": SearchIssuesInput,
    "get_issue": GetIssueInput,
    "get_issue_comments": GetIssueCommentsInput,
    "get_linked_issues": GetLinkedIssuesInput,
}

TTask = TypeVar("TTask", bound="SpecialistTask")


class SpecialistTask(BaseModel):
    """Base input task specification for a specialist agent."""

    model_config = ConfigDict(frozen=True)

    user_question: str = Field(
        ...,
        min_length=3,
        description="The overarching user or product question being investigated",
    )
    objective: str = Field(
        ...,
        min_length=3,
        description="Specific domain investigation objective assigned to this specialist",
    )
    specific_questions: list[str] = Field(
        default_factory=list,
        description="Targeted diagnostic questions to answer with domain evidence",
    )
    scope: InvestigationScope = Field(
        default_factory=InvestigationScope,
        description="PM-selected time boundary to apply when retrieving and interpreting evidence.",
    )
    llm_call_budget: int | None = Field(
        default=None,
        description="Optional profile-specific LLM call budget override",
    )


class EmptyInput(BaseModel):
    """Fallback empty input model for tool invocation."""


def sanitize_envelope_content(raw_str: str) -> str:
    """Ensure raw external content cannot break out of or manipulate untrusted_evidence_data delimiters.

    Replaces any opening or closing tags matching '<untrusted_evidence_data' or '</untrusted_evidence_data>'
    with safe escaped entities '&lt;...&gt;'.
    """
    escaped = re.sub(
        r"<\s*/\s*untrusted_evidence_data\s*>",
        "&lt;/untrusted_evidence_data&gt;",
        raw_str,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"<\s*untrusted_evidence_data",
        "&lt;untrusted_evidence_data",
        escaped,
        flags=re.IGNORECASE,
    )


def compact_tool_payload_for_context(tool_name: str, data: Any) -> str:
    """Format tool execution results into a compact yet substantively complete representation for LLM context.

    Preserves:
    - tool execution status and provenance
    - key factual values and measurements
    - relevant text excerpts and descriptions
    - identifiers required for follow-up (e.g. ticket IDs, issue keys)
    - errors and limitations
    Removes redundant transport URLs, raw JSON schemas, and empty fields.
    """
    if data is None:
        return "{}"

    dump: dict[str, Any]
    if hasattr(data, "model_dump"):
        dump = data.model_dump()
    elif isinstance(data, dict):
        dump = data
    elif isinstance(data, list):
        dump = {"items": [x.model_dump() if hasattr(x, "model_dump") else x for x in data]}
    else:
        return str(data)

    if tool_name in ("search_tickets", "get_ticket", "get_ticket_comments"):
        if "tickets" in dump and isinstance(dump["tickets"], list):
            compact_tickets = []
            for t in dump["tickets"]:
                compact_tickets.append(
                    {
                        "id": t.get("id"),
                        "subject": t.get("subject"),
                        "description": (t.get("description") or "")[:300],
                        "status": t.get("status"),
                        "priority": t.get("priority"),
                        "channel": t.get("channel"),
                        "tags": t.get("tags", []),
                        "created_at": str(t.get("created_at")),
                    }
                )
            return json.dumps(
                {
                    "total_count": dump.get("total_count", len(compact_tickets)),
                    "tickets": compact_tickets,
                },
                default=str,
            )
        elif "ticket" in dump or "id" in dump:
            ticket_value = dump.get("ticket")
            ticket_detail: dict[str, Any] = ticket_value if isinstance(ticket_value, dict) else dump
            comments_compact = []
            for c in ticket_detail.get("comments", []):
                comments_compact.append(
                    {
                        "id": c.get("id"),
                        "author_role": c.get("author_role"),
                        "body": (c.get("body") or "")[:300],
                        "created_at": str(c.get("created_at")),
                    }
                )
            return json.dumps(
                {
                    "id": ticket_detail.get("id"),
                    "requester_id": ticket_detail.get("requester_id"),
                    "subject": ticket_detail.get("subject"),
                    "description": (ticket_detail.get("description") or "")[:400],
                    "status": ticket_detail.get("status"),
                    "priority": ticket_detail.get("priority"),
                    "channel": ticket_detail.get("channel"),
                    "tags": ticket_detail.get("tags", []),
                    "created_at": str(ticket_detail.get("created_at")),
                    "comments": comments_compact,
                },
                default=str,
            )
        elif "comments" in dump:
            comments_compact = []
            for c in dump.get("comments", []):
                comments_compact.append(
                    {
                        "id": c.get("id"),
                        "author_role": c.get("author_role"),
                        "body": (c.get("body") or "")[:300],
                        "created_at": str(c.get("created_at")),
                    }
                )
            return json.dumps(
                {
                    "ticket_id": dump.get("ticket_id"),
                    "comments": comments_compact,
                },
                default=str,
            )

    elif tool_name in ("search_issues", "get_issue", "get_issue_comments", "get_linked_issues"):
        if "issues" in dump and isinstance(dump["issues"], list):
            compact_issues = []
            for iss in dump["issues"]:
                compact_issues.append(
                    {
                        "key": iss.get("key"),
                        "summary": iss.get("summary"),
                        "status": iss.get("status"),
                        "priority": iss.get("priority"),
                        "issue_type": iss.get("issue_type"),
                        "created": str(iss.get("created")),
                        "description": (iss.get("description") or "")[:300],
                    }
                )
            return json.dumps(
                {
                    "total_returned": dump.get("total_returned", len(compact_issues)),
                    "issues": compact_issues,
                },
                default=str,
            )
        elif "issue" in dump or ("key" in dump and "comments" in dump):
            issue_value = dump.get("issue")
            issue_detail: dict[str, Any] = issue_value if isinstance(issue_value, dict) else dump
            comments_compact = []
            for c in issue_detail.get("comments", []):
                comments_compact.append(
                    {
                        "id": c.get("id"),
                        "author": c.get("author"),
                        "body": (c.get("body") or "")[:300],
                        "created": str(c.get("created")),
                    }
                )
            return json.dumps(
                {
                    "key": issue_detail.get("key"),
                    "summary": issue_detail.get("summary"),
                    "status": issue_detail.get("status"),
                    "priority": issue_detail.get("priority"),
                    "issue_type": issue_detail.get("issue_type"),
                    "created": str(issue_detail.get("created")),
                    "description": (issue_detail.get("description") or "")[:400],
                    "comments": comments_compact,
                    "linked_issues": issue_detail.get("linked_issues", []),
                },
                default=str,
            )
        elif "comments" in dump:
            comments_compact = []
            for c in dump.get("comments", []):
                comments_compact.append(
                    {
                        "id": c.get("id"),
                        "author": c.get("author"),
                        "body": (c.get("body") or "")[:300],
                        "created": str(c.get("created")),
                    }
                )
            return json.dumps(
                {
                    "issue_key": dump.get("issue_key"),
                    "comments": comments_compact,
                },
                default=str,
            )
        elif "linked_issues" in dump:
            return json.dumps(
                {
                    "issue_key": dump.get("issue_key"),
                    "linked_issues": dump.get("linked_issues", []),
                },
                default=str,
            )

    elif tool_name == "query_analytics":
        result_value = dump.get("result")
        res: dict[str, Any] = result_value if isinstance(result_value, dict) else dump
        rows = res.get("rows") or dump.get("results") or []
        return json.dumps(
            {
                "query_description": res.get("query_description"),
                "metric": res.get("metric"),
                "value": res.get("value"),
                "dimensions": res.get("dimensions", []),
                "time_range": res.get("time_range"),
                "raw_count": res.get("raw_count"),
                "limitations": res.get("limitations", []),
                "rows": rows[:30] if isinstance(rows, list) else rows,
            },
            default=str,
        )

    def _clean_dict(d: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for k, v in d.items():
            if v is None or "url" in k.lower():
                continue
            if isinstance(v, dict):
                cleaned[k] = _clean_dict(v)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                cleaned[k] = [_clean_dict(x) for x in v]
            else:
                cleaned[k] = v
        return cleaned

    return json.dumps(_clean_dict(dump), default=str)


class BaseSpecialistAgent(Generic[TTask, TFinding], ABC):
    """Abstract base class for domain specialist agents enforcing hard dual budgets."""

    def __init__(
        self,
        role: Literal["research", "analytics", "engineering"],
        toolset: RoleBoundToolset,
        llm_client: LLMClient,
        model_name: str,
        system_prompt: str,
        finding_type: type[TFinding],
        tool_call_budget: int,
        llm_call_budget: int,
    ) -> None:
        self.role = role
        self.toolset = toolset
        self.llm = llm_client
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.finding_type = finding_type
        self.result_model_type: type[SpecialistResult[TFinding]] = cast(
            type[SpecialistResult[TFinding]],
            SpecialistResult[finding_type],  # type: ignore[valid-type]
        )
        self.tool_call_budget = tool_call_budget
        self.llm_call_budget = llm_call_budget

        self.tool_call_count = 0
        self.llm_call_count = 0
        self.ledger = EvidenceLedger(role=self.role)

    def _reset_state(self, round_index: int | None = None) -> None:
        self.tool_call_count = 0
        self.llm_call_count = 0
        self.ledger = EvidenceLedger(role=self.role, round_index=round_index)

    def _format_tools_for_llm(self) -> list[dict[str, Any]]:
        tools_def: list[dict[str, Any]] = []
        for tool in self.toolset.tools:
            schema_cls = TOOL_INPUT_SCHEMAS.get(tool.name)
            tools_def.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": schema_cls.model_json_schema() if schema_cls else {},
                    },
                }
            )
        return tools_def

    async def execute(
        self,
        task: TTask,
        *,
        round_index: int | None = None,
        tool_budget_override: int | None = None,
        llm_budget_override: int | None = None,
    ) -> SpecialistResult[TFinding]:
        """Execute specialist investigation loop subject to hard tool and LLM ceilings."""
        self._reset_state(round_index=round_index)
        effective_tool_budget = (
            min(tool_budget_override, self.tool_call_budget)
            if tool_budget_override is not None
            else self.tool_call_budget
        )
        task_llm_budget = getattr(task, "llm_call_budget", None)
        active_llm_override = (
            min(llm_budget_override, task_llm_budget)
            if (llm_budget_override is not None and task_llm_budget is not None)
            else (llm_budget_override if llm_budget_override is not None else task_llm_budget)
        )
        effective_llm_budget = (
            min(active_llm_override, self.llm_call_budget)
            if active_llm_override is not None
            else self.llm_call_budget
        )
        tools_def = self._format_tools_for_llm()

        # Initialize conversation state guiding complete Turn 1 retrieval
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=self.system_prompt),
            LLMMessage(
                role="user",
                content=(
                    f"INVESTIGATION TASK:\n"
                    f"User Question: {task.user_question}\n"
                    f"Domain Objective: {task.objective}\n"
                    f"Specific Diagnostic Questions: {task.specific_questions}\n\n"
                    f"TIME SCOPE: {task.scope.describe()}\n"
                    f"Only use evidence inside the selected primary period when one is provided. "
                    f"Use the comparison period only for comparison; do not mix it into the primary result.\n\n"
                    f"INSTRUCTIONS:\n"
                    f"Formulate a complete, focused initial batch of authorized domain tool calls to gather all relevant evidence needed for your domain objective. "
                    f"Query all relevant dimensions in this retrieval batch so you can proceed directly to structured synthesis."
                ),
            ),
        ]

        # ---------------------------------------------------------------------
        # 1. Bounded Tool-Selection Loop (Target: 1 retrieval batch -> synthesis)
        # ---------------------------------------------------------------------
        while (
            self.tool_call_count < effective_tool_budget
            and self.llm_call_count <= (effective_llm_budget - 1)
            and tools_def
        ):
            if self.llm_call_count >= (effective_llm_budget - 1):
                logger.info(
                    "LLM budget reservation reached (%d/%d); halting tool loop for synthesis",
                    self.llm_call_count,
                    effective_llm_budget,
                )
                break

            try:
                response = await self.llm.complete(
                    messages=messages,
                    model=self.model_name,
                    tools=tools_def,
                    temperature=0.0,
                    role=self.role,
                )
            except TypeError:
                response = await self.llm.complete(
                    messages=messages,
                    model=self.model_name,
                    tools=tools_def,
                    temperature=0.0,
                )
            self.llm_call_count += 1

            if not response.tool_calls:
                # LLM decided it has enough information or gave free text; exit tool loop
                if response.content:
                    messages.append(LLMMessage(role="assistant", content=response.content))
                break

            messages.append(
                LLMMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            # Execute tool calls individually against tool budget
            for tc in response.tool_calls:
                if self.tool_call_count >= effective_tool_budget:
                    logger.info(
                        "Tool budget reached (%d/%d); discarding remaining tool calls",
                        self.tool_call_count,
                        effective_tool_budget,
                    )
                    messages.append(
                        LLMMessage(
                            role="tool",
                            tool_call_id=tc.id,
                            content=(
                                "<tool_execution_status>\n"
                                "Tool execution halted: configured tool_call_budget exhausted.\n"
                                "</tool_execution_status>"
                            ),
                        )
                    )
                    break

                # If tool is unauthorized for this role, invoke directly to trigger permission_denied ToolResult
                if hasattr(self.toolset, "_tools") and tc.function_name not in self.toolset._tools:
                    tool_result = await self.toolset.invoke_tool(tc.function_name, EmptyInput())
                    self.tool_call_count += 1
                    entry = self.ledger.record_tool_result(tool_result)
                    err_msg = (
                        tool_result.error.message if tool_result.error else "Permission denied"
                    )
                    messages.append(
                        LLMMessage(
                            role="tool",
                            tool_call_id=tc.id,
                            content=(
                                f'<untrusted_evidence_data source_reference="failed" ledger_entry_id="none">\n'
                                f"TOOL EXECUTION FAILED (permission_denied): {err_msg}\n"
                                f"</untrusted_evidence_data>"
                            ),
                        )
                    )
                    continue

                schema_cls = TOOL_INPUT_SCHEMAS.get(tc.function_name)
                validation_error: str | None = None
                raw_arguments = tc.arguments

                # Failure events describe outcomes, not a required next step in
                # a conversion journey. Keeping them inside a funnel can turn a
                # valid started/submitted/completed sequence into an empty
                # result when failure instrumentation is absent. Preserve the
                # normal journey and let failure counts/breakdowns run as
                # separate analytics queries.
                if (
                    tc.function_name == "query_analytics"
                    and isinstance(raw_arguments, dict)
                    and raw_arguments.get("intent") == "funnel"
                    and isinstance(raw_arguments.get("steps"), list)
                ):
                    journey_steps = [
                        step
                        for step in raw_arguments["steps"]
                        if not str(step).endswith(("_failed", "_cancelled"))
                    ]
                    if len(journey_steps) >= 2:
                        raw_arguments = {**raw_arguments, "steps": journey_steps}

                if (
                    tc.function_name == "search_tickets"
                    and task.scope.is_bounded
                    and isinstance(raw_arguments, dict)
                ):
                    assert task.scope.start_time is not None
                    assert task.scope.end_time is not None
                    raw_arguments = {
                        **raw_arguments,
                        "start_time": task.scope.start_time.isoformat(),
                        "end_time": task.scope.end_time.isoformat(),
                    }

                # The investigation scope is authoritative. Normalize it before
                # schema validation so a model-supplied relative window cannot
                # conflict with the explicit PM-selected dates and waste the
                # analytics tool budget on a preventable validation error.
                if (
                    tc.function_name == "query_analytics"
                    and task.scope.is_bounded
                    and isinstance(raw_arguments, dict)
                ):
                    assert task.scope.start_time is not None
                    assert task.scope.end_time is not None
                    raw_arguments = {
                        **raw_arguments,
                        "time_range_days": None,
                        "start_time": task.scope.start_time.isoformat(),
                        "end_time": task.scope.end_time.isoformat(),
                    }

                if schema_cls and isinstance(raw_arguments, dict):
                    try:
                        input_data: BaseModel = schema_cls.model_validate(raw_arguments)
                    except Exception as val_exc:
                        validation_error = f"Invalid arguments for {tc.function_name}: {val_exc}"
                        input_data = EmptyInput()
                elif isinstance(raw_arguments, BaseModel):
                    input_data = raw_arguments
                else:
                    input_data = EmptyInput()

                if validation_error:
                    role_source_map = {
                        "research": "zendesk",
                        "analytics": "posthog",
                        "engineering": "jira",
                    }
                    tool_result = ToolResult(
                        success=False,
                        data=None,
                        error=ToolError(
                            error_type="invalid_input",
                            message=validation_error,
                            attempted_source=role_source_map.get(self.role),  # type: ignore[arg-type]
                        ),
                        provenance=None,
                        execution_duration_ms=0.0,
                    )
                else:
                    tool_result = await self.toolset.invoke_tool(tc.function_name, input_data)
                self.tool_call_count += 1

                # Record in authoritative append-only ledger (stores complete, untruncated typed payload)
                entry = self.ledger.record_tool_result(tool_result)
                entry_id = entry.ledger_entry_id if entry else "led_unrecorded"

                # Format compact substantive tool output for LLM conversation history
                if tool_result.success and tool_result.provenance:
                    source_ref = tool_result.provenance.source_reference
                    compact_data_str = compact_tool_payload_for_context(
                        tc.function_name, tool_result.data
                    )
                    safe_data_str = sanitize_envelope_content(compact_data_str)
                    safe_source_ref = source_ref.replace('"', "&quot;")
                    safe_entry_id = entry_id.replace('"', "&quot;")
                    tool_content = (
                        f'<untrusted_evidence_data source_reference="{safe_source_ref}" ledger_entry_id="{safe_entry_id}">\n'
                        f"{safe_data_str}\n"
                        f"</untrusted_evidence_data>"
                    )
                else:
                    err_msg = tool_result.error.message if tool_result.error else "Unknown error"
                    err_type = tool_result.error.error_type if tool_result.error else "error"
                    safe_err_msg = sanitize_envelope_content(err_msg)
                    tool_content = (
                        f'<untrusted_evidence_data source_reference="failed" ledger_entry_id="none">\n'
                        f"TOOL EXECUTION FAILED ({err_type}): {safe_err_msg}\n"
                        f"</untrusted_evidence_data>"
                    )

                messages.append(
                    LLMMessage(
                        role="tool",
                        tool_call_id=tc.id,
                        content=tool_content,
                    )
                )

            # Standard profile reserves at most one extra call for schema repair,
            # but retrieval remains a strict single batch.
            if active_llm_override is not None and active_llm_override <= 3:
                logger.info(
                    "Standard profile enforcement: Turn 1 batch tool execution completed (%d call made); breaking for direct Turn 2 synthesis",
                    self.llm_call_count,
                )
                break

            # Deep profile adaptive path: after Turn 1 retrieval, prompt specialist to synthesize unless an authentic gap exists
            if self.llm_call_count == 1 and self.llm_call_count < (effective_llm_budget - 1):
                messages.append(
                    LLMMessage(
                        role="user",
                        content=(
                            "Retrieved domain evidence has been recorded in the Evidence Ledger. "
                            "If you have gathered sufficient evidence to address the domain objective, proceed directly to final structured synthesis without requesting further tools. "
                            "Only request an additional tool call if an authentic, blocking evidence gap remains that must be queried."
                        ),
                    )
                )

        # ---------------------------------------------------------------------
        # 2. Evidence-Grounded Final Structured Synthesis
        # ---------------------------------------------------------------------
        # If LLM budget is fully exhausted, execute deterministic fallback
        if self.llm_call_count >= effective_llm_budget:
            logger.warning(
                "LLM budget exhausted (%d/%d); executing deterministic fallback",
                self.llm_call_count,
                effective_llm_budget,
            )
            return self._build_deterministic_fallback(
                task, reason="LLM call budget exhausted before synthesis"
            )

        # Build grounded synthesis prompt
        synthesis_prompt = self._build_synthesis_prompt(task)
        synthesis_messages = [
            LLMMessage(role="system", content=self.system_prompt),
            LLMMessage(role="user", content=synthesis_prompt),
        ]

        # Call structured synthesis (counts as 1 LLM call)
        repair_attempts = 0
        final_result: SpecialistResult[TFinding] | None = None

        max_synthesis_repairs = (
            1 if effective_llm_budget == 3 else (0 if effective_llm_budget <= 2 else 2)
        )
        while (
            repair_attempts <= max_synthesis_repairs and self.llm_call_count < effective_llm_budget
        ):
            call_made = False
            try:
                try:
                    raw_result = await self.llm.complete_structured(
                        messages=synthesis_messages,
                        model=self.model_name,
                        response_model=self.result_model_type,
                        temperature=0.0,
                        role=self.role,
                    )
                except TypeError:
                    raw_result = await self.llm.complete_structured(
                        messages=synthesis_messages,
                        model=self.model_name,
                        response_model=self.result_model_type,
                        temperature=0.0,
                    )
                call_made = True
                self.llm_call_count += 1

                # Validate Evidence identity against the authoritative ledger
                self.ledger.validate_specialist_result(raw_result)
                final_result = raw_result
                break

            except Exception as exc:
                if not call_made:
                    self.llm_call_count += 1
                if repair_attempts == 0:
                    logger.warning("Initial specialist synthesis failed validation: %s", exc)
                else:
                    logger.warning(
                        "Specialist synthesis repair failed validation (repair attempt %d/2): %s",
                        repair_attempts,
                        exc,
                    )
                repair_attempts += 1
                if repair_attempts <= 2 and self.llm_call_count < self.llm_call_budget:
                    synthesis_messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                f"VALIDATION ERROR IN PREVIOUS OUTPUT:\n{exc}\n\n"
                                f"Please correct the error and return a valid JSON object matching the schema. "
                                f"Ensure all evidence.ledger_entry_id, source_type, and source_reference match the ledger exactly."
                            ),
                        )
                    )

        if final_result is None:
            logger.warning(
                "Synthesis validation failed after %d repairs; using deterministic fallback",
                repair_attempts,
            )
            return self._build_deterministic_fallback(
                task, reason="Output validation failed and LLM call budget exhausted"
            )

        # ---------------------------------------------------------------------
        # 3. Post-Processing & Failure Propagation
        # ---------------------------------------------------------------------
        # Automatically inject any tool errors as limitations and unanswered questions
        failure_limitations = self.ledger.get_failure_limitations()
        all_limitations = list(final_result.limitations)
        for fl in failure_limitations:
            if fl not in all_limitations:
                all_limitations.append(fl)

        # Create finalized result preserving immutable accounting
        final_findings: list[TFinding] = list(final_result.findings)
        return SpecialistResult[TFinding](
            agent_role=self.role,
            findings=final_findings,
            overall_facts=final_result.overall_facts,
            overall_interpretations=final_result.overall_interpretations,
            overall_hypotheses=final_result.overall_hypotheses,
            contradictions=final_result.contradictions,
            unanswered_questions=final_result.unanswered_questions or [task.objective],
            limitations=all_limitations,
            tool_call_count=self.tool_call_count,
            llm_call_count=self.llm_call_count,
            investigation_complete=final_result.investigation_complete,
        )

    def _build_synthesis_prompt(self, task: TTask) -> str:
        """Compile grounded synthesis context from verified Evidence Ledger entries."""
        ledger_lines: list[str] = []
        for entry in self.ledger.entries:
            ledger_lines.append(
                f"- ID: {entry.ledger_entry_id} | Source: {entry.source_type} | Ref: {entry.source_reference}\n"
                f"  Summary: {entry.data_summary}"
            )
        ledger_text = "\n".join(ledger_lines) if ledger_lines else "No successful data retrieved."

        failures = self.ledger.get_failure_limitations()
        failures_text = "\n".join(f"- {f}" for f in failures) if failures else "None."

        return (
            f"FINAL SYNTHESIS REQUEST:\n"
            f"User Question: {task.user_question}\n"
            f"Domain Objective: {task.objective}\n"
            f"Specific Questions: {task.specific_questions}\n\n"
            f"VERIFIED EVIDENCE LEDGER (Only cite items from this list):\n"
            f"{ledger_text}\n\n"
            f"DATA GAPS & FAILED TOOL ATTEMPTS:\n"
            f"{failures_text}\n\n"
            f"INSTRUCTIONS:\n"
            f"Synthesize the verified ledger evidence into a concise SpecialistResult (aim for 2 to 4 core findings grouped by pattern/theme rather than repeating raw entries).\n"
            f"1. For every finding, populate distinct 'facts', 'interpretations', and 'hypotheses'.\n"
            f"2. Every evidence item MUST cite an exact ledger_entry_id from the ledger above, with matching source_type and source_reference.\n"
            f"3. Do not invent citations or extrapolate beyond observed facts.\n"
            f"4. Document any conflicting evidence in 'contradictions'.\n"
            f"5. Document any data gaps or tool failures in 'limitations' and 'unanswered_questions'."
        )

    def _build_deterministic_fallback(self, task: TTask, reason: str) -> SpecialistResult[TFinding]:
        """Construct a minimal valid SpecialistResult deterministically from ledger entries without LLM calls."""
        fallback_findings: list[TFinding] = []

        for entry in self.ledger.entries:
            ev = Evidence(
                ledger_entry_id=entry.ledger_entry_id,
                source_type=entry.source_type,
                source_reference=entry.source_reference,
                finding=f"Verified data retrieved from {entry.source_reference}",
                support=entry.data_summary[:100],
                confidence=EvidenceConfidence.LOW,
                limitations=["Constructed via deterministic fallback"],
            )
            # Instantiate concrete finding type with minimal required fields
            finding_kwargs = {
                "finding": f"Observation from {entry.source_reference}",
                "facts": [entry.data_summary],
                "interpretations": ["Data retrieved prior to budget exhaustion"],
                "hypotheses": [],
                "evidence": [ev],
                "confidence": EvidenceConfidence.LOW,
                "limitations": [reason],
            }
            # Add domain-specific required fields
            if self.role == "research":
                finding_kwargs["observed_pattern"] = entry.data_summary[:50]
            elif self.role == "analytics":
                finding_kwargs["metric"] = "retrieved_metric"
                finding_kwargs["value"] = "observed"
            elif self.role == "engineering":
                finding_kwargs["technical_context"] = entry.data_summary[:50]
                finding_kwargs["relationship_to_problem"] = "Contextual technical record"

            fallback_findings.append(self.finding_type(**finding_kwargs))  # type: ignore[arg-type]

        limitations = [reason] + self.ledger.get_failure_limitations()

        return SpecialistResult[TFinding](
            agent_role=self.role,
            findings=fallback_findings,
            overall_facts=[e.data_summary for e in self.ledger.entries],
            overall_interpretations=["Incomplete investigation due to budget limit"],
            overall_hypotheses=[],
            contradictions=[],
            unanswered_questions=task.specific_questions or [task.objective],
            limitations=limitations,
            tool_call_count=self.tool_call_count,
            llm_call_count=self.llm_call_count,
            investigation_complete=False,
        )
