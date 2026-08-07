"""
persistence_service.py

Owns the transaction boundary around MeetingRepository. Every public
function here either commits everything it did, or rolls back
everything and raises a RuntimeError with a clear message — callers
(API routes) never see a raw SQLAlchemy exception.
"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.meeting_schemas import (
    ActionItemOut,
    MeetingDetail,
    MeetingListItem,
    SummaryOut,
    TranscriptOut,
    build_summary_preview,
)
from app.services import vector_store_service

logger = logging.getLogger(__name__)


def save_meeting(
    db: Session,
    user_id: uuid.UUID,
    filename: str,
    duration_seconds: Optional[float],
    full_text: str,
    whisper_segments: List[dict],
    speaker_segments: List[dict],
    speaker_transcript: List[dict],
    meeting_intelligence: dict,
) -> uuid.UUID:
    """
    Persist one fully-processed meeting (transcript + AI intelligence)
    as a single transaction. Either everything is saved, or nothing is.

    Args:
        user_id: the authenticated user's id (from current_user.id in
            the route). Mandatory as of Phase 6.5 — Meeting.user_id is
            a NOT NULL foreign key, so every meeting must have an
            owner; there is no "unowned" meeting anymore.

    Returns:
        The new meeting's id.

    Raises:
        RuntimeError: on any database failure. The transaction is
            always rolled back before raising.
    """
    repo = MeetingRepository(db)

    try:
        meeting = repo.create_meeting(
            user_id=user_id,
            filename=filename,
            duration_seconds=duration_seconds,
            full_text=full_text,
            whisper_segments=whisper_segments,
            speaker_segments=speaker_segments,
            speaker_transcript=speaker_transcript,
            summary_text=meeting_intelligence["summary"],
            action_items=meeting_intelligence["action_items"],
            decisions=meeting_intelligence["decisions"],
            deadlines=meeting_intelligence["deadlines"],
            key_topics=meeting_intelligence["key_topics"],
        )
        db.commit()
        logger.info("Meeting saved (id=%s, user_id=%s, filename=%s)", meeting.id, user_id, filename)
        return meeting.id

    except IntegrityError as exc:
        db.rollback()
        logger.error("Meeting save failed: integrity error")
        raise RuntimeError(
            "Could not save the meeting due to a database integrity error "
            "(e.g. a duplicate or constraint violation)."
        ) from exc
    except OperationalError as exc:
        db.rollback()
        logger.error("Meeting save failed: database unavailable/timeout")
        raise RuntimeError(
            "Could not reach the database (it may be down, or the connection timed out)."
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Meeting save failed: unexpected database error")
        raise RuntimeError(f"Failed to save the meeting to the database: {exc}") from exc


def list_meetings(
    db: Session, user_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> List[MeetingListItem]:
    """
    Return one user's meeting history list, newest first.

    Args:
        user_id: the authenticated user's id. Mandatory — this always
            queries via MeetingRepository.get_meetings_for_user(), the
            only listing method the repository exposes. There is no
            way to call this function and get another user's meetings.
    """
    repo = MeetingRepository(db)
    try:
        meetings = repo.get_meetings_for_user(user_id=user_id, limit=limit, offset=offset)
    except SQLAlchemyError as exc:
        logger.error("Failed to list meetings for user %s", user_id)
        raise RuntimeError(f"Failed to load meeting history: {exc}") from exc

    return [
        MeetingListItem(
            id=meeting.id,
            filename=meeting.filename,
            created_at=meeting.created_at,
            duration_seconds=meeting.duration_seconds,
            summary_preview=build_summary_preview(
                meeting.summary.summary_text if meeting.summary else ""
            ),
        )
        for meeting in meetings
    ]


def get_meeting_detail(
    db: Session, meeting_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[MeetingDetail]:
    """
    Return the full detail payload for one meeting — but ONLY if it
    belongs to user_id.

    Args:
        user_id: the authenticated user's id. Passed straight into
            MeetingRepository.get_meeting_for_user(), which filters by
            both meeting_id and user_id in the SQL itself.

    Returns:
        None if the meeting doesn't exist OR belongs to a different
        user — the two cases are indistinguishable on purpose, so the
        route always responds 404 rather than confirming another
        user's meeting exists via a 403.
    """
    repo = MeetingRepository(db)
    try:
        meeting: Optional[Meeting] = repo.get_meeting_for_user(meeting_id, user_id)
    except SQLAlchemyError as exc:
        logger.error("Failed to load meeting %s for user %s", meeting_id, user_id)
        raise RuntimeError(f"Failed to load meeting: {exc}") from exc

    if meeting is None:
        return None

    return MeetingDetail(
        id=meeting.id,
        filename=meeting.filename,
        created_at=meeting.created_at,
        duration_seconds=meeting.duration_seconds,
        transcript=(
            TranscriptOut(
                full_text=meeting.transcript.full_text,
                speaker_transcript=meeting.transcript.speaker_transcript,
            )
            if meeting.transcript
            else None
        ),
        summary=(
            SummaryOut(summary_text=meeting.summary.summary_text)
            if meeting.summary
            else None
        ),
        action_items=[
            ActionItemOut(owner=item.owner, task=item.task, deadline=item.deadline)
            for item in meeting.action_items
        ],
        decisions=[d.decision_text for d in meeting.decisions],
        deadlines=[d.deadline_text for d in meeting.deadlines],
        key_topics=[t.topic_text for t in meeting.key_topics],
    )


def delete_meeting(db: Session, meeting_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """
    Delete a meeting and everything attached to it (cascade) — but
    ONLY if it belongs to user_id.

    Args:
        user_id: the authenticated user's id. Passed straight into
            MeetingRepository.delete_meeting(), which only deletes a
            row matching BOTH meeting_id and user_id.

    Returns:
        True if deleted. False if no meeting with that id existed, OR
        it exists but belongs to a different user — deliberately the
        same result for both, so the route can't leak which case it
        was via a different status code.

    Raises:
        RuntimeError: on database failure. Rolled back before raising.
    """
    repo = MeetingRepository(db)
    try:
        deleted = repo.delete_meeting(meeting_id, user_id)
        db.commit()
        if deleted:
            logger.info("Meeting deleted (id=%s, user_id=%s)", meeting_id, user_id)
            # Phase 7: also remove this meeting's vectors so the
            # chatbot can never retrieve or cite a deleted meeting.
            # Best-effort — the PostgreSQL delete already committed and
            # is the source of truth; a Chroma cleanup failure here is
            # logged, not raised, so it can't undo an already-successful
            # deletion or turn it into a 500 for the user.
            try:
                vector_store_service.delete_meeting_chunks(meeting_id)
            except Exception:
                logger.exception(
                    "Failed to delete Chroma chunks for meeting %s "
                    "(PostgreSQL deletion already succeeded).",
                    meeting_id,
                )
        return deleted
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to delete meeting %s for user %s", meeting_id, user_id)
        raise RuntimeError(f"Failed to delete meeting: {exc}") from exc
