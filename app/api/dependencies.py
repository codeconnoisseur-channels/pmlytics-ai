"""FastAPI dependency providers for the PMLytics AI API."""

from app.api.manager import InvestigationManager
from app.config.settings import Settings, get_settings
from app.orchestration.service import InvestigationService
from app.storage.investigations import InvestigationRepository

_manager_instance: InvestigationManager | None = None


def get_api_settings() -> Settings:
    """Provide cached application settings."""
    return get_settings()


def get_investigation_manager() -> InvestigationManager:
    """Provide singleton process-local InvestigationManager instance."""
    global _manager_instance
    if _manager_instance is None:
        service = InvestigationService.create_default()
        settings = get_settings()
        repository = (
            InvestigationRepository(settings.database_url) if settings.database_url else None
        )
        _manager_instance = InvestigationManager(service=service, repository=repository)
    return _manager_instance


def set_investigation_manager(manager: InvestigationManager | None) -> None:
    """Explicitly configure or reset manager instance (used for testing)."""
    global _manager_instance
    _manager_instance = manager
