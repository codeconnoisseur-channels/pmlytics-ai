"""Unit tests for JiraAdapter, ADF normalization, cursor pagination, and error mappings."""

import httpx
import pytest
import respx
from app.domain.jira import JiraComment, JiraIssue
from app.integrations.jira.adapter import JiraAdapter
from app.integrations.jira.client import JiraClient
from app.integrations.jira.exceptions import (
    JiraAuthError,
    JiraConnectionError,
    JiraNotFoundError,
    JiraResponseError,
    JiraTimeoutError,
)
from mocks.jira.expectations import make_adf_body

BASE_URL = "http://mock-jira.test"


@pytest.fixture
def jira_adapter() -> JiraAdapter:
    """Create JiraAdapter instance pointing to mock base URL."""
    client = JiraClient(
        base_url=BASE_URL,
        username="mock-jira@pocket.test",
        api_token="test-api-token",
        timeout_seconds=1.0,
    )
    return JiraAdapter(client)


@pytest.mark.asyncio
async def test_search_issues_modern_pagination(jira_adapter: JiraAdapter) -> None:
    """Verify search_issues sends JQL request and parses issues with nextPageToken."""
    mock_response = {
        "issues": [
            {
                "id": "10117",
                "key": "PAY-117",
                "fields": {
                    "summary": "Intermittent webhook callback delays on partner switch",
                    "description": "Downstream switch API accepts transactions with 202 Accepted...",
                    "issuetype": {"name": "Bug"},
                    "status": {"name": "In Progress"},
                    "priority": {"name": "High"},
                    "components": [{"name": "transfer-gateway"}],
                    "created": "2026-08-10T09:00:00.000Z",
                    "updated": "2026-08-10T11:30:00.000Z",
                    "issuelinks": [
                        {
                            "id": "link_101",
                            "type": {
                                "name": "Relates",
                                "inward": "relates to",
                                "outward": "relates to",
                            },
                            "outwardIssue": {"key": "PAY-110"},
                        }
                    ],
                },
            }
        ],
        "nextPageToken": "token_page_2",
        "isLast": False,
        "total": 1,
    }

    with respx.mock(base_url=BASE_URL) as respx_mock:
        route = respx_mock.post("/rest/api/3/search/jql").respond(
            json=mock_response, status_code=200
        )

        result = await jira_adapter.search_issues("project = PAY", max_results=25)
        assert route.called
        assert result.total == 1
        assert result.next_page_token == "token_page_2"
        assert not result.is_last
        assert len(result.issues) == 1

        issue = result.issues[0]
        assert isinstance(issue, JiraIssue)
        assert issue.key == "PAY-117"
        assert issue.status == "In Progress"
        assert len(issue.issuelinks) == 1
        assert issue.issuelinks[0].outward_key == "PAY-110"


@pytest.mark.asyncio
async def test_get_issue_and_adf_comment_normalization(jira_adapter: JiraAdapter) -> None:
    """Verify get_issue and get_issue_comments cleanly normalizes ADF comments to plain text."""
    issue_payload = {
        "id": "10117",
        "key": "PAY-117",
        "fields": {
            "summary": "Partner switch callback timeouts",
            "description": make_adf_body(["First description paragraph.", "Second paragraph."]),
            "issuetype": {"name": "Bug"},
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "created": "2026-08-10T09:00:00.000Z",
            "updated": "2026-08-10T11:30:00.000Z",
            "issuelinks": [
                {
                    "id": "link_99",
                    "type": {"name": "Relates", "inward": "relates to", "outward": "relates to"},
                    "inwardIssue": {"key": "PAY-100"},
                }
            ],
        },
    }

    comments_payload = {
        "comments": [
            {
                "id": "comm_101",
                "author": {"displayName": "Tunde Bakare"},
                "body": make_adf_body(
                    [
                        "Queue congestion detected on NIP partner switch.",
                        "Transactions settle eventually, but callbacks lag by hours.",
                    ]
                ),
                "created": "2026-08-10T10:15:00.000Z",
            }
        ],
        "total": 1,
    }

    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/rest/api/3/issue/PAY-117").respond(json=issue_payload, status_code=200)
        respx_mock.get("/rest/api/3/issue/PAY-117/comment").respond(
            json=comments_payload, status_code=200
        )

        issue = await jira_adapter.get_issue("PAY-117")
        assert issue.key == "PAY-117"
        assert "First description paragraph." in issue.description
        assert "Second paragraph." in issue.description

        # Check comment extraction
        assert len(issue.comments) == 1
        comment = issue.comments[0]
        assert isinstance(comment, JiraComment)
        assert comment.author == "Tunde Bakare"
        assert "Queue congestion detected" in comment.body
        assert "callbacks lag by hours" in comment.body

        # Check inward issue link parsing
        assert len(issue.issuelinks) == 1
        link = issue.issuelinks[0]
        assert link.inward_key == "PAY-100"
        assert link.outward_key == "PAY-117"

        # Check get_linked_issues application convenience method
        links = await jira_adapter.get_linked_issues("PAY-117")
        assert len(links) == 1
        assert links[0].inward_key == "PAY-100"


@pytest.mark.asyncio
async def test_jira_adapter_raises_not_found(jira_adapter: JiraAdapter) -> None:
    """Verify HTTP 404 is mapped to JiraNotFoundError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/rest/api/3/issue/UNKNOWN-999").respond(status_code=404)

        with pytest.raises(JiraNotFoundError):
            await jira_adapter.get_issue("UNKNOWN-999")


@pytest.mark.asyncio
async def test_jira_adapter_raises_auth_error(jira_adapter: JiraAdapter) -> None:
    """Verify HTTP 401/403 is mapped to JiraAuthError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.post("/rest/api/3/search/jql").respond(status_code=401)

        with pytest.raises(JiraAuthError):
            await jira_adapter.search_issues("project = PAY")


@pytest.mark.asyncio
async def test_jira_adapter_raises_timeout_error(jira_adapter: JiraAdapter) -> None:
    """Verify request timeout is mapped to JiraTimeoutError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.post("/rest/api/3/search/jql").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        with pytest.raises(JiraTimeoutError):
            await jira_adapter.search_issues("project = PAY")


@pytest.mark.asyncio
async def test_jira_adapter_raises_connection_error(jira_adapter: JiraAdapter) -> None:
    """Verify connect error is mapped to JiraConnectionError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.post("/rest/api/3/search/jql").mock(side_effect=httpx.ConnectError("Refused"))

        with pytest.raises(JiraConnectionError):
            await jira_adapter.search_issues("project = PAY")


@pytest.mark.asyncio
async def test_jira_adapter_raises_response_error_on_malformed_json(
    jira_adapter: JiraAdapter,
) -> None:
    """Verify malformed JSON or schema failure is mapped to JiraResponseError."""
    with respx.mock(base_url=BASE_URL) as respx_mock:
        respx_mock.get("/rest/api/3/issue/PAY-117").respond(text="not valid json", status_code=200)

        with pytest.raises(JiraResponseError):
            await jira_adapter.get_issue("PAY-117")
