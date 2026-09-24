"""Postgres persistence for investigation lifecycle records.

This adapter is an application boundary. Agents never receive database access.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

metadata = MetaData()

investigations = Table(
    "investigations",
    metadata,
    # IDs are intentionally text because they are externally visible application IDs.
    Column("investigation_id", String(80), primary_key=True),
    Column("owner_id", String(128), nullable=False),
    Column("user_query", Text, nullable=False),
    Column("display_name", Text, nullable=True),
    Column("context", JSONB, nullable=False, server_default="{}"),
    Column("status", String(40), nullable=False),
    Column("current_stage", Text, nullable=False),
    Column("active_agent", String(80), nullable=True),
    Column("revision_count", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("error", Text, nullable=True),
    Column("final_state", JSONB, nullable=True),
    Column("run_attempt", Integer, nullable=False, server_default="1"),
    Column("recovery_status", String(40), nullable=True),
    Column("heartbeat_at", DateTime(timezone=True), nullable=True),
    Column("lease_owner", String(128), nullable=True),
    Column("lease_expires_at", DateTime(timezone=True), nullable=True),
    Column("last_completed_node", String(80), nullable=True),
    Column("current_node", String(80), nullable=True),
)

Index(
    "ix_investigations_owner_created", investigations.c.owner_id, investigations.c.created_at.desc()
)

investigation_events = Table(
    "investigation_events",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "investigation_id",
        String(80),
        ForeignKey("investigations.investigation_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("event_type", String(40), nullable=False),
    Column("payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

Index(
    "ix_investigation_events_investigation_id",
    investigation_events.c.investigation_id,
    investigation_events.c.id,
)


def normalize_async_database_url(database_url: str) -> str:
    """Use asyncpg at runtime without changing the configured credentials."""
    value = database_url.strip()
    if value.startswith("postgresql+asyncpg://"):
        return value
    if value.startswith("postgresql+psycopg://"):
        return value.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+asyncpg://", 1)
    return value


@dataclass(slots=True)
class PersistedInvestigation:
    investigation_id: str
    owner_id: str
    user_query: str
    context: dict[str, Any]
    status: str
    current_stage: str
    active_agent: str | None
    revision_count: int
    created_at: datetime
    completed_at: datetime | None
    error: str | None
    final_state: dict[str, Any] | None
    display_name: str | None = None
    run_attempt: int = 1
    recovery_status: str | None = None
    heartbeat_at: datetime | None = None
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    last_completed_node: str | None = None
    current_node: str | None = None


class InvestigationRepository:
    """Owner-scoped Postgres repository for durable investigation history."""

    def __init__(self, database_url: str) -> None:
        self.engine: AsyncEngine = create_async_engine(
            normalize_async_database_url(database_url),
            pool_pre_ping=True,
            pool_recycle=300,
        )

    async def close(self) -> None:
        await self.engine.dispose()

    async def healthcheck(self) -> bool:
        try:
            async with self.engine.connect() as connection:
                await connection.execute(select(1))
            return True
        except Exception:
            return False

    async def save(self, record: PersistedInvestigation) -> None:
        values = {
            "investigation_id": record.investigation_id,
            "owner_id": record.owner_id,
            "user_query": record.user_query,
            "display_name": record.display_name,
            "context": record.context,
            "status": record.status,
            "current_stage": record.current_stage,
            "active_agent": record.active_agent,
            "revision_count": record.revision_count,
            "created_at": record.created_at,
            "updated_at": func.now(),
            "completed_at": record.completed_at,
            "error": record.error,
            "final_state": record.final_state,
            "run_attempt": record.run_attempt,
            "recovery_status": record.recovery_status,
            "heartbeat_at": record.heartbeat_at,
            "lease_owner": record.lease_owner,
            "lease_expires_at": record.lease_expires_at,
            "last_completed_node": record.last_completed_node,
            "current_node": record.current_node,
        }
        statement = insert(investigations).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[investigations.c.investigation_id],
            set_={
                key: value
                for key, value in values.items()
                if key not in {"investigation_id", "created_at"}
            },
            where=investigations.c.owner_id == record.owner_id,
        )
        async with self.engine.begin() as connection:
            await connection.execute(statement)

    async def append_event(self, investigation_id: str, event: dict[str, Any]) -> None:
        async with self.engine.begin() as connection:
            await connection.execute(
                investigation_events.insert().values(
                    investigation_id=investigation_id,
                    event_type=str(event.get("event", "message")),
                    payload=event,
                )
            )

    async def get(self, investigation_id: str, owner_id: str) -> PersistedInvestigation | None:
        statement = select(investigations).where(
            investigations.c.investigation_id == investigation_id,
            investigations.c.owner_id == owner_id,
        )
        async with self.engine.connect() as connection:
            row = (await connection.execute(statement)).mappings().one_or_none()
        return self._from_row(row) if row else None

    async def list_recent(self, owner_id: str, limit: int = 50) -> list[PersistedInvestigation]:
        statement = (
            select(investigations)
            .where(investigations.c.owner_id == owner_id)
            .order_by(investigations.c.created_at.desc())
            .limit(limit)
        )
        async with self.engine.connect() as connection:
            rows = (await connection.execute(statement)).mappings().all()
        return [self._from_row(row) for row in rows]

    async def rename(self, investigation_id: str, owner_id: str, display_name: str) -> bool:
        statement = (
            investigations.update()
            .where(
                investigations.c.investigation_id == investigation_id,
                investigations.c.owner_id == owner_id,
            )
            .values(display_name=display_name, updated_at=func.now())
        )
        async with self.engine.begin() as connection:
            result = await connection.execute(statement)
        return bool(result.rowcount)

    async def delete(self, investigation_id: str, owner_id: str) -> bool:
        async with self.engine.begin() as connection:
            owned = (
                await connection.execute(
                    select(investigations.c.investigation_id).where(
                        investigations.c.investigation_id == investigation_id,
                        investigations.c.owner_id == owner_id,
                    )
                )
            ).scalar_one_or_none()
            if owned is None:
                return False
            for table_name in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                await connection.execute(
                    text(f"DELETE FROM {table_name} WHERE thread_id = :thread_id"),
                    {"thread_id": investigation_id},
                )
            await connection.execute(
                investigations.delete().where(
                    investigations.c.investigation_id == investigation_id,
                    investigations.c.owner_id == owner_id,
                )
            )
        return True

    async def claim_recoverable(
        self,
        lease_owner: str,
        *,
        lease_seconds: int = 300,
    ) -> list[PersistedInvestigation]:
        """Atomically lease stale active records for this application process."""
        active_statuses = (
            "pending",
            "planning",
            "gathering_evidence",
            "synthesizing",
            "reviewing",
            "revising",
            "completing",
        )
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=lease_seconds)
        async with self.engine.begin() as connection:
            rows = (
                (
                    await connection.execute(
                        select(investigations)
                        .where(
                            investigations.c.status.in_(active_statuses),
                            (
                                investigations.c.lease_expires_at.is_(None)
                                | (investigations.c.lease_expires_at < now)
                            ),
                        )
                        .with_for_update(skip_locked=True)
                    )
                )
                .mappings()
                .all()
            )
            ids = [row["investigation_id"] for row in rows]
            if not ids:
                return []
            await connection.execute(
                investigations.update()
                .where(investigations.c.investigation_id.in_(ids))
                .values(
                    lease_owner=lease_owner,
                    lease_expires_at=expires_at,
                    recovery_status="recovering",
                    run_attempt=investigations.c.run_attempt + 1,
                    heartbeat_at=now,
                )
            )
            refreshed = (
                (
                    await connection.execute(
                        select(investigations).where(investigations.c.investigation_id.in_(ids))
                    )
                )
                .mappings()
                .all()
            )
        return [self._from_row(row) for row in refreshed]

    @staticmethod
    def _from_row(row: Any) -> PersistedInvestigation:
        return PersistedInvestigation(
            investigation_id=row["investigation_id"],
            owner_id=row["owner_id"],
            user_query=row["user_query"],
            display_name=row["display_name"],
            context=dict(row["context"] or {}),
            status=row["status"],
            current_stage=row["current_stage"],
            active_agent=row["active_agent"],
            revision_count=row["revision_count"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            error=row["error"],
            final_state=dict(row["final_state"]) if row["final_state"] else None,
            run_attempt=row["run_attempt"],
            recovery_status=row["recovery_status"],
            heartbeat_at=row["heartbeat_at"],
            lease_owner=row["lease_owner"],
            lease_expires_at=row["lease_expires_at"],
            last_completed_node=row["last_completed_node"],
            current_node=row["current_node"],
        )
