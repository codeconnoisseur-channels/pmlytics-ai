"""Secure internal tables from Supabase Data API access.

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic owns the application tables, while LangGraph creates checkpoint
    # tables during checkpointer setup. Secure whichever checkpoint tables
    # already exist; application startup applies the same controls after setup
    # so a clean database is protected as well.
    op.execute(
        """
        DO $$
        DECLARE
            table_name text;
        BEGIN
            FOREACH table_name IN ARRAY ARRAY[
                'alembic_version',
                'investigations',
                'investigation_events',
                'checkpoints',
                'checkpoint_blobs',
                'checkpoint_writes',
                'checkpoint_migrations'
            ]
            LOOP
                IF to_regclass(format('public.%I', table_name)) IS NOT NULL THEN
                    EXECUTE format(
                        'ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',
                        table_name
                    );
                    EXECUTE format(
                        'REVOKE ALL PRIVILEGES ON TABLE public.%I '
                        'FROM anon, authenticated, service_role',
                        table_name
                    );
                END IF;
            END LOOP;
        END
        $$;
        """
    )
    op.execute(
        "REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public "
        "FROM anon, authenticated, service_role"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE ALL PRIVILEGES ON TABLES FROM anon, authenticated, service_role"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE ALL PRIVILEGES ON SEQUENCES FROM anon, authenticated, service_role"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated, service_role"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public "
        "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
    )


def downgrade() -> None:
    # Intentionally irreversible. Restoring broad public-schema grants or
    # disabling RLS would recreate the security vulnerability this migration
    # closes. A future access requirement must use a new migration with explicit
    # least-privilege grants and policies.
    pass
