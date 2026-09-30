"""Database security controls for Supabase-exposed public tables."""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.orchestration import service as service_module
from app.orchestration.service import InvestigationService
from app.storage.security import CHECKPOINT_TABLES, secure_checkpoint_tables


class _ConnectionContext:
    def __init__(self, connection: AsyncMock) -> None:
        self.connection = connection

    async def __aenter__(self) -> AsyncMock:
        return self.connection

    async def __aexit__(self, *args: Any) -> None:
        return None


class _SecurityPool:
    def __init__(self) -> None:
        self.connection_mock = AsyncMock()

    def connection(self) -> _ConnectionContext:
        return _ConnectionContext(self.connection_mock)


@pytest.mark.asyncio
async def test_checkpoint_security_is_default_deny_for_data_api_roles() -> None:
    pool = _SecurityPool()

    await secure_checkpoint_tables(pool)  # type: ignore[arg-type]

    statements = [str(call.args[0]) for call in pool.connection_mock.execute.await_args_list]
    assert len(statements) == len(CHECKPOINT_TABLES) * 2
    for table_name in CHECKPOINT_TABLES:
        assert f"ALTER TABLE public.{table_name} ENABLE ROW LEVEL SECURITY" in statements
        assert (
            f"REVOKE ALL PRIVILEGES ON TABLE public.{table_name} "
            "FROM anon, authenticated, service_role"
        ) in statements


@pytest.mark.asyncio
async def test_service_secures_checkpoint_tables_after_langgraph_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class _Pool:
        check_connection = MagicMock()

        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        async def open(self, *, wait: bool) -> None:
            assert wait is True
            events.append("pool_open")

        async def close(self) -> None:
            events.append("pool_close")

    class _Saver:
        def __init__(self, pool: _Pool) -> None:
            self.pool = pool

        async def setup(self) -> None:
            events.append("checkpoint_setup")

    async def _secure(pool: _Pool) -> None:
        events.append("checkpoint_secure")

    monkeypatch.setattr(service_module, "AsyncConnectionPool", _Pool)
    monkeypatch.setattr(service_module, "AsyncPostgresSaver", _Saver)
    monkeypatch.setattr(service_module, "secure_checkpoint_tables", _secure)
    monkeypatch.setattr(service_module, "create_investigation_graph", MagicMock())

    service = object.__new__(InvestigationService)
    service.checkpointer = None
    service._checkpoint_pool = None
    service.settings = MagicMock(database_url="postgresql://example.invalid/database")
    service.llm_client = MagicMock()
    service.research_agent = MagicMock()
    service.analytics_agent = MagicMock()
    service.engineering_agent = MagicMock()

    await service.start()

    assert events == ["pool_open", "checkpoint_setup", "checkpoint_secure"]
    assert isinstance(service.checkpointer, _Saver)


def test_security_migration_covers_existing_and_future_public_objects() -> None:
    migration = (
        Path(__file__).parents[2]
        / "migrations"
        / "versions"
        / "0004_secure_public_internal_tables.py"
    ).read_text(encoding="utf-8")

    for table_name in (
        "alembic_version",
        "investigations",
        "investigation_events",
        *CHECKPOINT_TABLES,
    ):
        assert f"'{table_name}'" in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "REVOKE ALL PRIVILEGES ON TABLE" in migration
    assert "ALTER DEFAULT PRIVILEGES FOR ROLE postgres" in migration
