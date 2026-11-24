"""admin tools: ban, blocked flag, maintenance mode

Revision ID: c3a1f7d2e9b4
Revises: b29ddd50d53e
Create Date: 2026-11-24 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a1f7d2e9b4"
down_revision: str | Sequence[str] | None = "b29ddd50d53e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("storage_users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_banned", sa.Boolean(), server_default=sa.false(), nullable=False)
        )
        batch_op.add_column(
            sa.Column("is_blocked", sa.Boolean(), server_default=sa.false(), nullable=False)
        )

    # `status_work` was never used; it becomes the maintenance flag (off by default)
    with op.batch_alter_table("storage_settings", schema=None) as batch_op:
        batch_op.alter_column(
            "status_work",
            new_column_name="is_maintenance",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.false(),
        )
    op.execute(sa.text("UPDATE storage_settings SET is_maintenance = :off").bindparams(off=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("storage_settings", schema=None) as batch_op:
        batch_op.alter_column(
            "is_maintenance",
            new_column_name="status_work",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )

    with op.batch_alter_table("storage_users", schema=None) as batch_op:
        batch_op.drop_column("is_blocked")
        batch_op.drop_column("is_banned")
