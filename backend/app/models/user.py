"""
user.py

The User model. Phase 6.5 links this to Meeting via a proper
one-to-many relationship (User.meetings) — see models/meeting.py for
the Meeting.user_id foreign key and Meeting.user relationship.
"""

import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class User(Base):
    """A registered user of the platform."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    # Never store passwords — only the bcrypt hash. See app/security/password.py.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Deleting a user cascades to their meetings at the database level
    # (see the ondelete="CASCADE" on Meeting.user_id's ForeignKey).
    # passive_deletes=True here means SQLAlchemy lets the database
    # perform that cascade rather than issuing per-row DELETEs itself.
    meetings: Mapped[List["Meeting"]] = relationship(
        back_populates="user", passive_deletes=True, order_by="Meeting.created_at.desc()"
    )
