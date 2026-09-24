"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ]

    # Application persistence and identity
    database_url: str = ""
    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    supabase_publishable_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SUPABASE_PUBLISHABLE_KEY",
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        ),
    )
    auth_required: bool = True

    @field_validator("supabase_url")
    @classmethod
    def normalize_supabase_url(cls, value: str) -> str:
        """Accept a copied REST endpoint but retain the canonical project root."""
        normalized = value.strip().rstrip("/")
        if normalized.endswith("/rest/v1"):
            normalized = normalized[: -len("/rest/v1")]
        return normalized

    # OpenRouter (Inference Gateway)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openai/gpt-5.4"

    # Runtime Profile
    investigation_profile: Literal["standard", "deep"] = "deep"
    demo_dataset_version: str = "2.0"

    # Role Model Overrides (Set via env var e.g. RESEARCH_MODEL; falls back to profile routing or default_model)
    planner_model: str | None = None
    research_model: str | None = None
    analytics_model: str | None = None
    engineering_model: str | None = None
    assessment_model: str | None = None
    pm_model: str | None = None
    pm_revision_model: str | None = None
    critic_model: str | None = None

    # Role Token Ceilings (Evidence-based bounded limits to prevent truncation and eliminate retries)
    planner_max_tokens: int = 1024
    research_max_tokens: int = 2560
    analytics_max_tokens: int = 2560
    engineering_max_tokens: int = 2560
    pm_max_tokens: int = 5120
    pm_revision_max_tokens: int = 3584
    critic_max_tokens: int = 2048

    # LangSmith (AI Observability)
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "PMLytics-AI"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # PostHog (Product Analytics)
    posthog_host: str = "https://us.posthog.com"
    posthog_project_id: str = ""
    posthog_project_token: str = ""
    posthog_api_key: str = ""
    posthog_timeout_seconds: float = 20.0

    # Local Mocks
    zendesk_base_url: str = "http://localhost:8080"
    zendesk_username: str = "mock@pocket.test"
    zendesk_api_key: str = "mock-zendesk-token-pocket"
    zendesk_timeout_seconds: float = 5.0
    jira_base_url: str = "http://localhost:1080"
    jira_username: str = "mock-jira@pocket.test"
    jira_api_token: str = "mock-jira-token-pocket"
    jira_timeout_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    """Return cached instance of application settings and sync LangSmith environment variables."""
    s = Settings()
    import os

    if s.langsmith_tracing and s.langsmith_api_key:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_API_KEY"] = s.langsmith_api_key
        os.environ["LANGCHAIN_API_KEY"] = s.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = s.langsmith_project
        os.environ["LANGCHAIN_PROJECT"] = s.langsmith_project
        os.environ["LANGSMITH_ENDPOINT"] = s.langsmith_endpoint
        os.environ["LANGCHAIN_ENDPOINT"] = s.langsmith_endpoint
    return s


def get_model_for_role(role: str) -> str:
    """Resolve the configured model for a specific agent role.

    Resolution order:
    1. Explicit role override (e.g. RESEARCH_MODEL env var)
    2. Investigation profile defaults (if profile == 'standard', candidate mini routing)
    3. Global default model (DEFAULT_MODEL, default 'openai/gpt-5.4')
    """
    settings = get_settings()
    override = getattr(settings, f"{role}_model", None)
    if override:
        return str(override)

    if settings.investigation_profile == "standard":
        standard_models: dict[str, str] = {
            "planner": "openai/gpt-4.1-mini",
            "assessment": "openai/gpt-4.1-mini",
            "research": "openai/gpt-4.1-mini",
            "analytics": "openai/gpt-4.1-mini",
            "engineering": "openai/gpt-4.1-mini",
            "pm": "openai/gpt-5.4",
            "pm_synthesis": "openai/gpt-5.4",
            "pm_revision": "openai/gpt-5.4-mini",
            "critic": "openai/gpt-5.4-mini",
        }
        if role in standard_models:
            return standard_models[role]

    return str(settings.default_model)


def get_max_tokens_for_role(role: str) -> int:
    """Resolve the evidence-based token ceiling for a specific approved role."""
    settings = get_settings()
    normalized = role.lower().strip()
    ceiling_map = {
        "planner": settings.planner_max_tokens,
        "research": settings.research_max_tokens,
        "analytics": settings.analytics_max_tokens,
        "engineering": settings.engineering_max_tokens,
        "pm": settings.pm_max_tokens,
        "pm_synthesis": settings.pm_max_tokens,
        "pm_revision": settings.pm_revision_max_tokens,
        "critic": settings.critic_max_tokens,
    }
    if normalized not in ceiling_map:
        raise ValueError(
            f"Unknown or unapproved agent role '{role}' for token budget allocation. "
            f"Approved roles are: {list(ceiling_map.keys())}"
        )
    return ceiling_map[normalized]


ROLE_MAX_TOKENS: dict[str, int] = {
    "planner": 1024,
    "research": 2560,
    "analytics": 2560,
    "engineering": 2560,
    "pm": 5120,
    "critic": 2048,
}
