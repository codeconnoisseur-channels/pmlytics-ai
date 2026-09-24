"""Unit tests verifying model resolution and role-based configuration without hardcoding."""

from unittest.mock import MagicMock

import pytest
from app.agents.analytics import AnalyticsAgent
from app.agents.engineering import EngineeringAgent
from app.agents.research import ResearchAgent
from app.config.settings import get_model_for_role, get_settings


def test_get_model_for_role_default_when_no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify get_model_for_role falls back to default_model when no override exists."""
    get_settings.cache_clear()
    monkeypatch.setenv("INVESTIGATION_PROFILE", "deep")
    monkeypatch.delenv("RESEARCH_MODEL", raising=False)
    monkeypatch.delenv("ANALYTICS_MODEL", raising=False)
    monkeypatch.delenv("ENGINEERING_MODEL", raising=False)
    monkeypatch.delenv("DEFAULT_MODEL", raising=False)

    model = get_model_for_role("research")
    assert model == "openai/gpt-5.4"


def test_get_model_for_role_role_specific_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify get_model_for_role uses role-specific model override when present."""
    get_settings.cache_clear()
    monkeypatch.setenv("INVESTIGATION_PROFILE", "deep")
    monkeypatch.setenv("RESEARCH_MODEL", "anthropic/claude-sonnet-4.6")
    monkeypatch.setenv("DEFAULT_MODEL", "openai/gpt-5.4")

    research_model = get_model_for_role("research")
    analytics_model = get_model_for_role("analytics")

    assert research_model == "anthropic/claude-sonnet-4.6"
    assert analytics_model == "openai/gpt-5.4"
    get_settings.cache_clear()


def test_agents_do_not_hardcode_model_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify specialist agents resolve model dynamically from config without hardcoded strings."""
    get_settings.cache_clear()
    custom_model = "anthropic/claude-sonnet-4.6"
    monkeypatch.setenv("RESEARCH_MODEL", custom_model)
    monkeypatch.setenv("ANALYTICS_MODEL", custom_model)
    monkeypatch.setenv("ENGINEERING_MODEL", custom_model)

    mock_toolset = MagicMock()
    mock_llm = MagicMock()

    research_agent = ResearchAgent(toolset=mock_toolset, llm_client=mock_llm)
    analytics_agent = AnalyticsAgent(toolset=mock_toolset, llm_client=mock_llm)
    engineering_agent = EngineeringAgent(toolset=mock_toolset, llm_client=mock_llm)

    assert research_agent.model_name == custom_model
    assert analytics_agent.model_name == custom_model
    assert engineering_agent.model_name == custom_model

    get_settings.cache_clear()


def test_get_model_for_role_standard_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify standard profile activates candidate mini models and 5.4 PM / 5.4-mini Critic."""
    get_settings.cache_clear()
    monkeypatch.setenv("INVESTIGATION_PROFILE", "standard")
    monkeypatch.delenv("RESEARCH_MODEL", raising=False)
    monkeypatch.delenv("PM_MODEL", raising=False)
    monkeypatch.delenv("CRITIC_MODEL", raising=False)

    assert get_model_for_role("planner") == "openai/gpt-4.1-mini"
    assert get_model_for_role("research") == "openai/gpt-4.1-mini"
    assert get_model_for_role("analytics") == "openai/gpt-4.1-mini"
    assert get_model_for_role("engineering") == "openai/gpt-4.1-mini"
    assert get_model_for_role("assessment") == "openai/gpt-4.1-mini"
    assert get_model_for_role("pm") == "openai/gpt-5.4"
    assert get_model_for_role("critic") == "openai/gpt-5.4-mini"

    get_settings.cache_clear()
