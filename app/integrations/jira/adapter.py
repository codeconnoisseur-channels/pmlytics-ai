"""High-level application adapter for Jira Cloud REST API v3 integration.

Provides a typed, read-only interface for searching issues, retrieving individual
issues, and retrieving issue comments. Normalizes Atlassian Document Format (ADF)
comments into plain text strings, supports modern nextPageToken-based cursor
pagination on POST /rest/api/3/search/jql, and parses both inward and outward
linked issues.
"""

import logging
from datetime import datetime
from typing import Any, cast

from pydantic import BaseModel

from app.domain.jira import (
    IssuePriority,
    IssueStatus,
    IssueType,
    JiraComment,
    JiraIssue,
    JiraIssueLink,
    LinkType,
)
from app.integrations.jira.client import JiraClient
from app.integrations.jira.exceptions import JiraResponseError

logger = logging.getLogger(__name__)


class JiraSearchResult(BaseModel):
    """Container for paginated search results from Jira Cloud REST v3."""

    issues: list[JiraIssue]
    total: int
    next_page_token: str | None = None
    is_last: bool = True


class JiraAdapter:
    """Read-only application adapter connecting Pocket services to Jira Cloud REST v3."""

    def __init__(self, client: JiraClient) -> None:
        self.client = client

    async def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        next_page_token: str | None = None,
    ) -> JiraSearchResult:
        """Execute JQL search using Jira Cloud REST v3 enhanced search API."""
        payload: dict[str, Any] = {
            "jql": jql,
            "maxResults": max_results,
            "fields": [
                "summary",
                "description",
                "issuetype",
                "status",
                "priority",
                "components",
                "created",
                "updated",
                "issuelinks",
                "comment",
            ],
        }
        if next_page_token:
            payload["nextPageToken"] = next_page_token

        data = await self.client.post("rest/api/3/search/jql", json_data=payload)

        raw_issues = data.get("issues", [])
        next_token = data.get("nextPageToken")
        is_last = data.get("isLast", next_token is None)
        total = data.get("total", len(raw_issues))

        issues: list[JiraIssue] = []
        for raw in raw_issues:
            issues.append(self._parse_issue(raw))

        return JiraSearchResult(
            issues=issues,
            total=total,
            next_page_token=next_token,
            is_last=is_last,
        )

    async def get_issue(self, issue_id_or_key: str) -> JiraIssue:
        """Retrieve a single Jira issue by key (e.g. 'PAY-117') or numeric ID."""
        data = await self.client.get(f"rest/api/3/issue/{issue_id_or_key}")
        if not data or "key" not in data:
            raise JiraResponseError(
                f"Jira response for {issue_id_or_key} did not contain valid issue payload"
            )

        # Also retrieve comments if not embedded or empty
        comments = await self.get_issue_comments(issue_id_or_key)
        return self._parse_issue(data, comments=comments)

    async def get_issue_comments(self, issue_id_or_key: str) -> list[JiraComment]:
        """Retrieve conversation comments on an issue and normalize ADF to plain text."""
        data = await self.client.get(f"rest/api/3/issue/{issue_id_or_key}/comment")
        raw_comments = data.get("comments", [])

        comments: list[JiraComment] = []
        for c in raw_comments:
            comments.append(self._parse_comment(c, default_key=str(issue_id_or_key)))
        return comments

    async def get_linked_issues(self, issue_id_or_key: str) -> list[JiraIssueLink]:
        """Application convenience method returning parsed issue links from get_issue()."""
        issue = await self.get_issue(issue_id_or_key)
        return issue.issuelinks

    def _parse_issue(
        self,
        raw: dict[str, Any],
        comments: list[JiraComment] | None = None,
    ) -> JiraIssue:
        """Parse raw Jira v3 JSON issue into JiraIssue domain entity."""
        try:
            fields = raw.get("fields", {})
            issue_key = str(raw.get("key", ""))

            # Map IssueType
            type_name = fields.get("issuetype", {}).get("name", "Bug")
            issue_type: IssueType = (
                cast(IssueType, type_name)
                if type_name in ("Bug", "Task", "Story", "Incident")
                else "Bug"
            )

            # Map IssueStatus
            status_name = fields.get("status", {}).get("name", "To Do")
            status: IssueStatus = (
                cast(IssueStatus, status_name)
                if status_name in ("To Do", "In Progress", "Blocked", "Done")
                else "To Do"
            )

            # Map IssuePriority
            priority_name = fields.get("priority", {}).get("name", "Medium")
            priority: IssuePriority = (
                cast(IssuePriority, priority_name)
                if priority_name in ("Low", "Medium", "High", "Critical")
                else "Medium"
            )

            components = [
                comp.get("name", "")
                for comp in fields.get("components", [])
                if isinstance(comp, dict)
            ]

            created_at = self._parse_iso_datetime(fields.get("created"))
            updated_at = self._parse_iso_datetime(fields.get("updated")) or created_at

            # Extract issue links
            raw_links = fields.get("issuelinks", [])
            issuelinks = self._parse_issue_links(raw_links, current_key=issue_key)

            # Extract description (may be ADF or plain string)
            desc_raw = fields.get("description")
            description_text = self._extract_text(desc_raw)

            # Use passed comments or extract from fields.comment if present
            final_comments = comments or []
            if not final_comments and "comment" in fields:
                for c in fields["comment"].get("comments", []):
                    final_comments.append(self._parse_comment(c, default_key=issue_key))

            raw_id = raw.get("id")
            num_id = int(raw_id) if (raw_id and str(raw_id).isdigit()) else 10001

            return JiraIssue(
                id=num_id,
                key=issue_key,
                summary=str(fields.get("summary", "")),
                description=description_text,
                issue_type=issue_type,
                status=status,
                priority=priority,
                components=components,
                created_at=created_at,
                updated_at=updated_at,
                comments=final_comments,
                issuelinks=issuelinks,
            )
        except Exception as exc:
            logger.error("Failed to parse JiraIssue: %s", exc)
            raise JiraResponseError(f"Failed to parse Jira issue payload: {exc}") from exc

    def _parse_comment(self, raw: dict[str, Any], default_key: str) -> JiraComment:
        """Parse raw comment JSON, normalizing Atlassian Document Format (ADF) to plain text."""
        try:
            body_raw = raw.get("body")
            body_text = self._extract_text(body_raw)

            author = raw.get("author", {})
            author_str = (
                author.get("displayName")
                or author.get("name")
                or author.get("accountId")
                or "Unknown Engineer"
            )

            created_at = self._parse_iso_datetime(raw.get("created"))
            comm_id = str(raw.get("id", "1"))

            return JiraComment(
                id=comm_id,
                issue_key=default_key,
                author=str(author_str),
                body=body_text,
                created_at=created_at,
            )
        except Exception as exc:
            logger.error("Failed to parse JiraComment: %s", exc)
            raise JiraResponseError(f"Failed to parse Jira comment payload: {exc}") from exc

    def _parse_issue_links(
        self, raw_links: list[dict[str, Any]], current_key: str
    ) -> list[JiraIssueLink]:
        """Parse Jira v3 issuelinks handling both inwardIssue and outwardIssue."""
        links: list[JiraIssueLink] = []
        for lk in raw_links:
            link_id = str(lk.get("id", "link_01"))
            link_type_info = lk.get("type", {})
            inward_desc = link_type_info.get("inward", "relates to").lower()
            outward_desc = link_type_info.get("outward", "relates to").lower()

            rel: LinkType = "relates to"
            if "block" in inward_desc or "block" in outward_desc:
                rel = "blocks" if "blocks" in outward_desc else "is blocked by"
            elif "duplicate" in inward_desc or "duplicate" in outward_desc:
                rel = "duplicates"

            # Handle outward link (current -> target)
            if "outwardIssue" in lk:
                target_key = lk["outwardIssue"].get("key")
                if target_key:
                    links.append(
                        JiraIssueLink(
                            id=link_id,
                            inward_key=current_key,
                            outward_key=target_key,
                            relationship=rel,
                        )
                    )
            # Handle inward link (source -> current)
            elif "inwardIssue" in lk:
                source_key = lk["inwardIssue"].get("key")
                if source_key:
                    links.append(
                        JiraIssueLink(
                            id=link_id,
                            inward_key=source_key,
                            outward_key=current_key,
                            relationship=rel,
                        )
                    )
        return links

    @classmethod
    def _extract_text(cls, raw_content: Any) -> str:
        """Recursively extract plain text from Atlassian Document Format (ADF) or strings."""
        if isinstance(raw_content, str):
            return raw_content
        if not isinstance(raw_content, dict):
            return ""

        # ADF root or node: traverse content array
        extracted_chunks: list[str] = []
        cls._walk_adf(raw_content, extracted_chunks)
        return "\n".join(chunk.strip() for chunk in extracted_chunks if chunk.strip())

    @classmethod
    def _walk_adf(cls, node: dict[str, Any], chunks: list[str]) -> None:
        """Walk ADF tree nodes collecting text."""
        node_type = node.get("type")
        if node_type == "text":
            text_val = node.get("text", "")
            if text_val:
                chunks.append(text_val)

        for child in node.get("content", []):
            if isinstance(child, dict):
                cls._walk_adf(child, chunks)

    @staticmethod
    def _parse_iso_datetime(dt_val: Any) -> datetime:
        """Parse ISO timestamp or return current datetime fallback."""
        if isinstance(dt_val, datetime):
            return dt_val
        if isinstance(dt_val, str):
            try:
                clean_dt = dt_val.replace("Z", "+00:00")
                return datetime.fromisoformat(clean_dt)
            except ValueError:
                pass
        from datetime import UTC

        return datetime.now(UTC)
