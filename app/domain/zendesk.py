"""Zendesk customer support domain models and enums."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TicketStatus = Literal["new", "open", "pending", "solved", "closed"]
TicketPriority = Literal["low", "normal", "high", "urgent"]
TicketChannel = Literal["email", "web", "chat"]


class ZendeskComment(BaseModel):
    """A comment thread entry associated with a support ticket."""

    id: int = Field(..., gt=0)
    ticket_id: int = Field(..., gt=0)
    author_id: str
    body: str
    created_at: datetime
    public: bool = True
    author_role: Literal["customer", "agent"] = Field(
        default="customer",
        description="Author role: 'customer' if requester, 'agent' if support staff",
    )


class ZendeskTicket(BaseModel):
    """Operational entity representing a customer support ticket."""

    id: int = Field(..., gt=0)
    requester_id: str = Field(..., pattern=r"^usr_[a-z0-9]{6}$")
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    channel: TicketChannel
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    comments: list[ZendeskComment] = Field(default_factory=list)
