"""Zendesk integration package."""

from app.integrations.zendesk.adapter import ZendeskAdapter, ZendeskSearchResult
from app.integrations.zendesk.client import ZendeskClient
from app.integrations.zendesk.exceptions import (
    ZendeskAuthError,
    ZendeskConnectionError,
    ZendeskError,
    ZendeskHttpError,
    ZendeskNotFoundError,
    ZendeskResponseError,
    ZendeskTimeoutError,
)

__all__ = [
    "ZendeskAdapter",
    "ZendeskSearchResult",
    "ZendeskClient",
    "ZendeskError",
    "ZendeskConnectionError",
    "ZendeskTimeoutError",
    "ZendeskAuthError",
    "ZendeskNotFoundError",
    "ZendeskHttpError",
    "ZendeskResponseError",
]
