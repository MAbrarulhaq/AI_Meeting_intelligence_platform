"""
meeting_repository.py

Pure data-access layer for the Meeting aggregate and its children.
No business logic lives here, and no SQLAlchemy code lives outside
this layer (or database/) anywhere else in the project.

Transaction boundaries (commit/rollback) are NOT this repository's
responsibility — that belongs to the service layer
(services/persistence_service.py), which may combine several
repository calls into one transaction. This repository only adds
objects to the session and flushes when it needs generated values
(like a new row's id) back before the caller commits.
"""

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.action_item import ActionItem
from app.models.deadline import Deadline
from app.models.decision import Decision
from app.models.key_topic import KeyTopic
from app.models.meeting import Meeting
from app.models.summary import Summary
from app.models.transcript import Transcript


class MeetingRepository:
    """Data-access methods for Meeting and everything attached to it."""

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------
    # Writes
    # -------------------------------------------------------------

    def create_meeting(
        self,
        filename: str,
        duration_seconds: Optional[float],
        full_text: str,
        whisper_segments: List[dict],
        speaker_segments: List[dict],
        speaker_transcript: List[dict],
        summary_text: str,
        action_items: List[dict],
        decisions: List[str],
        deadlines: List[str],
        key_topics: List[str],
    ) -> Meeting:
        """
        Build the full Meeting aggregate (meeting + transcript + summary
        + all child rows) as ORM objects, add them to the session, and
        flush so generated columns (ids, server defaults) are populated.

        Does NOT commit — the caller controls the transaction boundary.
        """
        meeting = Meeting(filename=filename, duration_seconds=duration_seconds)

        meeting.transcript = Transcript(
            full_text=full_text,
            whisper_segments=whisper_segments,
            speaker_segments=speaker_segments,
            speaker_transcript=speaker_transcript,
        )

        meeting.summary = Summary(summary_text=summary_text)

        meeting.action_items = [
            ActionItem(
                owner=item.get("owner", ""),
                task=item.get("task", ""),
                deadline=item.get("deadline", ""),
            )
            for item in action_items
        ]
        meeting.decisions = [Decision(decision_text=text) for text in decisions]
        meeting.deadlines = [Deadline(deadline_text=text) for text in deadlines]
        meeting.key_topics = [KeyTopic(topic_text=text) for text in key_topics]

        self.db.add(meeting)
        self.db.flush()  # populate meeting.id and all child ids/timestamps
        return meeting

    def delete_meeting(self, meeting_id: uuid.UUID) -> bool:
        """
        Delete a meeting and everything attached to it (cascade, enforced
        at the database level via ondelete="CASCADE" on every FK).

        Returns:
            True if a meeting was found and deleted, False if no meeting
            with that id existed.
        """
        meeting = self.db.get(Meeting, meeting_id)
        if meeting is None:
            return False
        self.db.delete(meeting)
        self.db.flush()
        return True

    # -------------------------------------------------------------
    # Reads
    # -------------------------------------------------------------

    def list_meetings(self, limit: int = 50, offset: int = 0) -> List[Meeting]:
        """
        Return meetings newest-first, with their summary eagerly loaded
        (list views need the summary preview but not the full transcript
        or every child row).
        """
        stmt = (
            select(Meeting)
            .options(selectinload(Meeting.summary))
            .order_by(Meeting.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_meeting(self, meeting_id: uuid.UUID) -> Optional[Meeting]:
        """
        Return one meeting with every related row eagerly loaded in a
        single query (selectinload avoids the N+1 problem across the
        five separate child collections).
        """
        stmt = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(
                selectinload(Meeting.transcript),
                selectinload(Meeting.summary),
                selectinload(Meeting.action_items),
                selectinload(Meeting.decisions),
                selectinload(Meeting.deadlines),
                selectinload(Meeting.key_topics),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_transcript(self, meeting_id: uuid.UUID) -> Optional[Transcript]:
        """Return just the transcript row for one meeting, if it exists."""
        stmt = select(Transcript).where(Transcript.meeting_id == meeting_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_summary(self, meeting_id: uuid.UUID) -> Optional[Summary]:
        """Return just the summary row for one meeting, if it exists."""
        stmt = select(Summary).where(Summary.meeting_id == meeting_id)
        return self.db.execute(stmt).scalar_one_or_none()
