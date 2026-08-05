"""initial schema - meetings, transcripts, summaries, action_items, decisions, deadlines, key_topics

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-08-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------
    # meetings — the root entity
    # -----------------------------------------------------------------
    op.create_table(
        "meetings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        # Reserved for Phase 6/7 auth - nullable, indexed, no FK yet
        # (the users table doesn't exist). Adding the FK constraint
        # later is a small additive migration, not a rewrite.
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_meetings_user_id", "meetings", ["user_id"])
    op.create_index("ix_meetings_created_at", "meetings", ["created_at"])

    # -----------------------------------------------------------------
    # transcripts — 1:1 with meetings
    # -----------------------------------------------------------------
    op.create_table(
        "transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("whisper_segments", postgresql.JSONB(), nullable=False),
        sa.Column("speaker_segments", postgresql.JSONB(), nullable=False),
        sa.Column("speaker_transcript", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_transcripts_meeting_id", "transcripts", ["meeting_id"])

    # -----------------------------------------------------------------
    # summaries — 1:1 with meetings
    # -----------------------------------------------------------------
    op.create_table(
        "summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_summaries_meeting_id", "summaries", ["meeting_id"])

    # -----------------------------------------------------------------
    # action_items — 1:N with meetings
    # -----------------------------------------------------------------
    op.create_table(
        "action_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("owner", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("deadline", sa.String(length=255), nullable=False, server_default=""),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_action_items_meeting_id", "action_items", ["meeting_id"])

    # -----------------------------------------------------------------
    # decisions — 1:N with meetings
    # -----------------------------------------------------------------
    op.create_table(
        "decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("decision_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_decisions_meeting_id", "decisions", ["meeting_id"])

    # -----------------------------------------------------------------
    # deadlines — 1:N with meetings
    # -----------------------------------------------------------------
    op.create_table(
        "deadlines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("deadline_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_deadlines_meeting_id", "deadlines", ["meeting_id"])

    # -----------------------------------------------------------------
    # key_topics — 1:N with meetings
    # -----------------------------------------------------------------
    op.create_table(
        "key_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meeting_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meetings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic_text", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_key_topics_meeting_id", "key_topics", ["meeting_id"])


def downgrade() -> None:
    # Reverse order - children before the parent they reference.
    op.drop_table("key_topics")
    op.drop_table("deadlines")
    op.drop_table("decisions")
    op.drop_table("action_items")
    op.drop_table("summaries")
    op.drop_table("transcripts")
    op.drop_table("meetings")
