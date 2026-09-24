"""Unit tests for operational domain models."""

from datetime import UTC, datetime

import pytest
from app.domain.analytics import AnalyticsEvent, EventName
from app.domain.jira import JiraComment, JiraIssue, JiraIssueLink
from app.domain.transactions import Transaction
from app.domain.users import User
from app.domain.zendesk import ZendeskComment, ZendeskTicket
from pydantic import ValidationError


def test_user_model_valid() -> None:
    """Verify valid User instantiation."""
    user = User(
        user_id="usr_01428a",
        user_type="student",
        primary_bank="Bank A",
        app_version="2.4.1",
        signup_date=datetime.now(UTC),
    )
    assert user.user_id == "usr_01428a"
    assert user.user_type == "student"
    assert user.primary_bank == "Bank A"


def test_user_model_invalid_id() -> None:
    """Verify User rejects invalid ID formats."""
    with pytest.raises(ValidationError):
        User(
            user_id="invalid_id",
            user_type="student",
            primary_bank="Bank A",
            app_version="2.4.1",
            signup_date=datetime.now(UTC),
        )


def test_transaction_transfer_model_valid() -> None:
    """Verify valid transfer Transaction instantiation."""
    txn = Transaction(
        transaction_id="txn_003827",
        user_id="usr_01428a",
        amount_ngn=75000,
        amount_bracket="50k-200k",
        transaction_type="transfer",
        destination_bank="Bank A",
        app_version="2.4.1",
        timestamp=datetime.now(UTC),
        status="processing",
    )
    assert txn.transaction_id == "txn_003827"
    assert txn.destination_bank == "Bank A"
    assert txn.status == "processing"


def test_transaction_transfer_missing_destination_bank() -> None:
    """Verify transfer rejects missing destination_bank."""
    with pytest.raises(
        ValidationError, match="Transfer transactions must specify destination_bank"
    ):
        Transaction(
            transaction_id="txn_003827",
            user_id="usr_01428a",
            amount_ngn=75000,
            amount_bracket="50k-200k",
            transaction_type="transfer",
            destination_bank=None,
            app_version="2.4.1",
            timestamp=datetime.now(UTC),
            status="completed",
        )


def test_transaction_bracket_mismatch() -> None:
    """Verify transaction rejects amount bracket mismatch."""
    with pytest.raises(ValidationError, match="corresponds to bracket '<10k'"):
        Transaction(
            transaction_id="txn_003827",
            user_id="usr_01428a",
            amount_ngn=5000,
            amount_bracket=">=200k",  # Mismatched bracket
            transaction_type="transfer",
            destination_bank="Bank B",
            app_version="2.4.1",
            timestamp=datetime.now(UTC),
            status="completed",
        )


def test_analytics_event_valid() -> None:
    """Verify valid AnalyticsEvent instantiation."""
    evt = AnalyticsEvent(
        distinct_id="usr_01428a",
        event="transfer_submitted",
        timestamp=datetime.now(UTC),
        properties={
            "transaction_id": "txn_003827",
            "amount_ngn": 75000,
            "destination_bank": "Bank A",
            "app_version": "2.4.1",
        },
    )
    assert evt.event == "transfer_submitted"
    assert evt.properties["destination_bank"] == "Bank A"


def test_analytics_event_taxonomy_complete() -> None:
    """Verify all 18 events across Account, Transfers, KYC, Wallet, and Bills instantiate."""
    now = datetime.now(UTC)
    all_events: list[EventName] = [
        # Account
        "signup_completed",
        "login_completed",
        # Transfers
        "transfer_started",
        "transfer_recipient_selected",
        "transfer_reviewed",
        "transfer_submitted",
        "transfer_processing",
        "transfer_completed",
        "transfer_failed",
        "transfer_cancelled",
        # KYC
        "kyc_started",
        "kyc_document_submitted",
        "kyc_completed",
        "kyc_failed",
        # Wallet
        "wallet_funding_started",
        "wallet_funding_submitted",
        "wallet_funding_completed",
        "wallet_funding_failed",
        # Bill Payments
        "bill_payment_started",
        "bill_payment_submitted",
        "bill_payment_completed",
        "bill_payment_failed",
    ]
    for ev in all_events:
        event_obj = AnalyticsEvent(
            distinct_id="usr_01428a",
            event=ev,
            timestamp=now,
            properties={"app_version": "2.4.1"},
        )
        assert event_obj.event == ev


def test_zendesk_ticket_and_comment_valid() -> None:
    """Verify valid ZendeskTicket with embedded comment."""
    now = datetime.now(UTC)
    comment = ZendeskComment(
        id=501,
        ticket_id=1047,
        author_id="usr_01428a",
        body="My transfer is still pending after 3 hours",
        created_at=now,
    )
    ticket = ZendeskTicket(
        id=1047,
        requester_id="usr_01428a",
        subject="Transfer pending",
        description="I sent money to Bank A and it is stuck",
        status="open",
        priority="high",
        channel="web",
        tags=["transfer", "bank_a", "delay"],
        created_at=now,
        updated_at=now,
        comments=[comment],
    )
    assert ticket.id == 1047
    assert len(ticket.comments) == 1
    assert ticket.comments[0].ticket_id == 1047


def test_jira_issue_and_link_valid() -> None:
    """Verify valid JiraIssue and JiraIssueLink."""
    now = datetime.now(UTC)
    j_comment = JiraComment(
        id="comm_01",
        issue_key="PAY-117",
        author="eng_tunde",
        body="Callback queue worker latency exceeds 45s",
        created_at=now,
    )
    link = JiraIssueLink(
        id="link_01",
        inward_key="PAY-117",
        outward_key="PAY-110",
        relationship="relates to",
    )
    issue = JiraIssue(
        id=10117,
        key="PAY-117",
        summary="Webhook callback timeouts on partner switch",
        description="Detailed technical description without evaluative conclusions.",
        issue_type="Bug",
        status="In Progress",
        priority="High",
        components=["transfer-gateway"],
        created_at=now,
        updated_at=now,
        comments=[j_comment],
        issuelinks=[link],
    )
    assert issue.key == "PAY-117"
    assert len(issue.comments) == 1
    assert len(issue.issuelinks) == 1
