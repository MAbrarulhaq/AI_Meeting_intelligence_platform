"""
meeting.py

The Meeting model is the root entity: one row per processed recording.
Transcript, Summary, ActionItems, Decisions, Deadlines, and KeyTopics
all hang off it via foreign keys with cascade delete — deleting a
Meeting deletes everything related to it.
"""

import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.action_item import ActionItem
    from app.models.deadline import Deadline
    from app.models.decision import Decision
    from app.models.key_topic import KeyTopic
    from app.models.summary import Summary
    from app.models.transcript import Transcript
    from app.models.user import User


class Meeting(Base):
    """One processed meeting recording, with all its derived data attached."""

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Phase 6.5: every meeting must belong to exactly one user. NOT
    # NULL + a real FK now (was a nullable, unconstrained placeholder
    # column through Phase 6 — see the Phase 6.5 migration for how
    # existing NULL rows are handled).
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    transcript: Mapped[Optional["Transcript"]] = relationship(
        back_populates="meeting", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    summary: Mapped[Optional["Summary"]] = relationship(
        back_populates="meeting", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    action_items: Mapped[List["ActionItem"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", passive_deletes=True,
        order_by="ActionItem.created_at",
    )
    decisions: Mapped[List["Decision"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Decision.created_at",
    )
    deadlines: Mapped[List["Deadline"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Deadline.created_at",
    )
    key_topics: Mapped[List["KeyTopic"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", passive_deletes=True,
        order_by="KeyTopic.created_at",
    )
    user: Mapped["User"] = relationship(back_populates="meetings")
