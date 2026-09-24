"""Add durable recovery and lease metadata.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "investigations", sa.Column("run_attempt", sa.Integer(), server_default="1", nullable=False)
    )
    op.add_column(
        "investigations", sa.Column("recovery_status", sa.String(length=40), nullable=True)
    )
    op.add_column(
        "investigations", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("investigations", sa.Column("lease_owner", sa.String(length=128), nullable=True))
    op.add_column(
        "investigations", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "investigations", sa.Column("last_completed_node", sa.String(length=80), nullable=True)
    )
    op.add_column("investigations", sa.Column("current_node", sa.String(length=80), nullable=True))
    op.create_index("ix_investigations_recovery", "investigations", ["status", "lease_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_investigations_recovery", table_name="investigations")
    op.drop_column("investigations", "last_completed_node")
    op.drop_column("investigations", "current_node")
    op.drop_column("investigations", "lease_expires_at")
    op.drop_column("investigations", "lease_owner")
    op.drop_column("investigations", "heartbeat_at")
    op.drop_column("investigations", "recovery_status")
    op.drop_column("investigations", "run_attempt")
