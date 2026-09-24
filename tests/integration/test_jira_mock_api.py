"""End-to-end live HTTP integration tests for MockServer 7.6.0 and JiraAdapter.

Exercises the full chain:
JiraAdapter -> actual HTTP wire -> MockServer 7.6.0 (running in Docker) -> typed app.domain.jira objects.
"""

import pytest
from app.domain.jira import JiraComment, JiraIssue
from app.integrations.jira.adapter import JiraAdapter
from app.integrations.jira.client import JiraClient
from app.integrations.jira.exceptions import JiraNotFoundError


@pytest.mark.asyncio
async def test_jira_mock_api_end_to_end(mock_jira_server: str) -> None:
    """Verify live HTTP communication, search/jql, get_issue, and comments against MockServer 7.6.0."""
    client = JiraClient(
        base_url=mock_jira_server,
        username="mock-jira@pocket.test",
        api_token="mock-jira-token-pocket",
        timeout_seconds=5.0,
    )
    adapter = JiraAdapter(client)

    # 1. Test single issue retrieval: PAY-117
    issue = await adapter.get_issue("PAY-117")
    assert isinstance(issue, JiraIssue)
    assert issue.key == "PAY-117"
    assert issue.status == "In Progress"
    assert issue.priority == "High"
    assert "Intermittent webhook callback delays" in issue.summary
    assert "Downstream switch API accepts transactions" in issue.description

    # 2. Verify ADF comment normalization to plain text
    assert len(issue.comments) >= 2
    first_comm = issue.comments[0]
    assert isinstance(first_comm, JiraComment)
    assert first_comm.author == "Tunde Bakare"
    assert "queue congestion on their NIP gateway" in first_comm.body
    assert "callbacks are delayed by 2-4 hours" in first_comm.body

    # 3. Verify issue links parsing from fields.issuelinks
    assert len(issue.issuelinks) >= 1
    link = issue.issuelinks[0]
    assert link.inward_key == "PAY-117"
    assert link.outward_key == "PAY-110"
    assert link.relationship == "relates to"

    # 4. Verify get_linked_issues convenience method
    links = await adapter.get_linked_issues("PAY-117")
    assert len(links) >= 1
    assert links[0].outward_key == "PAY-110"

    # 5. Test JQL search via enhanced POST /rest/api/3/search/jql
    search_res = await adapter.search_issues("project = PAY")
    assert search_res.total >= 3
    assert search_res.is_last
    assert any(i.key == "PAY-117" for i in search_res.issues)
    assert any(i.key == "CORE-82" for i in search_res.issues)
    assert any(i.key == "PAY-134" for i in search_res.issues)

    # 6. Verify 404 behavior over live HTTP wire
    with pytest.raises(JiraNotFoundError):
        await adapter.get_issue("UNKNOWN-999")
