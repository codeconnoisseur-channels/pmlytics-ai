"""Referential integrity validation across entities."""

from app.domain.analytics import AnalyticsEvent
from app.domain.jira import JiraIssue, JiraIssueLink
from app.domain.transactions import Transaction
from app.domain.users import User
from app.domain.zendesk import ZendeskComment, ZendeskTicket


class ReferentialIntegrityError(ValueError):
    """Raised when an entity references a non-existent parent entity."""


def validate_referential_integrity(
    users: list[User],
    transactions: list[Transaction],
    events: list[AnalyticsEvent],
    tickets: list[ZendeskTicket],
    issues: list[JiraIssue],
    issue_links: list[JiraIssueLink],
) -> None:
    """Validate foreign keys and entity cross-references."""
    user_ids = {u.user_id for u in users}
    ticket_ids = {t.id for t in tickets}
    issue_keys = {i.key for i in issues}

    # 1. Transaction user references
    for txn in transactions:
        if txn.user_id not in user_ids:
            raise ReferentialIntegrityError(
                f"Transaction {txn.transaction_id} references unknown user_id: {txn.user_id}"
            )

    # 2. Analytics event user references
    for evt in events:
        if evt.distinct_id not in user_ids:
            raise ReferentialIntegrityError(
                f"Analytics event '{evt.event}' references unknown distinct_id: {evt.distinct_id}"
            )

    # 3. Zendesk ticket requester references
    for ticket in tickets:
        if ticket.requester_id not in user_ids:
            raise ReferentialIntegrityError(
                f"Ticket #{ticket.id} references unknown requester_id: {ticket.requester_id}"
            )
        # Check embedded comments
        for comment in ticket.comments:
            if comment.ticket_id != ticket.id and comment.ticket_id not in ticket_ids:
                raise ReferentialIntegrityError(
                    f"Comment #{comment.id} references non-existent ticket_id: {comment.ticket_id}"
                )

    # 4. Jira issue links
    for link in issue_links:
        if link.inward_key not in issue_keys:
            raise ReferentialIntegrityError(
                f"Issue link references unknown inward_key: {link.inward_key}"
            )
        if link.outward_key not in issue_keys:
            raise ReferentialIntegrityError(
                f"Issue link references unknown outward_key: {link.outward_key}"
            )


def validate_ticket_comments(tickets: list[ZendeskTicket], comments: list[ZendeskComment]) -> None:
    """Validate that standalone comments reference valid tickets."""
    ticket_ids = {t.id for t in tickets}
    for c in comments:
        if c.ticket_id not in ticket_ids:
            raise ReferentialIntegrityError(
                f"Comment #{c.id} references non-existent ticket_id: {c.ticket_id}"
            )
