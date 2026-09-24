"""Global pytest configuration and fixtures."""

import pytest
from app.config.settings import Settings

pytest_plugins = ["tests.fixtures.mock_zendesk", "tests.fixtures.mock_jira"]


@pytest.fixture
def default_settings() -> Settings:
    """Fixture providing clean default application settings."""
    return Settings(
        environment="test",
        openrouter_api_key="test-key",
    )
