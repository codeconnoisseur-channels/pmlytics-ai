"""Authoritative Evidence Ledger for specialist agents with zero Any."""

from datetime import datetime
from typing import Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.domain.analytics import AnalyticsQueryResult
from app.domain.jira import JiraComment, JiraIssue, JiraIssueLink
from app.domain.provenance import source_references_match
from app.domain.specialists import SpecialistResult, TFinding
from app.domain.zendesk import ZendeskComment, ZendeskTicket
from app.integrations.jira.adapter import JiraSearchResult
from app.integrations.zendesk.adapter import ZendeskSearchResult
from app.tools.analytics import QueryAnalyticsOutput
from app.tools.base import ToolError, ToolResult
from app.tools.engineering import (
    GetIssueCommentsOutput,
    GetIssueOutput,
    GetLinkedIssuesOutput,
    SearchIssuesOutput,
)
from app.tools.support import (
    GetTicketCommentsOutput,
    GetTicketOutput,
    SearchTicketsOutput,
)

LedgerPayload = (
    # Tool output envelopes
    SearchTicketsOutput
    | GetTicketOutput
    | GetTicketCommentsOutput
    | QueryAnalyticsOutput
    | SearchIssuesOutput
    | GetIssueOutput
    | GetIssueCommentsOutput
    | GetLinkedIssuesOutput
    # Operational domain entities
    | ZendeskTicket
    | ZendeskComment
    | list[ZendeskComment]
    | ZendeskSearchResult
    | JiraIssue
    | list[JiraComment]
    | list[JiraIssueLink]
    | JiraSearchResult
    | AnalyticsQueryResult
)


class EvidenceLedgerEntry(BaseModel):
    """An immutable record of verified data retrieved from a successful tool execution."""

    model_config = ConfigDict(frozen=True)

    ledger_entry_id: str = Field(
        ...,
        description="Unique invocation-level identifier, e.g. 'led_001'",
    )
    source_type: Literal["zendesk", "posthog", "jira"] = Field(
        ...,
        description="External domain source type",
    )
    source_reference: str = Field(
        ...,
        description="Display reference (e.g. 'ticket_id:101', 'issue_key:PAY-117')",
    )
    retrieved_at: datetime = Field(
        ...,
        description="UTC timestamp when evidence was retrieved",
    )
    data_summary: str = Field(
        ...,
        description="Concise factual excerpt or metric summary derived from payload",
    )
    typed_payload: LedgerPayload = Field(
        ...,
        description="Strongly typed domain entity payload",
    )


TLedgerPayload = TypeVar("TLedgerPayload", bound=LedgerPayload)


class EvidenceLedger(BaseModel):
    """Authoritative operational ledger tracking all evidence gathered during an investigation."""

    role: str = ""
    round_index: int | None = None
    entries: list[EvidenceLedgerEntry] = Field(default_factory=list)
    failed_tool_attempts: list[ToolError] = Field(default_factory=list)

    @property
    def failed_results(self) -> list[ToolError]:
        """Compatibility property accessing failed tool attempts."""
        return self.failed_tool_attempts

    def record_tool_result(self, result: ToolResult[TLedgerPayload]) -> EvidenceLedgerEntry | None:
        """Record successful evidence or failed tool attempts with zero Any.

        Returns EvidenceLedgerEntry if successful, None if failed.
        """
        if result.success and result.provenance and result.data is not None:
            if self.role and self.round_index is not None:
                prefix = f"{self.role}:r{self.round_index}:"
            elif self.role:
                prefix = f"{self.role}:"
            else:
                prefix = ""
            entry_id = f"{prefix}led_{len(self.entries) + 1:03d}"
            summary = self._extract_summary(result.data)
            entry = EvidenceLedgerEntry(
                ledger_entry_id=entry_id,
                source_type=result.provenance.source_type,
                source_reference=result.provenance.source_reference,
                retrieved_at=result.provenance.retrieved_at,
                data_summary=summary,
                typed_payload=result.data,
            )
            self.entries.append(entry)
            return entry
        if not result.success and result.error is not None:
            # Failed tool results NEVER enter evidence entries; they track gaps/limitations
            self.failed_tool_attempts.append(result.error)
            return None
        return None

    def get_entry_by_id(self, ledger_entry_id: str) -> EvidenceLedgerEntry | None:
        """Find a ledger entry by its unique invocation ID."""
        for e in self.entries:
            if e.ledger_entry_id == ledger_entry_id:
                return e
        return None

    def get_valid_ledger_ids(self) -> set[str]:
        """Return the set of all verified ledger entry IDs."""
        return {e.ledger_entry_id for e in self.entries}

    def validate_specialist_result(self, result: SpecialistResult[TFinding]) -> None:
        """Strictly validate Evidence identity against the authoritative ledger entry:

        1. ledger_entry_id must exist in the ledger.
        2. source_type must match the referenced ledger entry exactly.
        3. source_reference must match the referenced ledger entry exactly.
        """
        for finding in result.findings:
            for ev in finding.evidence:
                entry = self.get_entry_by_id(ev.ledger_entry_id)
                if entry is None:
                    valid_ids = sorted(e.ledger_entry_id for e in self.entries)
                    raise ValueError(
                        f"Unverified evidence ledger_entry_id '{ev.ledger_entry_id}' found in finding. "
                        f"Every evidence item must reference an exact successful ledger entry. "
                        f"Valid retrieved IDs: {valid_ids}"
                    )
                if ev.source_type != entry.source_type:
                    raise ValueError(
                        f"Evidence source_type mismatch for ledger entry '{ev.ledger_entry_id}': "
                        f"expected '{entry.source_type}', got '{ev.source_type}'."
                    )
                if not source_references_match(
                    entry.source_type, entry.source_reference, ev.source_reference
                ):
                    raise ValueError(
                        f"Evidence source_reference mismatch for ledger entry '{ev.ledger_entry_id}': "
                        f"expected '{entry.source_reference}', got '{ev.source_reference}'."
                    )

    def get_failure_limitations(self) -> list[str]:
        """Generate limitation descriptions from failed tool attempts."""
        limitations: list[str] = []
        for err in self.failed_tool_attempts:
            source = err.attempted_source or "tool"
            limitations.append(f"{source} query failed ({err.error_type}): {err.message}")
        return limitations

    @staticmethod
    def _extract_summary(payload: LedgerPayload) -> str:
        """Extract a concise factual summary from a typed domain entity."""
        # Tool output envelopes
        from app.tools.analytics import QueryAnalyticsOutput
        from app.tools.engineering import (
            GetIssueCommentsOutput,
            GetIssueOutput,
            GetLinkedIssuesOutput,
            SearchIssuesOutput,
        )
        from app.tools.support import (
            GetTicketCommentsOutput,
            GetTicketOutput,
            SearchTicketsOutput,
        )

        if isinstance(payload, SearchTicketsOutput):
            if not payload.tickets:
                return "Customer-support search returned 0 conversations."
            examples = "; ".join(
                f"#{ticket.id} {ticket.subject}: {ticket.description[:180]}"
                for ticket in payload.tickets[:8]
            )
            return (
                f"Customer-support search returned {payload.total_count} conversations. "
                f"Representative records: {examples}"
            )
        if isinstance(payload, GetTicketOutput):
            return (
                f"Ticket #{payload.ticket.id} [{payload.ticket.status}]: {payload.ticket.subject}"
            )
        if isinstance(payload, GetTicketCommentsOutput):
            return f"Ticket #{payload.ticket_id} has {len(payload.comments)} comments"
        if isinstance(payload, QueryAnalyticsOutput):
            return EvidenceLedger._analytics_summary(payload.result)
        if isinstance(payload, SearchIssuesOutput):
            if not payload.issues:
                return "Engineering search returned 0 matching issues."
            examples = "; ".join(
                f"{issue.key} [{issue.status}] {issue.summary}: {issue.description[:180]}"
                for issue in payload.issues[:5]
            )
            return (
                f"Engineering search returned {payload.total_returned} matching issues. "
                f"Records: {examples}"
            )
        if isinstance(payload, GetIssueOutput):
            return f"Issue {payload.issue.key} [{payload.issue.status}]: {payload.issue.summary}"
        if isinstance(payload, GetIssueCommentsOutput):
            return f"Issue {payload.issue_key} has {len(payload.comments)} comments"
        if isinstance(payload, GetLinkedIssuesOutput):
            return f"Issue {payload.issue_key} has {len(payload.linked_issues)} linked issues"

        # Direct domain entities
        if isinstance(payload, ZendeskTicket):
            return f"Ticket #{payload.id} [{payload.status}, {payload.priority}]: {payload.subject}. Description: {payload.description[:150]}"
        if isinstance(payload, ZendeskComment):
            role_label = "Customer" if payload.author_role == "customer" else "Agent Staff"
            visibility = "Public" if payload.public else "Internal Note"
            return f"Comment on Ticket #{payload.ticket_id} by {role_label} ({visibility}): {payload.body[:150]}"
        if isinstance(payload, list) and payload and isinstance(payload[0], ZendeskComment):
            comments_list: list[ZendeskComment] = payload
            return (
                f"{len(comments_list)} comments retrieved. Latest: {comments_list[-1].body[:100]}"
            )
        if isinstance(payload, ZendeskSearchResult):
            return f"Zendesk search returned {payload.count} tickets. Matching IDs: {[t.id for t in payload.tickets[:5]]}"
        if isinstance(payload, JiraIssue):
            return f"Jira {payload.key} [{payload.status}, {payload.priority}]: {payload.summary}. Description: {payload.description[:150]}"
        if isinstance(payload, list) and payload and isinstance(payload[0], JiraComment):
            jira_comments: list[JiraComment] = payload
            return f"{len(jira_comments)} Jira comments retrieved. Latest: {jira_comments[-1].body[:100]}"
        if isinstance(payload, list) and payload and isinstance(payload[0], JiraIssueLink):
            links: list[JiraIssueLink] = payload
            return f"{len(links)} linked issues retrieved: {[(link.relationship, link.outward_key) for link in links]}"
        if isinstance(payload, JiraSearchResult):
            return f"Jira search returned {len(payload.issues)} issues. Keys: {[i.key for i in payload.issues[:5]]}"
        if isinstance(payload, AnalyticsQueryResult):
            return EvidenceLedger._analytics_summary(payload)
        return "Retrieved domain data record"

    @staticmethod
    def _analytics_summary(result: AnalyticsQueryResult) -> str:
        """Preserve tabular metrics in the prompt-sized ledger summary.

        Event-count and breakdown queries intentionally return tables, so their
        scalar ``value`` is often None.  Treating that as the whole result hid
        the useful numbers from the Analytics Agent and PM synthesis.
        """
        if result.value is not None:
            return (
                f"Product analytics: {result.query_description}. "
                f"Metric {result.metric}: {result.value}."
            )

        if result.rows:
            rendered_rows = []
            for row in result.rows[:12]:
                fields = ", ".join(f"{key}={value}" for key, value in row.items())
                rendered_rows.append(fields)
            suffix = "" if len(result.rows) <= 12 else f"; plus {len(result.rows) - 12} more rows"
            return (
                f"Product analytics: {result.query_description}. "
                f"{result.metric} results: " + "; ".join(rendered_rows) + suffix + "."
            )

        return f"Product analytics: {result.query_description}. No matching records were returned."
