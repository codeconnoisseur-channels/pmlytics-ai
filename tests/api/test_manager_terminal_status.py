"""Regression tests for truthful API investigation terminal states."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.api.manager import InvestigationManager
from app.orchestration.state import InvestigationState


@pytest.mark.asyncio
async def test_manager_does_not_promote_failed_graph_to_completed() -> None:
    service = MagicMock()
    service.investigate = AsyncMock(
        return_value=InvestigationState(
            investigation_id="inv_failed_graph",
            user_query="Why did verification drop off?",
            status="failed",
        )
    )
    manager = InvestigationManager(service=service)

    record = manager.create_investigation("Why did verification drop off?")
    await record.task

    assert record.status == "failed"
    assert record.error == "The investigation ended without enough verified evidence for a report."
    assert record.event_history[-1]["event"] == "failed"
