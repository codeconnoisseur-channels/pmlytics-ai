"""Create owner-scoped investigation persistence.

Revision ID: 0001
Revises: None
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("investigation_id", sa.String(length=80), primary_key=True),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("user_query", sa.Text(), nullable=False),
        sa.Column(
            "context", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("current_stage", sa.Text(), nullable=False),
        sa.Column("active_agent", sa.String(length=80), nullable=True),
        sa.Column("revision_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("final_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(
        "ix_investigations_owner_created",
        "investigations",
        ["owner_id", sa.text("created_at DESC")],
    )
    op.create_table(
        "investigation_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column(
            "investigation_id",
            sa.String(length=80),
            sa.ForeignKey("investigations.investigation_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_investigation_events_investigation_id",
        "investigation_events",
        ["investigation_id", "id"],
    )

    # Supabase Data API access is owner-scoped. The backend also applies ownership
    # checks because its pooled database connection may have elevated privileges.
    op.execute("ALTER TABLE investigations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE investigation_events ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY investigations_owner_select ON investigations FOR SELECT "
        "TO authenticated USING ((SELECT auth.uid())::text = owner_id)"
    )
    op.execute(
        "CREATE POLICY investigations_owner_insert ON investigations FOR INSERT "
        "TO authenticated WITH CHECK ((SELECT auth.uid())::text = owner_id)"
    )
    op.execute(
        "CREATE POLICY investigations_owner_update ON investigations FOR UPDATE "
        "TO authenticated USING ((SELECT auth.uid())::text = owner_id) "
        "WITH CHECK ((SELECT auth.uid())::text = owner_id)"
    )
    op.execute(
        "CREATE POLICY investigation_events_owner_select ON investigation_events FOR SELECT "
        "TO authenticated USING (EXISTS (SELECT 1 FROM investigations i "
        "WHERE i.investigation_id = investigation_events.investigation_id "
        "AND i.owner_id = (SELECT auth.uid())::text))"
    )


def downgrade() -> None:
    op.drop_table("investigation_events")
    op.drop_table("investigations")
