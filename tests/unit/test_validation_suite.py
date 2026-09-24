"""Unit tests for synthetic data validation suite."""

from datetime import UTC, datetime, timedelta

import pytest
from app.domain.analytics import AnalyticsEvent
from app.domain.jira import JiraIssue, JiraIssueLink
from app.domain.transactions import Transaction
from app.domain.users import User
from app.domain.zendesk import ZendeskTicket
from seed.scenarios.schema import InjectionTimeline
from seed.validation.pii import (
    PIIValidationError,
    validate_identifier_format,
    validate_text_for_pii,
)
from seed.validation.referential import (
    ReferentialIntegrityError,
    validate_referential_integrity,
)
from seed.validation.temporal import (
    TemporalIntegrityError,
    validate_lifecycle_timestamps,
    validate_scenario_timeline_sequencing,
)


@pytest.fixture
def sample_user() -> User:
    return User(
        user_id="usr_01428a",
        user_type="student",
        primary_bank="Bank A",
        app_version="2.4.1",
        signup_date=datetime.now(UTC),
    )


def test_referential_validation_success(sample_user: User) -> None:
    """Verify referential integrity succeeds when all relationships resolve."""
    now = datetime.now(UTC)
    txn = Transaction(
        transaction_id="txn_003827",
        user_id=sample_user.user_id,
        amount_ngn=5000,
        amount_bracket="<10k",
        transaction_type="transfer",
        destination_bank="Bank A",
        app_version="2.4.1",
        timestamp=now,
        status="completed",
    )
    evt = AnalyticsEvent(
        distinct_id=sample_user.user_id,
        event="transfer_completed",
        timestamp=now,
        properties={"transaction_id": txn.transaction_id},
    )
    ticket = ZendeskTicket(
        id=101,
        requester_id=sample_user.user_id,
        subject="Issue with transfer",
        description="Help please",
        status="new",
        priority="normal",
        channel="web",
        created_at=now,
        updated_at=now,
    )
    issue1 = JiraIssue(
        id=1,
        key="PAY-101",
        summary="Service bug",
        description="Stack trace info",
        issue_type="Bug",
        status="In Progress",
        priority="Medium",
        created_at=now,
        updated_at=now,
    )
    issue2 = JiraIssue(
        id=2,
        key="PAY-102",
        summary="Upstream error",
        description="Details",
        issue_type="Bug",
        status="To Do",
        priority="Medium",
        created_at=now,
        updated_at=now,
    )
    link = JiraIssueLink(
        id="l1",
        inward_key="PAY-101",
        outward_key="PAY-102",
        relationship="relates to",
    )

    validate_referential_integrity(
        users=[sample_user],
        transactions=[txn],
        events=[evt],
        tickets=[ticket],
        issues=[issue1, issue2],
        issue_links=[link],
    )


def test_referential_validation_fails_on_orphan_transaction() -> None:
    """Verify referential integrity catches transactions referencing non-existent users."""
    now = datetime.now(UTC)
    txn = Transaction(
        transaction_id="txn_003827",
        user_id="usr_999999",  # Non-existent user
        amount_ngn=5000,
        amount_bracket="<10k",
        transaction_type="transfer",
        destination_bank="Bank A",
        app_version="2.4.1",
        timestamp=now,
        status="completed",
    )
    with pytest.raises(ReferentialIntegrityError, match="references unknown user_id"):
        validate_referential_integrity(
            users=[],
            transactions=[txn],
            events=[],
            tickets=[],
            issues=[],
            issue_links=[],
        )


def test_temporal_validation_lifecycle() -> None:
    """Verify temporal validation detects inverted created_at / updated_at."""
    t0 = datetime.now(UTC)
    t1 = t0 - timedelta(hours=1)  # Invalid: updated_at before created_at

    ticket = ZendeskTicket(
        id=101,
        requester_id="usr_01428a",
        subject="Test",
        description="Desc",
        status="new",
        priority="normal",
        channel="web",
        created_at=t0,
        updated_at=t1,
    )
    with pytest.raises(TemporalIntegrityError, match="created_at .* after updated_at"):
        validate_lifecycle_timestamps(tickets=[ticket], issues=[])


def test_temporal_scenario_sequencing() -> None:
    """Verify scenario timeline validation detects tickets preceding the incident."""
    timeline = InjectionTimeline(
        start_time_iso="2026-08-10T08:00:00Z",
        end_time_iso="2026-08-15T20:00:00Z",
        jira_logged_offset_hours=1.0,
        analytics_degradation_offset_hours=2.0,
        ticket_spike_offset_hours=4.0,
    )

    t0 = datetime(2026, 8, 10, 8, 0, 0, tzinfo=UTC)
    t_jira = t0 + timedelta(hours=1)
    t_analytics = t0 + timedelta(hours=2)
    t_ticket_valid = t0 + timedelta(hours=4)
    t_ticket_invalid = t0 + timedelta(minutes=30)  # Invalid: precedes Jira incident

    # Valid sequencing
    validate_scenario_timeline_sequencing(
        timeline,
        jira_created_at=t_jira,
        analytics_first_observed=t_analytics,
        first_ticket_created_at=t_ticket_valid,
    )

    # Invalid sequencing: tickets surge before incident
    with pytest.raises(TemporalIntegrityError, match="began before the engineering incident"):
        validate_scenario_timeline_sequencing(
            timeline,
            jira_created_at=t_jira,
            analytics_first_observed=t_analytics,
            first_ticket_created_at=t_ticket_invalid,
        )


def test_pii_validation_clean() -> None:
    """Verify clean synthetic text passes PII validation."""
    validate_text_for_pii(
        "User usr_01428a contacted support@pocket.test regarding transfer txn_003827."
    )
    validate_identifier_format("usr_01428a", "usr")
    validate_identifier_format("txn_003827", "txn")


def test_pii_validation_detects_credit_card() -> None:
    """Verify raw payment card number pattern is rejected."""
    with pytest.raises(PIIValidationError, match="Potential raw credit card number"):
        validate_text_for_pii("Customer provided card number: 4111 2222 3333 4444")


def test_pii_validation_detects_real_email() -> None:
    """Verify non-synthetic email domain is rejected."""
    with pytest.raises(PIIValidationError, match="Real or unapproved email domain"):
        validate_text_for_pii("Sent receipt to realuser@gmail.com")
