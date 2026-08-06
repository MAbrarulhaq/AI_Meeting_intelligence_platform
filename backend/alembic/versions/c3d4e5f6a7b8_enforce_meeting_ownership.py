"""enforce meeting ownership - FK + NOT NULL on meetings.user_id

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-06

This migration is intentionally NOT a blind schema change. Before Phase
6.5, meetings.user_id was nullable and unconstrained (a placeholder
column added in the Phase 5 migration, reserved for auth that didn't
exist yet). Making it a mandatory foreign key requires every existing
row to already have an owner — this migration checks for that first
and refuses to proceed (safely, with no partial changes — see the
transaction note below) if any meeting is still unowned, rather than
either guessing an owner or silently deleting data.

If this migration halts with an "orphaned meeting(s)" error:
    1. Decide, for each listed meeting, which user should own it (or
       that it should be deleted — e.g. it was only test data from
       before authentication existed).
    2. Run one of, per meeting:
         UPDATE meetings SET user_id = '<user-uuid>' WHERE id = '<meeting-id>';
       or:
         DELETE FROM meetings WHERE id = '<meeting-id>';
    3. Re-run `alembic upgrade head`. It will proceed past the check
       once no NULL user_id rows remain.

This is safe to attempt multiple times: Alembic runs each migration in
a transaction, so the RuntimeError raised below rolls back the entire
migration (no FK gets added, no column gets altered) — the schema is
left exactly as it was before this migration ran, never half-migrated.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FK_NAME = "fk_meetings_user_id_users"


def upgrade() -> None:
    connection = op.get_bind()

    orphaned = connection.execute(
        sa.text("SELECT id, filename FROM meetings WHERE user_id IS NULL")
    ).fetchall()

    if orphaned:
        orphan_lines = "\n".join(f"  - {row.id}  ({row.filename})" for row in orphaned)
        raise RuntimeError(
            f"\n\nCannot make meetings.user_id NOT NULL: {len(orphaned)} meeting(s) "
            f"have no owner:\n{orphan_lines}\n\n"
            "Assign each to a real user, e.g.:\n"
            "  UPDATE meetings SET user_id = '<user-uuid>' WHERE id = '<meeting-id>';\n"
            "or delete it if it was only test data from before authentication existed:\n"
            "  DELETE FROM meetings WHERE id = '<meeting-id>';\n\n"
            "Then re-run `alembic upgrade head`. Nothing has been changed by this "
            "migration attempt — it rolled back cleanly.\n"
        )

    op.create_foreign_key(
        _FK_NAME,
        "meetings",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("meetings", "user_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)


def downgrade() -> None:
    op.alter_column("meetings", "user_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.drop_constraint(_FK_NAME, "meetings", type_="foreignkey")
