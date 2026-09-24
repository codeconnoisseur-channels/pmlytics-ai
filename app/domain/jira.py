"""Jira engineering issue domain models and enums."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

IssueType = Literal["Bug", "Task", "Story", "Incident"]
IssueStatus = Literal["To Do", "In Progress", "Blocked", "Done"]
IssuePriority = Literal["Low", "Medium", "High", "Critical"]
LinkType = Literal["blocks", "is blocked by", "relates to", "duplicates"]


class JiraComment(BaseModel):
    """An engineering comment associated with a Jira issue."""

    id: str
    issue_key: str = Field(..., pattern=r"^[A-Z]+-[0-9]+$")
    author: str
    body: str
    created_at: datetime


class JiraIssueLink(BaseModel):
    """A directional link between two Jira issues."""

    id: str
    inward_key: str = Field(..., pattern=r"^[A-Z]+-[0-9]+$")
    outward_key: str = Field(..., pattern=r"^[A-Z]+-[0-9]+$")
    relationship: LinkType


class JiraIssue(BaseModel):
    """Operational entity representing an engineering issue."""

    id: int = Field(..., gt=0)
    key: str = Field(..., pattern=r"^[A-Z]+-[0-9]+$")
    summary: str
    description: str
    issue_type: IssueType
    status: IssueStatus
    priority: IssuePriority
    components: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    comments: list[JiraComment] = Field(default_factory=list)
    issuelinks: list[JiraIssueLink] = Field(default_factory=list)
