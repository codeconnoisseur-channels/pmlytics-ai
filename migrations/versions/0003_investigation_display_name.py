"""Add user-managed investigation display names.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("investigations", sa.Column("display_name", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("investigations", "display_name")
