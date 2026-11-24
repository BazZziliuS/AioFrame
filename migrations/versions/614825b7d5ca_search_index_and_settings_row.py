"""search text, created_at index, settings row

- `storage_users.search_text`: lowercased "fullname login" for case-insensitive search
  (SQLite lower() is ASCII-only, so Cyrillic names were not found)
- index on `created_at` for statistics and "newest first" lists
- names were stored HTML-escaped (`&lt;` / `&gt;`) by older versions: store raw values
- the single settings row always has id=1

Revision ID: 614825b7d5ca
Revises: c3a1f7d2e9b4
Create Date: 2026-11-24 05:28:02.606589

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "614825b7d5ca"
down_revision: str | Sequence[str] | None = "c3a1f7d2e9b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

users = sa.table(
    "storage_users",
    sa.column("id", sa.Integer),
    sa.column("user_login", sa.String),
    sa.column("user_name", sa.String),
    sa.column("user_surname", sa.String),
    sa.column("user_fullname", sa.String),
    sa.column("search_text", sa.String),
)


def _unescape(value: str | None) -> str:
    # Older versions replaced only "<" and ">"; nothing else needs to be restored
    return (value or "").replace("&lt;", "<").replace("&gt;", ">")


def _backfill_users() -> None:
    if context.is_offline_mode():
        # No access to rows when generating SQL: the bot refreshes profiles on contact
        op.execute(
            users.update().values(
                search_text=sa.func.lower(users.c.user_fullname + " " + users.c.user_login)
            )
        )
        return

    connection = op.get_bind()
    rows = connection.execute(
        sa.select(
            users.c.id,
            users.c.user_login,
            users.c.user_name,
            users.c.user_surname,
            users.c.user_fullname,
        )
    ).all()
    for row in rows:
        fullname = _unescape(row.user_fullname)
        connection.execute(
            users.update()
            .where(users.c.id == row.id)
            .values(
                user_name=_unescape(row.user_name),
                user_surname=_unescape(row.user_surname),
                user_fullname=fullname,
                # Python lower() handles every alphabet
                search_text=f"{fullname} {row.user_login or ''}".strip().lower(),
            )
        )


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("storage_users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("search_text", sa.String(), server_default="", nullable=False)
        )
        batch_op.create_index(
            batch_op.f("ix_storage_users_created_at"), ["created_at"], unique=False
        )

    _backfill_users()

    # The bot expects exactly one settings row with id=1
    op.execute(
        sa.text(
            "INSERT INTO storage_settings (id, is_maintenance) "
            "SELECT 1, :off WHERE NOT EXISTS (SELECT 1 FROM storage_settings WHERE id = 1)"
        ).bindparams(off=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("storage_users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_storage_users_created_at"))
        batch_op.drop_column("search_text")
