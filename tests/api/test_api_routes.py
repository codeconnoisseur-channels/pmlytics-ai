"""Integration tests for FastAPI HTTP routes using httpx AsyncClient."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.api.auth import AuthenticatedUser, get_current_user
from app.api.dependencies import set_investigation_manager
from app.api.main import create_app
from app.api.manager import InvestigationManager
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_app():
    """Create FastAPI application with a mocked InvestigationManager."""
    app = create_app()
    mock_service = MagicMock()
    mock_service.settings = MagicMock()
    mock_service.settings.langsmith_tracing = False
    mock_service.settings.langsmith_api_key = ""
    mock_service.settings.environment = "test"

    async def slow_investigate(*args, **kwargs):
        await asyncio.sleep(5)

    mock_service.investigate = AsyncMock(side_effect=slow_investigate)
    manager = InvestigationManager(service=mock_service)
    set_investigation_manager(manager)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(user_id="test-user")
    yield app
    app.dependency_overrides.clear()
    set_investigation_manager(None)


@pytest.mark.asyncio
async def test_post_investigations_returns_202_accepted(mock_app) -> None:
    """POST /api/v1/investigations accepts valid query and returns 202."""
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/investigations", json={"user_query": "Why are transfers failing?"}
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "investigation_id" in data
        assert data["status"] == "pending"
        assert "/api/v1/investigations/" in data["status_url"]


@pytest.mark.asyncio
async def test_post_investigations_validates_query(mock_app) -> None:
    """Empty or whitespace-only queries must return 422 Unprocessable Entity."""
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/investigations", json={"user_query": "   "})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_status_returns_404_for_unknown_id(mock_app) -> None:
    """GET /api/v1/investigations/{id} returns 404 for unknown ID."""
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/investigations/inv_nonexistent_123")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_result_returns_409_while_running(mock_app) -> None:
    """GET /api/v1/investigations/{id}/result returns 409 Conflict when still in progress."""
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post_resp = await client.post("/api/v1/investigations", json={"user_query": "Running test"})
        inv_id = post_resp.json()["investigation_id"]

        result_resp = await client.get(f"/api/v1/investigations/{inv_id}/result")
        assert result_resp.status_code == 409
        detail = result_resp.json()["detail"]
        assert "still in progress" in detail["message"]


@pytest.mark.asyncio
async def test_get_result_returns_500_on_failed_investigation(mock_app) -> None:
    """GET /api/v1/investigations/{id}/result returns 500 when investigation failed (never 200)."""
    from app.api.dependencies import get_investigation_manager

    mgr = get_investigation_manager()
    mgr.service.investigate = AsyncMock(side_effect=RuntimeError("Simulated upstream failure"))

    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post_resp = await client.post("/api/v1/investigations", json={"user_query": "Failing test"})
        inv_id = post_resp.json()["investigation_id"]

        record = mgr.get(inv_id)
        if record and record.task:
            await record.task

        result_resp = await client.get(f"/api/v1/investigations/{inv_id}/result")
        assert result_resp.status_code == 500
        assert "failed during execution" in str(result_resp.json()["detail"])


@pytest.mark.asyncio
async def test_health_endpoint_is_sanitized(mock_app) -> None:
    """GET /api/v1/health returns health status without exposing credentials."""
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["process"] == "healthy"
        assert "dependencies" in data
        # Verify no secrets in response text
        raw_text = resp.text
        assert "sk-or-v1" not in raw_text
        assert "api_key" not in raw_text


@pytest.mark.asyncio
async def test_cancel_investigation(mock_app) -> None:
    """POST /api/v1/investigations/{id}/cancel cancels an active investigation."""
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post_resp = await client.post("/api/v1/investigations", json={"user_query": "Cancel test"})
        inv_id = post_resp.json()["investigation_id"]

        cancel_resp = await client.post(f"/api/v1/investigations/{inv_id}/cancel")
        assert cancel_resp.status_code == 200
        data = cancel_resp.json()
        assert data["status"] == "cancelled"

        status_resp = await client.get(f"/api/v1/investigations/{inv_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_rename_and_delete_terminal_investigation(mock_app) -> None:
    from app.api.dependencies import get_investigation_manager

    manager = get_investigation_manager()
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/v1/investigations", json={"user_query": "Original product question"}
        )
        investigation_id = created.json()["investigation_id"]
        await client.post(f"/api/v1/investigations/{investigation_id}/cancel")

        renamed = await client.patch(
            f"/api/v1/investigations/{investigation_id}",
            json={"display_name": "Transfer reliability review"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["display_name"] == "Transfer reliability review"
        assert renamed.json()["user_query"] == "Original product question"

        deleted = await client.delete(f"/api/v1/investigations/{investigation_id}")
        assert deleted.status_code == 204
        assert manager.get(investigation_id) is None


@pytest.mark.asyncio
async def test_failed_investigation_can_be_retried_as_new_run(mock_app) -> None:
    from app.api.dependencies import get_investigation_manager

    manager = get_investigation_manager()
    record = manager.create_investigation(
        user_query="Why did verification fail?", owner_id="test-user"
    )
    if record.task:
        record.task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await record.task
    record.status = "failed"

    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/v1/investigations/{record.investigation_id}/retry")

    assert response.status_code == 202
    assert response.json()["investigation_id"] != record.investigation_id


@pytest.mark.asyncio
async def test_cors_rejects_unauthorized_origins(mock_app) -> None:
    """CORS middleware rejects origins not in the configured list."""
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://malicious-external-origin.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert (
            resp.headers.get("access-control-allow-origin")
            != "http://malicious-external-origin.com"
        )
