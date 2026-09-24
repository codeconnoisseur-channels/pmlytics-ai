"""Regression tests for durable investigation lifecycle behavior."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from app.api.manager import InvestigationManager
from app.storage.investigations import PersistedInvestigation


class FakeRepository:
    def __init__(self, records: list[PersistedInvestigation] | None = None) -> None:
        self.records = {record.investigation_id: record for record in records or []}
        self.events: list[tuple[str, dict[str, object]]] = []

    async def save(self, record: PersistedInvestigation) -> None:
        self.records[record.investigation_id] = record

    async def get(self, investigation_id: str, owner_id: str) -> PersistedInvestigation | None:
        record = self.records.get(investigation_id)
        return record if record and record.owner_id == owner_id else None

    async def list_recent(self, owner_id: str, limit: int = 50) -> list[PersistedInvestigation]:
        return [record for record in self.records.values() if record.owner_id == owner_id][:limit]

    async def append_event(self, investigation_id: str, event: dict[str, object]) -> None:
        self.events.append((investigation_id, event))


def _record(*, status: str = "completed", owner_id: str = "user-a") -> PersistedInvestigation:
    return PersistedInvestigation(
        investigation_id="inv_persisted_1",
        owner_id=owner_id,
        user_query="Why did completion fall?",
        context={},
        status=status,
        current_stage="Investigation complete",
        active_agent=None,
        revision_count=0,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC) if status == "completed" else None,
        error=None,
        final_state=None,
    )


@pytest.mark.asyncio
async def test_history_is_reloaded_and_owner_scoped() -> None:
    repository = FakeRepository([_record()])
    manager = InvestigationManager(service=MagicMock(), repository=repository)  # type: ignore[arg-type]

    assert await manager.get_owned("inv_persisted_1", "user-b") is None
    loaded = await manager.get_owned("inv_persisted_1", "user-a")

    assert loaded is not None
    assert loaded.status == "completed"
    assert loaded.user_query == "Why did completion fall?"


@pytest.mark.asyncio
async def test_process_lost_active_run_is_not_shown_as_still_running() -> None:
    repository = FakeRepository([_record(status="reviewing")])
    manager = InvestigationManager(service=MagicMock(), repository=repository)  # type: ignore[arg-type]

    loaded = await manager.get_owned("inv_persisted_1", "user-a")

    assert loaded is not None
    assert loaded.status == "recovery_required"
    assert loaded.current_stage == "Investigation needs recovery"
    assert loaded.completed_at is None
    assert repository.records["inv_persisted_1"].status == "recovery_required"


@pytest.mark.asyncio
async def test_live_foreign_lease_is_not_mislabeled_as_interrupted() -> None:
    persisted = _record(status="reviewing")
    persisted.lease_owner = "another-live-api-process"
    persisted.lease_expires_at = datetime.now(UTC) + timedelta(minutes=2)
    repository = FakeRepository([persisted])
    manager = InvestigationManager(service=MagicMock(), repository=repository)  # type: ignore[arg-type]

    loaded = await manager.get_owned("inv_persisted_1", "user-a")

    assert loaded is not None
    assert loaded.status == "reviewing"
    assert loaded.current_stage == "Investigation complete"
    assert repository.records["inv_persisted_1"].status == "reviewing"
