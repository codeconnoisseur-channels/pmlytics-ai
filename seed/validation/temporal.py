"""Temporal integrity validation supporting scenario-specific sequencing."""

from datetime import datetime

from app.domain.jira import JiraIssue
from app.domain.zendesk import ZendeskComment, ZendeskTicket

from seed.scenarios.schema import InjectionTimeline


class TemporalIntegrityError(ValueError):
    """Raised when an entity violates chronological ordering or scenario timeline sequencing."""


def validate_lifecycle_timestamps(
    tickets: list[ZendeskTicket],
    issues: list[JiraIssue],
    comments: list[ZendeskComment] | None = None,
) -> None:
    """Validate internal chronological order for tickets, issues, and comments."""
    for ticket in tickets:
        if ticket.created_at > ticket.updated_at:
            raise TemporalIntegrityError(
                f"Ticket #{ticket.id} has created_at ({ticket.created_at}) after updated_at ({ticket.updated_at})"
            )
        for comment in ticket.comments:
            if comment.created_at < ticket.created_at:
                raise TemporalIntegrityError(
                    f"Comment #{comment.id} has created_at ({comment.created_at}) before ticket created_at ({ticket.created_at})"
                )

    if comments:
        ticket_map = {t.id: t.created_at for t in tickets}
        for comment in comments:
            t_created = ticket_map.get(comment.ticket_id)
            if t_created and comment.created_at < t_created:
                raise TemporalIntegrityError(
                    f"Standalone comment #{comment.id} precedes parent ticket created_at"
                )

    for issue in issues:
        if issue.created_at > issue.updated_at:
            raise TemporalIntegrityError(
                f"Jira issue {issue.key} has created_at ({issue.created_at}) after updated_at ({issue.updated_at})"
            )
        for j_comment in issue.comments:
            if j_comment.created_at < issue.created_at:
                raise TemporalIntegrityError(
                    f"Comment #{j_comment.id} has created_at before issue created_at"
                )


def validate_scenario_timeline_sequencing(
    timeline: InjectionTimeline,
    jira_created_at: datetime | None,
    analytics_first_observed: datetime | None,
    first_ticket_created_at: datetime | None,
) -> None:
    """Validate that cross-system timestamps follow scenario-defined sequential offsets.

    Example:
        Jira incident logged -> PostHog degradation begins -> Zendesk complaints appear
    """
    # Verify timeline offset ordering declared in seed config
    if timeline.jira_logged_offset_hours > timeline.ticket_spike_offset_hours:
        raise TemporalIntegrityError(
            f"Scenario timeline specifies ticket surge ({timeline.ticket_spike_offset_hours}h) "
            f"before Jira logging ({timeline.jira_logged_offset_hours}h)"
        )

    # When actual entity timestamps are provided, verify sequential chronological order
    if (
        jira_created_at
        and first_ticket_created_at
        and timeline.jira_logged_offset_hours <= timeline.ticket_spike_offset_hours
        and first_ticket_created_at < jira_created_at
    ):
        raise TemporalIntegrityError(
            f"Customer tickets ({first_ticket_created_at}) began before the engineering "
            f"incident occurred ({jira_created_at})"
        )

    if (
        analytics_first_observed
        and first_ticket_created_at
        and timeline.analytics_degradation_offset_hours <= timeline.ticket_spike_offset_hours
        and first_ticket_created_at < analytics_first_observed
    ):
        raise TemporalIntegrityError(
            f"Customer complaints ({first_ticket_created_at}) surfaced before the behavioral "
            f"degradation appeared ({analytics_first_observed})"
        )
