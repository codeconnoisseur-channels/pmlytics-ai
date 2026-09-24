"""Mock Zendesk package."""

from mocks.zendesk.compat_handler import PocketZendeskCompatHandler, reset_mock_stores
from mocks.zendesk.server import MockZendeskServer

__all__ = ["PocketZendeskCompatHandler", "MockZendeskServer", "reset_mock_stores"]
