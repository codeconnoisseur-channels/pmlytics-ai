"""Database hardening for internally managed workflow tables."""

from typing import Any

from psycopg_pool import AsyncConnectionPool

CHECKPOINT_TABLES = (
    "checkpoints",
    "checkpoint_blobs",
    "checkpoint_writes",
    "checkpoint_migrations",
)


async def secure_checkpoint_tables(pool: AsyncConnectionPool[Any]) -> None:
    """Keep LangGraph tables private after its setup routine creates them.

    Table names are a fixed application allowlist. Runtime users never supply
    identifiers to this function.
    """
    async with pool.connection() as connection:
        for table_name in CHECKPOINT_TABLES:
            await connection.execute(f"ALTER TABLE public.{table_name} ENABLE ROW LEVEL SECURITY")
            await connection.execute(
                f"REVOKE ALL PRIVILEGES ON TABLE public.{table_name} "
                "FROM anon, authenticated, service_role"
            )
