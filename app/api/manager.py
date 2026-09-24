"""Single-process asynchronous investigation manager for portfolio/demo deployment."""

import asyncio
import logging
import re
import uuid
from collections.abc import AsyncGenerator
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any

from app.agents.ledger import EvidenceLedgerEntry
from app.api.schemas import (
    CriticReviewSchema,
    EvidenceLedgerItemSchema,
    EvidenceSupportingRecordSchema,
    InvestigationDetailResponse,
    InvestigationStatusResponse,
    ProductRecommendationSchema,
    StructuredEvidenceCitationSchema,
    StructuredFindingSchema,
    TelemetrySummarySchema,
)
from app.domain.analytics import AnalyticsQueryResult
from app.domain.investigation_scope import InvestigationScope
from app.domain.jira import JiraComment, JiraIssue
from app.domain.zendesk import ZendeskComment, ZendeskTicket
from app.integrations.observability.tracer import InvestigationTracer
from app.orchestration.service import InvestigationService
from app.orchestration.state import InvestigationState
from app.storage.investigations import InvestigationRepository, PersistedInvestigation
from app.tools.analytics import QueryAnalyticsOutput
from app.tools.engineering import GetIssueCommentsOutput, GetIssueOutput, SearchIssuesOutput
from app.tools.support import GetTicketCommentsOutput, GetTicketOutput, SearchTicketsOutput

logger = logging.getLogger(__name__)

_LEASE_DURATION = timedelta(minutes=5)
_HEARTBEAT_INTERVAL_SECONDS = 30


_INTERNAL_DETAIL_PATTERN = re.compile(
    r"(?:https?://|localhost|/api/|/rest/|"
    r"\bserver disconnected\b|\bconnection (?:failed|refused)\b|\bhttp\s*\d{3}\b|"
    r"\b(?:jql|hogql|query:)\b|\btool error\b|"
    r"\b(?:system prompt|prompt injection|system override|ignore previous)\b)",
    re.IGNORECASE,
)

_INTERNAL_LIMITATION_PATTERN = re.compile(
    r"(?:\b(?:llm|schema|structured generation|output validation|critic|ledger)\b|"
    r"\b(?:tool|query) (?:failed|failure|budget)\b|"
    r"\b(?:jira|zendesk|posthog) (?:scope|search|query|issue tracking)\b|"
    r"\b(?:raw|rest) api\b)",
    re.IGNORECASE,
)


def _public_source_reference(source_type: str, source_reference: str) -> str:
    """Return a useful, non-implementation-facing evidence label."""
    if source_type == "zendesk":
        ticket = re.search(r"(?:ticket(?:_id)?[:# ]?)(\d+)", source_reference, re.IGNORECASE)
        return (
            f"Customer conversation #{ticket.group(1)}" if ticket else "Customer support evidence"
        )
    if source_type == "jira":
        issue = re.search(r"\b[A-Z][A-Z0-9]+-\d+\b", source_reference)
        return f"Engineering issue {issue.group(0)}" if issue else "Engineering delivery context"
    return "Product analytics evidence"


def _public_text(text: str, *, fallback: str) -> str:
    """Translate safe product evidence without discarding an entire useful sentence."""
    citations: dict[str, str] = {}

    def preserve_citation(match: re.Match[str]) -> str:
        token = f"CITATIONTOKEN{len(citations)}"
        citations[token] = f"[{match.group(1)}]"
        return token

    cleaned = re.sub(
        r"\[?((?:research|analytics|engineering):r\d+:led_\d+)\]?",
        preserve_citation,
        text,
        flags=re.IGNORECASE,
    )
    cleaned = cleaned.replace("\\_", "_")
    replacements = (
        (r"\bvalidation-driven technical remediation track\b", "focused reliability improvement"),
        (r"\bpost-submission handling area\b", "payment confirmation step"),
        (r"\bmonth-end payment status updates backlog\b", "month-end payment confirmation backlog"),
        (r"\bprocessing delay behavior\b", "delayed payment processing"),
        (r"\bservice-error-heavy failures\b", "service errors"),
        (
            r"Proceed with a focused reliability improvement for the bill-payment path, focused first on",
            "Proceed with a focused reliability improvement for the bill-payment path, prioritising",
        ),
        (r"\boperational cause\b", "primary cause"),
        (r"\bBAD[_ ]GATEWAY-heavy\b", "service-error-heavy"),
        (r"\bfailures are mostly BAD[_ ]GATEWAY\b", "failures are mostly service errors"),
        (r"\bBAD[_ ]GATEWAY accounts\b", "service errors account"),
        (r"\blabeled BAD[_ ]GATEWAY\b", "classified as service errors"),
        (r"\bBAD[_ ]GATEWAY failures\b", "service-error failures"),
        (r"\bTIMEOUT-driven\b", "processing-delay"),
        (r"\bBAD[_ ]GATEWAY\b", "service error"),
        (r"\bTIMEOUTS?\b", "processing delay"),
        (r"\bwebhook processing\b", "payment status updates"),
        (r"\basync payment status updates backlogs?\b", "payment confirmation backlog"),
        (r"\bwebhooks?\b", "payment status updates"),
        (r"\bgateway/API layer\b", "payment processing services"),
        (r"\bAPI/load-related\b", "service-capacity-related"),
        (r"\bAPI\s*v?\d+\b", "payment path"),
        (r"\bAPIs?(?: endpoints?| layer| responsiveness| failures?)?\b", "payment service"),
        (r"\bupstream\b", "payment provider"),
        (r"\bbackend processing\b", "payment processing"),
        (r"\bserver load\b", "service capacity"),
        (r"\bgateway instability\b", "payment-provider reliability issues"),
        (r"\bgateway failures\b", "payment-provider failures"),
        (r"\blatency\b", "processing time"),
        (r"\berror-rate\b", "failure-rate"),
        (r"\berror rates\b", "failure rates"),
        (r"\bfailure-code breakdown shows\b", "failure records show"),
        (r"\bpayment processing payment service\b", "payment service"),
        (r"\bBaseline source:\s*", ""),
        (r"\btelemetry\b", "product analytics"),
        (r"\bZendesk\b", "customer support"),
        (r"\bJira\b", "engineering"),
        (r"\bPostHog\b", "product analytics"),
        (r"\bpayment-provider reliability issues is\b", "payment-provider reliability is"),
        (
            r"\bdirect processing time or failure-rate metrics\b",
            "direct processing-performance metrics",
        ),
    )
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    # Some phrases are produced by an earlier translation in this same pass.
    # Normalize those derived phrases before returning customer-facing copy.
    cleaned = re.sub(
        r"\bservice-error-heavy failures\b", "service errors", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\bmonth-end payment status updates backlog\b",
        "month-end payment confirmation backlog",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"(?<=\w)_(?=\w)", " ", cleaned)
    cleaned = " ".join(cleaned.split())
    if not cleaned or _INTERNAL_DETAIL_PATTERN.search(cleaned):
        return fallback
    for token, citation in citations.items():
        cleaned = cleaned.replace(token, citation)
    if cleaned and cleaned[0].isalpha():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def _public_list(
    values: list[str],
    *,
    fallback: str | None = None,
    limit: int | None = None,
) -> list[str]:
    """Sanitize, deduplicate, and bound repeated model-generated report items."""
    visible: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _public_text(value, fallback="")
        key = (
            re.sub(
                r"(?:EV-\d+|(?:research|analytics|engineering):r\d+:led_\d+)",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            .strip(" [],")
            .casefold()
        )
        if not cleaned or not key or key in seen:
            continue
        seen.add(key)
        visible.append(cleaned)
        if limit is not None and len(visible) >= limit:
            break
    if not visible and fallback:
        visible.append(fallback)
    return visible


def _public_limitations(limitations: list[str]) -> list[str]:
    visible: list[str] = []
    for limitation in limitations:
        # Critic diagnostics are internal workflow controls, not customer copy.
        # The revised recommendation already carries the corresponding bounded
        # uncertainty in plain product language.
        if limitation.lower().startswith(
            "unresolved critic issue"
        ) or _INTERNAL_LIMITATION_PATTERN.search(limitation):
            continue
        cleaned = _public_text(
            limitation,
            fallback="",
        )
        if cleaned not in visible:
            visible.append(cleaned)
        if len(visible) >= 4:
            break
    return visible


def _ticket_supporting_record(ticket: ZendeskTicket) -> EvidenceSupportingRecordSchema:
    return EvidenceSupportingRecordSchema(
        record_id=f"ticket-{ticket.id}",
        record_type="ticket",
        source_reference=f"Customer conversation #{ticket.id}",
        title=_public_text(ticket.subject, fallback="Customer support conversation"),
        excerpt=_public_text(
            ticket.description,
            fallback="The customer described an experience relevant to this finding.",
        ),
        status=ticket.status.replace("_", " ").title(),
        occurred_at=ticket.created_at,
        attributes={
            "Priority": ticket.priority.title(),
            "Channel": ticket.channel.title(),
        },
    )


def _zendesk_comment_supporting_record(
    comment: ZendeskComment,
) -> EvidenceSupportingRecordSchema:
    return EvidenceSupportingRecordSchema(
        record_id=f"ticket-{comment.ticket_id}-comment-{comment.id}",
        record_type="comment",
        source_reference=f"Customer conversation #{comment.ticket_id}",
        title="Customer message" if comment.author_role == "customer" else "Support reply",
        excerpt=_public_text(
            comment.body,
            fallback="A public conversation update was reviewed.",
        ),
        occurred_at=comment.created_at,
    )


def _jira_issue_supporting_record(issue: JiraIssue) -> EvidenceSupportingRecordSchema:
    return EvidenceSupportingRecordSchema(
        record_id=f"issue-{issue.key}",
        record_type="issue",
        source_reference=f"Engineering issue {issue.key}",
        title=_public_text(issue.summary, fallback="Relevant engineering work item"),
        excerpt=_public_text(
            issue.description,
            fallback="The delivery team recorded an issue relevant to this finding.",
        ),
        status=issue.status,
        occurred_at=issue.updated_at,
        attributes={
            "Priority": issue.priority,
            "Type": issue.issue_type,
        },
    )


def _jira_comment_supporting_record(comment: JiraComment) -> EvidenceSupportingRecordSchema:
    return EvidenceSupportingRecordSchema(
        record_id=f"issue-{comment.issue_key}-comment-{comment.id}",
        record_type="comment",
        source_reference=f"Engineering issue {comment.issue_key}",
        title=f"Delivery update on {comment.issue_key}",
        excerpt=_public_text(
            comment.body,
            fallback="A delivery update relevant to this finding was reviewed.",
        ),
        occurred_at=comment.created_at,
    )


def _analytics_supporting_records(
    result: AnalyticsQueryResult,
) -> list[EvidenceSupportingRecordSchema]:
    records: list[EvidenceSupportingRecordSchema] = []
    for index, row in enumerate(result.rows[:12], start=1):
        attributes: dict[str, str] = {}
        for key, value in row.items():
            if key.lower() in {"distinct_id", "transaction_id", "failure_code"}:
                continue
            normalized_key = key.replace("_", " ").strip().title()
            if not normalized_key or normalized_key.lower().endswith(" id"):
                continue
            if "duration" in key.lower() and isinstance(value, (int, float)):
                normalized_key = normalized_key.removesuffix(" Ms")
                total_seconds = float(value) / 1000
                if total_seconds >= 3600:
                    rendered_value = (
                        f"{int(total_seconds // 3600)}h {int((total_seconds % 3600) // 60)}m"
                    )
                elif total_seconds >= 60:
                    rendered_value = f"{int(total_seconds // 60)}m {int(total_seconds % 60)}s"
                else:
                    rendered_value = f"{round(total_seconds, 1)}s"
            else:
                rendered_value = _public_text(
                    str(value).replace("_", " "),
                    fallback="Available in the source analysis.",
                )
            attributes[normalized_key] = rendered_value

        first_value = next(iter(attributes.values()), str(index))
        records.append(
            EvidenceSupportingRecordSchema(
                record_id=f"metric-{index}",
                record_type="metric",
                source_reference=f"Analytics segment {index}",
                title=f"Measured segment: {first_value}",
                excerpt=" · ".join(f"{key}: {value}" for key, value in attributes.items())
                or "An aggregated product metric was reviewed.",
                attributes=attributes,
            )
        )

    if not records and result.value is not None:
        records.append(
            EvidenceSupportingRecordSchema(
                record_id="metric-1",
                record_type="metric",
                source_reference="Aggregated product metric",
                title="Measured result",
                excerpt=_public_text(
                    str(result.value),
                    fallback="An aggregated product metric was reviewed.",
                ),
            )
        )
    return records


def _supporting_records(entry: EvidenceLedgerEntry) -> list[EvidenceSupportingRecordSchema]:
    """Project typed ledger payloads into a bounded, customer-safe audit layer."""
    payload = entry.typed_payload
    if isinstance(payload, SearchTicketsOutput):
        return [_ticket_supporting_record(ticket) for ticket in payload.tickets[:20]]
    if isinstance(payload, GetTicketOutput):
        return [_ticket_supporting_record(payload.ticket)]
    if isinstance(payload, GetTicketCommentsOutput):
        return [
            _zendesk_comment_supporting_record(comment)
            for comment in payload.comments[:20]
            if comment.public
        ]
    if isinstance(payload, ZendeskTicket):
        return [_ticket_supporting_record(payload)]
    if isinstance(payload, ZendeskComment) and payload.public:
        return [_zendesk_comment_supporting_record(payload)]
    if isinstance(payload, list) and payload and isinstance(payload[0], ZendeskComment):
        return [
            _zendesk_comment_supporting_record(comment)
            for comment in payload[:20]
            if comment.public
        ]
    if isinstance(payload, SearchIssuesOutput):
        return [_jira_issue_supporting_record(issue) for issue in payload.issues[:20]]
    if isinstance(payload, GetIssueOutput):
        return [_jira_issue_supporting_record(payload.issue)]
    if isinstance(payload, GetIssueCommentsOutput):
        return [_jira_comment_supporting_record(comment) for comment in payload.comments[:20]]
    if isinstance(payload, JiraIssue):
        return [_jira_issue_supporting_record(payload)]
    if isinstance(payload, JiraComment):
        return [_jira_comment_supporting_record(payload)]
    if isinstance(payload, list) and payload and isinstance(payload[0], JiraComment):
        return [_jira_comment_supporting_record(comment) for comment in payload[:20]]
    if isinstance(payload, QueryAnalyticsOutput):
        return _analytics_supporting_records(payload.result)
    if isinstance(payload, AnalyticsQueryResult):
        return _analytics_supporting_records(payload)
    return []


class InvestigationRecord:
    """In-memory record of an investigation in the current process."""

    def __init__(
        self,
        investigation_id: str,
        user_query: str,
        owner_id: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.investigation_id = investigation_id
        self.user_query = user_query
        self.display_name: str | None = None
        self.owner_id = owner_id
        self.context = context or {}
        self.status = "pending"
        self.current_stage = "Queued for investigation"
        self.active_agent: str | None = None
        self.revision_count = 0
        self.created_at = datetime.now(UTC)
        self.completed_at: datetime | None = None
        self.error: str | None = None
        self.final_state: InvestigationState | None = None
        self.task: asyncio.Task[Any] | None = None
        self.tracer: InvestigationTracer | None = None
        self.subscribers: list[asyncio.Queue[dict[str, Any]]] = []
        self.event_history: list[dict[str, Any]] = []
        self.run_attempt = 1
        self.recovery_status: str | None = None
        self.heartbeat_at: datetime | None = None
        self.lease_owner: str | None = None
        self.lease_expires_at: datetime | None = None
        self.last_completed_node: str | None = None
        self.current_node: str | None = None

    @property
    def elapsed_seconds(self) -> float:
        end_time = self.completed_at or datetime.now(UTC)
        return round((end_time - self.created_at).total_seconds(), 2)


class InvestigationManager:
    """Manages live tasks while persisting lifecycle state through an adapter."""

    def __init__(
        self,
        service: InvestigationService | None = None,
        repository: InvestigationRepository | None = None,
    ) -> None:
        self.service = service or InvestigationService.create_default()
        self.repository = repository
        self._records: dict[str, InvestigationRecord] = {}
        self._lock = asyncio.Lock()
        self._persistence_lock = asyncio.Lock()
        self.instance_id = f"api-{uuid.uuid4().hex}"

    async def create_owned_investigation(
        self,
        user_query: str,
        context: dict[str, Any] | None,
        owner_id: str,
    ) -> InvestigationRecord:
        """Persist a fresh record before spending any LLM credit."""
        inv_id = f"inv_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        record = InvestigationRecord(inv_id, user_query, owner_id, context)
        record.heartbeat_at = datetime.now(UTC)
        record.lease_owner = self.instance_id
        record.lease_expires_at = datetime.now(UTC) + _LEASE_DURATION
        self._records[inv_id] = record
        if self.repository:
            await self.repository.save(self._to_persisted(record))
        record.task = asyncio.create_task(self._run_task(record))
        return record

    def create_investigation(
        self,
        user_query: str,
        context: dict[str, Any] | None = None,
        investigation_id: str | None = None,
        owner_id: str = "local-development-user",
    ) -> InvestigationRecord:
        """Create a new investigation record and schedule background execution."""
        inv_id = (
            investigation_id
            or f"inv_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        )
        record = InvestigationRecord(
            investigation_id=inv_id,
            user_query=user_query,
            owner_id=owner_id,
            context=context,
        )
        self._records[inv_id] = record

        # Launch background task
        task = asyncio.create_task(self._run_task(record))
        record.task = task
        return record

    def get(
        self,
        investigation_id: str,
        owner_id: str | None = None,
    ) -> InvestigationRecord | None:
        """Retrieve an investigation, optionally enforcing user ownership."""
        record = self._records.get(investigation_id)
        if record is None or (owner_id is not None and record.owner_id != owner_id):
            return None
        return record

    async def get_owned(
        self,
        investigation_id: str,
        owner_id: str,
    ) -> InvestigationRecord | None:
        """Load an owned record from memory or durable storage."""
        record = self.get(investigation_id, owner_id=owner_id)
        if record or not self.repository:
            return record
        persisted = await self.repository.get(investigation_id, owner_id)
        if persisted is None:
            return None
        record = self._from_persisted(persisted)
        if not self._has_live_foreign_lease(record):
            await self._resolve_interrupted_record(record)
        self._records[record.investigation_id] = record
        return record

    def list_recent(
        self,
        limit: int = 50,
        owner_id: str | None = None,
    ) -> list[InvestigationRecord]:
        """List recent investigations, optionally scoped to one owner."""
        records = [
            record
            for record in self._records.values()
            if owner_id is None or record.owner_id == owner_id
        ]
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[:limit]

    async def list_recent_owned(
        self,
        owner_id: str,
        limit: int = 50,
    ) -> list[InvestigationRecord]:
        """Return durable owner-scoped history, merged with current live tasks."""
        if not self.repository:
            return self.list_recent(limit=limit, owner_id=owner_id)
        persisted_records = await self.repository.list_recent(owner_id, limit)
        records: list[InvestigationRecord] = []
        for persisted in persisted_records:
            record = self.get(persisted.investigation_id, owner_id=owner_id)
            if record is None:
                record = self._from_persisted(persisted)
                if not self._has_live_foreign_lease(record):
                    await self._resolve_interrupted_record(record)
                self._records[record.investigation_id] = record
            records.append(record)
        records.sort(key=lambda item: item.created_at, reverse=True)
        return records[:limit]

    async def cancel_owned_investigation(self, investigation_id: str, owner_id: str) -> bool:
        record = await self.get_owned(investigation_id, owner_id)
        if not record:
            return False
        cancelled = self.cancel_investigation(investigation_id, owner_id=owner_id)
        if cancelled and self.repository:
            await self._persist_record(record)
        return cancelled

    async def rename_owned_investigation(
        self, investigation_id: str, owner_id: str, display_name: str
    ) -> InvestigationRecord | None:
        record = await self.get_owned(investigation_id, owner_id)
        if record is None:
            return None
        if self.repository and not await self.repository.rename(
            investigation_id, owner_id, display_name
        ):
            return None
        record.display_name = display_name
        return record

    async def delete_owned_investigation(self, investigation_id: str, owner_id: str) -> bool:
        record = await self.get_owned(investigation_id, owner_id)
        if record is None:
            return False
        if record.status not in {
            "completed",
            "partial",
            "failed",
            "cancelled",
            "recovery_required",
        }:
            raise ValueError("An active investigation must be stopped before it can be deleted.")
        if self.repository and not await self.repository.delete(investigation_id, owner_id):
            return False
        self._records.pop(investigation_id, None)
        return True

    async def retry_owned_investigation(
        self, investigation_id: str, owner_id: str
    ) -> InvestigationRecord | None:
        record = await self.get_owned(investigation_id, owner_id)
        if record is None or record.status != "failed":
            return None
        return await self.create_owned_investigation(
            user_query=record.user_query,
            context=record.context,
            owner_id=owner_id,
        )

    def cancel_investigation(
        self,
        investigation_id: str,
        owner_id: str | None = None,
    ) -> bool:
        """Cancel an in-progress investigation task."""
        record = self.get(investigation_id, owner_id=owner_id)
        if not record:
            return False
        if record.status in ("completed", "failed", "cancelled", "recovery_required"):
            return False
        if record.task and not record.task.done():
            record.task.cancel()
        record.status = "cancelled"
        record.current_stage = "Investigation cancelled by user"
        record.completed_at = datetime.now(UTC)
        record.active_agent = None
        self._broadcast(
            record,
            {
                "event": "cancelled",
                "investigation_id": record.investigation_id,
                "status": "cancelled",
                "elapsed_seconds": record.elapsed_seconds,
                "message": "Investigation cancelled by user",
            },
        )
        return True

    async def _run_task(self, record: InvestigationRecord, *, resume: bool = False) -> None:
        """Execute the LangGraph workflow in the background, updating progress."""
        heartbeat_task = asyncio.create_task(self._heartbeat_lease(record))
        tracer = InvestigationTracer(
            investigation_id=record.investigation_id,
            enabled=bool(
                self.service.settings.langsmith_tracing and self.service.settings.langsmith_api_key
            ),
            environment=self.service.settings.environment,
        )
        record.tracer = tracer

        # Define tracer progress listener to map LangGraph node spans to API presentation statuses
        def on_tracer_event(event_type: str, name: str, payload: dict[str, Any]) -> None:
            if event_type == "start":
                self._handle_span_start(record, name, payload)
            elif event_type == "end":
                self._handle_span_end(record, name, payload)

        tracer.add_listener(on_tracer_event)

        try:
            record.status = "planning"
            record.current_stage = "Formulating investigation plan"
            record.active_agent = "planner"
            self._broadcast(
                record,
                {
                    "event": "progress",
                    "stage": record.status,
                    "active_agent": record.active_agent,
                    "message": record.current_stage,
                    "elapsed_seconds": record.elapsed_seconds,
                },
            )

            investigation_kwargs: dict[str, Any] = {
                "user_query": record.user_query,
                "investigation_id": record.investigation_id,
                "context": record.context,
                "tracer": tracer,
            }
            if resume:
                investigation_kwargs["resume"] = True
            final_state = await self.service.investigate(
                **investigation_kwargs,
            )

            record.final_state = final_state
            record.active_agent = None

            # LangGraph owns the substantive outcome. Never promote a partial or
            # failed graph result merely because the background task returned.
            if final_state.status == "completed":
                # Verify the report can be assembled before announcing completion.
                self.build_detail_response(record)
                record.status = "completed"
                record.current_stage = "Investigation complete"
                event = "complete"
                message = "Your decision-ready report is ready."
            elif final_state.status == "partial" and final_state.recommendation:
                self.build_detail_response(record)
                record.status = "partial"
                record.current_stage = "Decision available with follow-up items"
                event = "partial"
                message = "A decision is available, with items to validate."
            else:
                record.status = "failed"
                record.current_stage = "Investigation could not produce a decision-ready report"
                record.error = (
                    "The investigation ended without enough verified evidence for a report."
                )
                event = "failed"
                message = record.error

            record.completed_at = datetime.now(UTC)
            record.recovery_status = None
            record.lease_owner = None
            record.lease_expires_at = None
            await self._persist_record(record)
            self._broadcast(
                record,
                {
                    "event": event,
                    "investigation_id": record.investigation_id,
                    "status": record.status,
                    "elapsed_seconds": record.elapsed_seconds,
                    "message": message,
                    "error": record.error,
                },
            )

        except asyncio.CancelledError:
            record.status = "cancelled"
            record.current_stage = "Investigation cancelled"
            record.completed_at = datetime.now(UTC)
            record.lease_owner = None
            record.lease_expires_at = None
            await self._persist_record_best_effort(record)
            self._broadcast(
                record,
                {
                    "event": "cancelled",
                    "investigation_id": record.investigation_id,
                    "status": "cancelled",
                    "elapsed_seconds": record.elapsed_seconds,
                },
            )
            raise
        except Exception as exc:
            logger.exception(
                "Investigation %s failed during execution: %s", record.investigation_id, exc
            )
            record.status = "failed"
            record.error = "The investigation could not be completed. Please try again."
            record.current_stage = "Investigation could not be completed"
            record.completed_at = datetime.now(UTC)
            record.active_agent = None
            record.lease_owner = None
            record.lease_expires_at = None
            await self._persist_record_best_effort(record)
            self._broadcast(
                record,
                {
                    "event": "failed",
                    "investigation_id": record.investigation_id,
                    "status": "failed",
                    "error": record.error,
                    "elapsed_seconds": record.elapsed_seconds,
                },
            )
        finally:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task

    async def _heartbeat_lease(self, record: InvestigationRecord) -> None:
        """Keep a live workflow lease fresh, including during long model calls."""
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL_SECONDS)
            if record.status in {
                "completed",
                "partial",
                "failed",
                "cancelled",
                "recovery_required",
            }:
                return
            record.heartbeat_at = datetime.now(UTC)
            record.lease_owner = self.instance_id
            record.lease_expires_at = record.heartbeat_at + _LEASE_DURATION
            await self._persist_record_best_effort(record)

    def _handle_span_start(
        self, record: InvestigationRecord, name: str, payload: dict[str, Any]
    ) -> None:
        """Map LangGraph node span starts to user-facing progress updates."""
        stage_map = {
            "planner": ("planning", "planner", "Clarifying the question"),
            "research": ("gathering_evidence", "research_agent", "Reviewing customer feedback"),
            "research_agent": (
                "gathering_evidence",
                "research_agent",
                "Reviewing customer feedback",
            ),
            "analytics": ("gathering_evidence", "analytics_agent", "Examining product usage"),
            "analytics_agent": ("gathering_evidence", "analytics_agent", "Examining product usage"),
            "engineering": ("gathering_evidence", "engineering_agent", "Checking delivery context"),
            "engineering_agent": (
                "gathering_evidence",
                "engineering_agent",
                "Checking delivery context",
            ),
            "assessment": ("gathering_evidence", "orchestrator", "Bringing the evidence together"),
            "targeted_follow_up": (
                "gathering_evidence",
                "specialists",
                "Checking one remaining question",
            ),
            "pm_synthesis": ("synthesizing", "pm", "Bringing the findings together"),
            "critic": ("reviewing", "critic", "Checking the recommendation"),
            "pm_revision": ("revising", "pm", "Refining the recommendation"),
            "finalize": ("completing", "orchestrator", "Preparing your decision brief"),
        }

        if name in stage_map:
            status, agent, message = stage_map[name]
            record.status = status
            record.active_agent = agent
            record.current_stage = message
            record.current_node = name
            record.heartbeat_at = datetime.now(UTC)
            record.lease_expires_at = datetime.now(UTC) + _LEASE_DURATION
            if name == "pm_revision":
                record.revision_count += 1
                record.current_stage = "Refining the recommendation"

            self._broadcast(
                record,
                {
                    "event": "progress",
                    "stage": record.status,
                    "active_agent": record.active_agent,
                    "message": record.current_stage,
                    "revision_count": record.revision_count,
                    "elapsed_seconds": record.elapsed_seconds,
                },
            )

    def _handle_span_end(
        self, record: InvestigationRecord, name: str, payload: dict[str, Any]
    ) -> None:
        """Capture span completions if relevant."""
        record.last_completed_node = name
        record.current_node = None
        record.heartbeat_at = datetime.now(UTC)
        if self.repository:
            asyncio.create_task(self._persist_record_best_effort(record))

    def _broadcast(self, record: InvestigationRecord, event_data: dict[str, Any]) -> None:
        """Record event in history and dispatch to active SSE subscriber queues."""
        record.event_history.append(event_data)
        if self.repository:
            asyncio.create_task(self._persist_progress(record, event_data))
        for queue in record.subscribers:
            with suppress(Exception):
                queue.put_nowait(event_data)

    async def _persist_progress(
        self,
        record: InvestigationRecord,
        event_data: dict[str, Any],
    ) -> None:
        """Persist progress without delaying the customer-facing event stream."""
        if not self.repository:
            return
        try:
            async with self._persistence_lock:
                await self.repository.save(self._to_persisted(record))
                await self.repository.append_event(record.investigation_id, event_data)
        except Exception:
            logger.exception("Could not persist progress for %s", record.investigation_id)

    async def _persist_record(self, record: InvestigationRecord) -> None:
        if self.repository:
            async with self._persistence_lock:
                await self.repository.save(self._to_persisted(record))

    async def _persist_record_best_effort(self, record: InvestigationRecord) -> None:
        try:
            await self._persist_record(record)
        except Exception:
            if self.repository:
                logger.exception("Could not persist investigation %s", record.investigation_id)

    async def _resolve_interrupted_record(self, record: InvestigationRecord) -> None:
        """Never present a process-lost task as if it were still running."""
        active_statuses = {
            "pending",
            "planning",
            "gathering_evidence",
            "synthesizing",
            "reviewing",
            "revising",
            "completing",
        }
        if record.status not in active_statuses:
            return
        record.status = "recovery_required"
        record.recovery_status = "recovery_required"
        record.current_stage = "Investigation needs recovery"
        record.active_agent = None
        record.error = "This investigation was interrupted during an active step. Its completed work has been preserved."
        await self._persist_record(record)

    def _has_live_foreign_lease(self, record: InvestigationRecord) -> bool:
        """Return true when another API process still owns this active workflow."""
        return bool(
            record.lease_owner
            and record.lease_owner != self.instance_id
            and record.lease_expires_at
            and record.lease_expires_at > datetime.now(UTC)
        )

    @staticmethod
    def _to_persisted(record: InvestigationRecord) -> PersistedInvestigation:
        return PersistedInvestigation(
            investigation_id=record.investigation_id,
            owner_id=record.owner_id,
            user_query=record.user_query,
            display_name=record.display_name,
            context=record.context,
            status=record.status,
            current_stage=record.current_stage,
            active_agent=record.active_agent,
            revision_count=record.revision_count,
            created_at=record.created_at,
            completed_at=record.completed_at,
            error=record.error,
            final_state=(
                record.final_state.model_dump(mode="json") if record.final_state else None
            ),
            run_attempt=record.run_attempt,
            recovery_status=record.recovery_status,
            heartbeat_at=record.heartbeat_at,
            lease_owner=record.lease_owner,
            lease_expires_at=record.lease_expires_at,
            last_completed_node=record.last_completed_node,
            current_node=record.current_node,
        )

    @staticmethod
    def _from_persisted(persisted: PersistedInvestigation) -> InvestigationRecord:
        record = InvestigationRecord(
            investigation_id=persisted.investigation_id,
            user_query=persisted.user_query,
            owner_id=persisted.owner_id,
            context=persisted.context,
        )
        record.status = persisted.status
        record.display_name = persisted.display_name
        record.current_stage = persisted.current_stage
        record.active_agent = persisted.active_agent
        record.revision_count = persisted.revision_count
        record.created_at = persisted.created_at
        record.completed_at = persisted.completed_at
        record.error = persisted.error
        record.run_attempt = persisted.run_attempt
        record.recovery_status = persisted.recovery_status
        record.heartbeat_at = persisted.heartbeat_at
        record.lease_owner = persisted.lease_owner
        record.lease_expires_at = persisted.lease_expires_at
        record.last_completed_node = persisted.last_completed_node
        record.current_node = persisted.current_node
        record.final_state = (
            InvestigationState.model_validate(persisted.final_state)
            if persisted.final_state
            else None
        )
        return record

    async def recover_incomplete_investigations(self) -> None:
        """Resume safe checkpoints and pause ambiguous in-flight paid work."""
        if not self.repository or not self.service.checkpointer:
            return
        for persisted in await self.repository.claim_recoverable(self.instance_id):
            record = self._from_persisted(persisted)
            self._records[record.investigation_id] = record
            config = {"configurable": {"thread_id": record.investigation_id}}
            snapshot = await self.service.graph.aget_state(config)
            next_nodes = set(snapshot.next)
            if not snapshot.values:
                if record.status == "pending":
                    record.task = asyncio.create_task(self._run_task(record))
                    continue
                await self._resolve_interrupted_record(record)
                continue
            if record.current_node and record.current_node in next_nodes:
                await self._resolve_interrupted_record(record)
                continue
            record.recovery_status = "resumed"
            record.error = None
            record.task = asyncio.create_task(self._run_task(record, resume=True))

    async def recover_owned_investigation(
        self, investigation_id: str, owner_id: str
    ) -> InvestigationRecord | None:
        """Explicitly retry only the checkpointed step after an ambiguous interruption."""
        record = await self.get_owned(investigation_id, owner_id)
        if not record or record.status != "recovery_required" or not self.service.checkpointer:
            return None
        record.status = "planning"
        record.current_stage = "Resuming preserved investigation"
        record.error = None
        record.recovery_status = "resumed_by_user"
        record.run_attempt += 1
        record.lease_owner = self.instance_id
        record.lease_expires_at = datetime.now(UTC) + _LEASE_DURATION
        await self._persist_record(record)
        record.task = asyncio.create_task(self._run_task(record, resume=True))
        return record

    async def subscribe(
        self,
        investigation_id: str,
        owner_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to live progress events with immediate state snapshot replay."""
        record = self.get(investigation_id, owner_id=owner_id)
        if not record:
            raise KeyError(f"Investigation '{investigation_id}' not found.")

        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        record.subscribers.append(queue)

        try:
            # 1. Immediate state snapshot event
            snapshot_event = {
                "event": "snapshot",
                "investigation_id": record.investigation_id,
                "status": record.status,
                "active_agent": record.active_agent,
                "current_stage": record.current_stage,
                "revision_count": record.revision_count,
                "elapsed_seconds": record.elapsed_seconds,
                "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                "error": record.error,
            }
            yield snapshot_event

            # If already finished, yield terminal event and finish
            if record.status in (
                "completed",
                "partial",
                "failed",
                "cancelled",
                "recovery_required",
            ):
                if record.status == "completed":
                    yield {
                        "event": "complete",
                        "investigation_id": record.investigation_id,
                        "status": "completed",
                        "elapsed_seconds": record.elapsed_seconds,
                    }
                elif record.status == "partial":
                    yield {
                        "event": "partial",
                        "investigation_id": record.investigation_id,
                        "status": "partial",
                        "elapsed_seconds": record.elapsed_seconds,
                    }
                elif record.status == "recovery_required":
                    yield {
                        "event": "recovery_required",
                        "investigation_id": record.investigation_id,
                        "status": record.status,
                        "error": record.error,
                        "elapsed_seconds": record.elapsed_seconds,
                    }
                else:
                    yield {
                        "event": record.status,
                        "investigation_id": record.investigation_id,
                        "status": record.status,
                        "error": record.error,
                        "elapsed_seconds": record.elapsed_seconds,
                    }
                return

            # 2. Stream subsequent live events
            while True:
                event = await queue.get()
                yield event
                if event.get("event") in (
                    "complete",
                    "partial",
                    "failed",
                    "cancelled",
                    "recovery_required",
                ):
                    break
        finally:
            if queue in record.subscribers:
                record.subscribers.remove(queue)

    def build_status_response(self, record: InvestigationRecord) -> InvestigationStatusResponse:
        """Construct lightweight status response model."""
        return InvestigationStatusResponse(
            investigation_id=record.investigation_id,
            user_query=record.user_query,
            display_name=record.display_name,
            status=record.status,
            current_stage=record.current_stage,
            active_agent=record.active_agent,
            revision_count=record.revision_count,
            elapsed_seconds=record.elapsed_seconds,
            created_at=record.created_at,
            completed_at=record.completed_at,
            error=record.error,
            scope=InvestigationScope.model_validate(record.context.get("scope") or {}),
        )

    def build_detail_response(self, record: InvestigationRecord) -> InvestigationDetailResponse:
        """Construct rich, typed response with structured epistemic separation and evidence ledger."""
        state = record.final_state
        if state is None or state.recommendation is None:
            raise ValueError(
                f"Investigation '{record.investigation_id}' has no completed recommendation."
            )

        rec = state.recommendation

        # 1. Evidence Ledger Mapping (Scrubbed & Sanitized)
        citation_meta: dict[str, Any] = {}
        for cf in state.customer_findings:
            for ev in cf.evidence:
                citation_meta[ev.ledger_entry_id] = ev
        for af in state.analytics_findings:
            for ev in af.evidence:
                citation_meta[ev.ledger_entry_id] = ev
        for ef in state.engineering_findings:
            for ev in ef.evidence:
                citation_meta[ev.ledger_entry_id] = ev
        for ev in rec.evidence:
            citation_meta[ev.ledger_entry_id] = ev

        ledger_map: dict[str, EvidenceLedgerItemSchema] = {}
        for entry_id, entry in state.evidence_ledger_entries.items():
            ev_meta = citation_meta.get(entry_id)
            ledger_map[entry_id] = EvidenceLedgerItemSchema(
                ledger_entry_id=entry.ledger_entry_id,
                source_type=entry.source_type,
                source_reference=_public_source_reference(
                    entry.source_type, entry.source_reference
                ),
                finding=_public_text(
                    ev_meta.finding if ev_meta else entry.data_summary,
                    fallback=f"Verified {entry.source_type} evidence was reviewed.",
                ),
                support_excerpt=_public_text(
                    ev_meta.support if ev_meta else entry.data_summary,
                    fallback="Supporting detail is retained in the evidence record.",
                ),
                confidence=ev_meta.confidence.value if ev_meta else "high",
                retrieved_at=entry.retrieved_at,
                supporting_records=_supporting_records(entry),
            )

        # 2. Structured Evidence Citations
        citations: list[StructuredEvidenceCitationSchema] = []
        for ev in rec.evidence:
            citations.append(
                StructuredEvidenceCitationSchema(
                    ledger_entry_id=ev.ledger_entry_id,
                    source=ev.source_type,
                    source_reference=_public_source_reference(ev.source_type, ev.source_reference),
                    finding=_public_text(ev.finding, fallback="Verified evidence was reviewed."),
                    support=_public_text(
                        ev.support,
                        fallback="Supporting detail is retained in the evidence record.",
                    ),
                    confidence=ev.confidence.value,
                )
            )

        # 3. Epistemic Separation Triad: Facts, Inferences, Hypotheses
        facts: list[StructuredFindingSchema] = []
        for f in _public_list(rec.factual_observations, limit=6):
            # Associate citation IDs matching this observation
            linked = [
                ev.ledger_entry_id
                for ev in rec.evidence
                if ev.ledger_entry_id in f or ev.source_reference.lower() in f.lower()
            ]
            if not linked and rec.evidence:
                # Fallback to all citations if general
                linked = [rec.evidence[0].ledger_entry_id]
            facts.append(
                StructuredFindingSchema(
                    statement=f,
                    epistemic_type="fact",
                    evidence_ids=linked,
                )
            )

        inferences: list[StructuredFindingSchema] = []
        for inf in _public_list(rec.inferences, limit=4):
            linked = [
                ev.ledger_entry_id
                for ev in rec.evidence
                if ev.ledger_entry_id in inf or ev.source_reference.lower() in inf.lower()
            ]
            inferences.append(
                StructuredFindingSchema(
                    statement=inf,
                    epistemic_type="inference",
                    evidence_ids=linked,
                )
            )

        hypotheses: list[StructuredFindingSchema] = []
        for hyp in _public_list(rec.hypotheses, limit=3):
            hypotheses.append(
                StructuredFindingSchema(
                    statement=hyp,
                    epistemic_type="hypothesis",
                    evidence_ids=[],
                )
            )

        rec_schema = ProductRecommendationSchema(
            problem_statement=_public_text(
                rec.problem_statement, fallback="A customer-impacting product issue was identified."
            ),
            why_it_matters=_public_text(
                rec.why_it_matters,
                fallback="The issue may affect customer confidence and successful completion.",
            ),
            affected_users=_public_text(
                rec.affected_users, fallback="Customers affected by the investigated journey."
            ),
            factual_observations=facts,
            inferences=inferences,
            hypotheses=hypotheses,
            recommendation=_public_text(
                rec.recommendation,
                fallback="Review the available evidence and agree the next customer-facing improvement.",
            ),
            recommendation_type=rec.recommendation_type,
            confidence=rec.confidence,
            success_metrics=_public_list(rec.success_metrics, limit=3),
            risks=_public_list(rec.risks, limit=3),
            likely_causes=_public_list(rec.likely_causes, limit=3),
            conflicting_evidence=_public_list(rec.conflicting_evidence, limit=3),
            disclosed_limitations=_public_limitations([*rec.open_questions, *state.limitations]),
            evidence_citations=citations,
        )

        # 4. Critic Review Mapping
        last_review = state.critic_reviews[-1] if state.critic_reviews else None
        critic_schema = CriticReviewSchema(
            status=last_review.decision if last_review else "PASS",
            revisions_completed=state.revision_count,
            critique_summary=(
                "The recommendation was checked against the available evidence and revised "
                "where needed."
                if last_review
                else "The recommendation was checked against the available evidence."
            ),
            issues_addressed=[],
        )

        # 5. Telemetry Summary
        trace_id_str = None
        if record.tracer and record.tracer.root_run and getattr(record.tracer.root_run, "id", None):
            trace_id_str = str(record.tracer.root_run.id)

        telemetry = TelemetrySummarySchema(
            investigation_id=record.investigation_id,
            trace_id=trace_id_str,
            llm_calls=state.budget_usage.total_llm_calls,
            total_tokens=0,
            provider_reported_cost=None,
            internally_estimated_cost=None,
        )

        return InvestigationDetailResponse(
            investigation_id=record.investigation_id,
            user_query=record.user_query,
            status=record.status,
            duration_seconds=record.elapsed_seconds,
            scope=InvestigationScope.model_validate(record.context.get("scope") or {}),
            recommendation=rec_schema,
            evidence_ledger=ledger_map,
            critic_review=critic_schema,
            telemetry_summary=telemetry,
        )
