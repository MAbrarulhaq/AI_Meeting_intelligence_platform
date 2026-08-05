"""
transcript.py

The full transcript for one meeting: Whisper's plain text and raw
segments, PyAnnote's speaker segments, and the final grouped speaker
transcript. One-to-one with Meeting.
"""

import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class Transcript(Base):
    """Everything Whisper + PyAnnote + the merge step produced for one meeting."""

    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    full_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Stored as JSONB (queryable, indexable if ever needed) rather than
    # re-normalizing every segment into its own table — segments are
    # always read as a whole per meeting, never queried individually.
    whisper_segments: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    speaker_segments: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    speaker_transcript: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    meeting: Mapped["Meeting"] = relationship(back_populates="transcript")
