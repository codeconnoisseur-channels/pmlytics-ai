"""Invariant tests verifying that evidence compaction preserves all substantive evidence."""

import json
from datetime import datetime

from app.agents.base import compact_tool_payload_for_context
from app.domain.analytics import AnalyticsQueryResult
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.jira import JiraComment, JiraIssue, JiraIssueLink
from app.domain.specialists import (
    AnalyticsFinding,
    CustomerFinding,
    EngineeringFinding,
)
from app.domain.zendesk import ZendeskComment, ZendeskTicket
from app.tools.analytics import QueryAnalyticsOutput
from app.tools.engineering import (
    GetIssueOutput,
    SearchIssuesOutput,
)
from app.tools.support import (
    GetTicketOutput,
    SearchTicketsOutput,
)


def test_zendesk_search_compaction_preserves_substantive_evidence() -> None:
    """Invariant: Zendesk search results compaction must retain IDs, subjects, descriptions, and statuses."""
    ticket = ZendeskTicket(
        id=101,
        requester_id="usr_abc123",
        subject="Surge in transfer failures",
        description="I tried to transfer 50,000 NGN to GTBank and it failed with timeout error.",
        status="open",
        priority="high",
        channel="email",
        tags=["transfer_failure", "gtbank"],
        created_at=datetime(2026, 9, 15, 10, 0),
        updated_at=datetime(2026, 9, 15, 11, 0),
    )
    raw_output = SearchTicketsOutput(
        tickets=[ticket],
        total_count=1,
        page=1,
    )

    compacted_str = compact_tool_payload_for_context("search_tickets", raw_output)
    compacted = json.loads(compacted_str)

    assert compacted["total_count"] == 1
    assert len(compacted["tickets"]) == 1
    t = compacted["tickets"][0]
    assert t["id"] == 101
    assert t["subject"] == "Surge in transfer failures"
    assert "failed with timeout error" in t["description"]
    assert t["status"] == "open"
    assert t["priority"] == "high"
    assert "gtbank" in t["tags"]

    # Invariant: information suffices to substantiate CustomerFinding
    cf = CustomerFinding(
        finding="Customers report transfer failures to GTBank",
        facts=[f"Ticket #{t['id']}: {t['subject']}"],
        observed_pattern=t["subject"],
        interpretations=["Transfer failures concentrated on specific destination bank"],
        evidence=[
            Evidence(
                ledger_entry_id="led_support_001",
                source_type="zendesk",
                source_reference=f"ticket:{t['id']}",
                finding=t["subject"],
                support=t["description"],
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
    )
    assert cf.evidence[0].source_reference == "ticket:101"
    assert len(cf.facts) == 1


def test_zendesk_ticket_and_comments_compaction_preserves_details() -> None:
    """Invariant: Zendesk ticket comments compaction retains comment text and author role."""
    comment = ZendeskComment(
        id=501,
        ticket_id=101,
        author_id="usr_abc123",
        body="Still not working after 3 retries.",
        created_at=datetime(2026, 9, 15, 12, 0),
        public=True,
        author_role="customer",
    )
    ticket = ZendeskTicket(
        id=101,
        requester_id="usr_abc123",
        subject="Failed transfer",
        description="Transfer timeout",
        status="open",
        priority="normal",
        channel="chat",
        created_at=datetime(2026, 9, 15, 10, 0),
        updated_at=datetime(2026, 9, 15, 12, 0),
        comments=[comment],
    )
    compacted_str = compact_tool_payload_for_context("get_ticket", GetTicketOutput(ticket=ticket))
    compacted = json.loads(compacted_str)

    assert compacted["id"] == 101
    assert compacted["requester_id"] == "usr_abc123"
    assert len(compacted["comments"]) == 1
    assert compacted["comments"][0]["body"] == "Still not working after 3 retries."
    assert compacted["comments"][0]["author_role"] == "customer"


def test_jira_issues_compaction_preserves_substantive_evidence() -> None:
    """Invariant: Jira issue search compaction retains keys, summaries, statuses, and context."""
    issue = JiraIssue(
        id=1001,
        key="PAY-117",
        summary="Payment processor timeout on GTBank webhook callbacks",
        description="Upstream partner GTBank is experiencing latency spikes causing HTTP 504 gateway timeouts.",
        status="In Progress",
        priority="High",
        issue_type="Bug",
        created_at=datetime(2026, 9, 14, 8, 30),
        updated_at=datetime(2026, 9, 15, 9, 0),
        comments=[
            JiraComment(
                id="comm_1",
                issue_key="PAY-117",
                author="eng_lead",
                body="Mitigation deployed to increase timeout threshold to 30s.",
                created_at=datetime(2026, 9, 15, 9, 15),
            )
        ],
        issuelinks=[
            JiraIssueLink(
                id="link_1",
                inward_key="PAY-117",
                outward_key="CORE-82",
                relationship="relates to",
            )
        ],
    )
    raw_output = SearchIssuesOutput(
        issues=[issue],
        next_page_token=None,
        total_returned=1,
    )

    compacted_str = compact_tool_payload_for_context("search_issues", raw_output)
    compacted = json.loads(compacted_str)

    assert compacted["total_returned"] == 1
    assert len(compacted["issues"]) == 1
    iss = compacted["issues"][0]
    assert iss["key"] == "PAY-117"
    assert "GTBank webhook" in iss["summary"]
    assert iss["status"] == "In Progress"
    assert iss["priority"] == "High"
    assert "latency spikes" in iss["description"]

    # Invariant: information suffices to substantiate EngineeringFinding
    ef = EngineeringFinding(
        finding="Active bug PAY-117 indicates partner webhook timeouts",
        facts=[f"Issue {iss['key']} status is {iss['status']}"],
        issue_status=iss["status"],
        technical_context=iss["description"],
        relationship_to_problem="contributing_factor",
        interpretations=["Technical timeouts match customer complaints"],
        evidence=[
            Evidence(
                ledger_entry_id="led_jira_001",
                source_type="jira",
                source_reference=f"issue:{iss['key']}",
                finding=iss["summary"],
                support=iss["description"],
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
    )
    assert ef.evidence[0].source_reference == "issue:PAY-117"
    assert len(ef.facts) == 1


def test_jira_single_issue_compaction_preserves_comments_and_links() -> None:
    """Invariant: GetIssue compaction preserves comments and linked issue keys."""
    issue = JiraIssue(
        id=1001,
        key="PAY-117",
        summary="Payment processor timeout",
        description="Timeout issues",
        status="In Progress",
        priority="High",
        issue_type="Bug",
        created_at=datetime(2026, 9, 14, 8, 30),
        updated_at=datetime(2026, 9, 15, 9, 0),
        comments=[
            JiraComment(
                id="comm_1",
                issue_key="PAY-117",
                author="eng_lead",
                body="Mitigation deployed",
                created_at=datetime(2026, 9, 15, 9, 15),
            )
        ],
        issuelinks=[
            JiraIssueLink(
                id="link_1",
                inward_key="PAY-117",
                outward_key="CORE-82",
                relationship="relates to",
            )
        ],
    )
    compacted_str = compact_tool_payload_for_context("get_issue", GetIssueOutput(issue=issue))
    compacted = json.loads(compacted_str)

    assert compacted["key"] == "PAY-117"
    assert len(compacted["comments"]) == 1
    assert compacted["comments"][0]["body"] == "Mitigation deployed"


def test_analytics_compaction_preserves_substantive_evidence() -> None:
    """Invariant: Analytics compaction preserves metric, values, dimensions, and rows."""
    query_res = AnalyticsQueryResult(
        query_description="Transfer failure rate broken down by destination bank",
        metric="failure_rate",
        value=0.184,
        dimensions=["destination_bank"],
        rows=[
            {"destination_bank": "GTBank", "total": 1200, "failed": 450, "rate": 0.375},
            {"destination_bank": "Zenith", "total": 1500, "failed": 45, "rate": 0.030},
        ],
        time_range="last_7_days",
        raw_count=2700,
        limitations=["Only includes completed and failed states"],
    )
    raw_output = QueryAnalyticsOutput(result=query_res)

    compacted_str = compact_tool_payload_for_context("query_analytics", raw_output)
    compacted = json.loads(compacted_str)

    assert compacted["metric"] == "failure_rate"
    assert compacted["value"] == 0.184
    assert compacted["dimensions"] == ["destination_bank"]
    assert len(compacted["rows"]) == 2
    assert compacted["rows"][0]["destination_bank"] == "GTBank"
    assert compacted["rows"][0]["rate"] == 0.375
    assert compacted["raw_count"] == 2700
    assert len(compacted["limitations"]) == 1

    # Invariant: information suffices to substantiate AnalyticsFinding
    af = AnalyticsFinding(
        finding="GTBank destination transfer failure rate spiked to 37.5%",
        facts=[f"Failure rate for GTBank is {compacted['rows'][0]['rate']}"],
        metric=compacted["metric"],
        value=str(compacted["value"]),
        comparison="Baseline across other banks is ~3.0%",
        interpretations=["Failures are isolated to GTBank transactions"],
        evidence=[
            Evidence(
                ledger_entry_id="led_posthog_001",
                source_type="posthog",
                source_reference="query:transfer_failure_rate",
                finding=f"Failure rate: {compacted['value']}",
                support=f"GTBank failure rate: {compacted['rows'][0]['rate']}",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
    )
    assert af.metric == "failure_rate"
    assert af.value == "0.184"
    assert len(af.facts) == 1
