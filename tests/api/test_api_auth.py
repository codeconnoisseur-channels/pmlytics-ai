"""Authentication and investigation-ownership API boundary tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.api.auth import AuthenticatedUser, get_current_user
from app.api.dependencies import set_investigation_manager
from app.api.main import create_app
from app.api.manager import InvestigationManager
from httpx import ASGITransport, AsyncClient


def _manager() -> InvestigationManager:
    service = MagicMock()

    async def slow_investigate(*args, **kwargs):
        await asyncio.sleep(5)

    service.investigate = AsyncMock(side_effect=slow_investigate)
    service.settings = MagicMock(
        langsmith_tracing=False,
        langsmith_api_key="",
        environment="test",
    )
    return InvestigationManager(service=service)


@pytest.mark.asyncio
async def test_protected_investigation_route_requires_authentication() -> None:
    app = create_app()
    set_investigation_manager(_manager())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/investigations")
    assert response.status_code == 401
    set_investigation_manager(None)


@pytest.mark.asyncio
async def test_investigation_ids_do_not_cross_user_boundary() -> None:
    app = create_app()
    manager = _manager()
    set_investigation_manager(manager)
    current_user = AuthenticatedUser(user_id="user-a")
    app.dependency_overrides[get_current_user] = lambda: current_user
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/v1/investigations",
            json={"user_query": "Why are transfers failing?"},
        )
        assert created.status_code == 202
        investigation_id = created.json()["investigation_id"]

        current_user = AuthenticatedUser(user_id="user-b")
        hidden = await client.get(f"/api/v1/investigations/{investigation_id}")
        assert hidden.status_code == 404

        visible_list = await client.get("/api/v1/investigations")
        assert visible_list.status_code == 200
        assert visible_list.json() == []

    record = manager.get(investigation_id)
    if record and record.task:
        record.task.cancel()
    app.dependency_overrides.clear()
    set_investigation_manager(None)
