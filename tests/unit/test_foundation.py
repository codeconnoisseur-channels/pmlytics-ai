"""Foundation and environment verification tests for Phase 0."""

from pathlib import Path

import app
import pytest
from app.config.settings import Settings, get_settings


def test_package_importability() -> None:
    """Verify that the app package and core modules are importable."""
    assert app is not None
    assert hasattr(app, "__version__")
    assert isinstance(app.__version__, str)


def test_settings_load_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that settings can be loaded cleanly with safe defaults."""
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.default_model == "openai/gpt-5.4"
    assert settings.langsmith_tracing is False
    assert settings.zendesk_base_url == "http://localhost:8080"
    assert settings.jira_base_url == "http://localhost:1080"


def test_get_settings_caching() -> None:
    """Verify that get_settings returns a cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_env_example_matches_settings_contract() -> None:
    """Verify that all keys declared in .env.example exist in Settings model fields."""
    env_example_path = Path(__file__).parents[2] / ".env.example"
    assert env_example_path.exists(), ".env.example must exist in repository root"

    env_keys: set[str] = set()
    with open(env_example_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                env_keys.add(key.lower())

    settings_fields = {field.lower() for field in Settings.model_fields}
    frontend_public_keys = {key for key in env_keys if key.startswith("next_public_")}
    assert {
        "next_public_supabase_url",
        "next_public_supabase_publishable_key",
    }.issubset(frontend_public_keys)

    missing_in_settings = (env_keys - frontend_public_keys) - settings_fields
    assert not missing_in_settings, (
        f".env.example defines keys missing from Settings: {missing_in_settings}"
    )


def test_settings_override_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that environment variables properly override default settings."""
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4.6")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    settings = Settings()
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
    assert settings.default_model == "anthropic/claude-sonnet-4.6"
    assert settings.langsmith_tracing is True
