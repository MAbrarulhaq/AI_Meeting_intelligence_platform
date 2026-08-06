"""
meetings.py

Meeting history endpoints: list, detail, transcript-only,
summary-only, and delete. All persistence logic is delegated to
services/persistence_service.py — no SQLAlchemy code here.

SECURITY: every route below requires authentication and passes
current_user.id into persistence_service — never a meeting id alone.
No route accepts a user id from the request; ownership is determined
exclusively from the verified JWT via get_current_user. See the
Phase 6.6 security audit for what this replaced (these routes
previously had no auth dependency at all).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.meeting_schemas import MeetingDetail, MeetingListItem, SummaryOut, TranscriptOut
from app.security.dependencies import get_current_user
from app.services import persistence_service

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("", response_model=list[MeetingListItem])
def list_meetings(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's meeting history, newest first — never any other user's."""
    try:
        return persistence_service.list_meetings(db, user_id=current_user.id, limit=limit, offset=offset)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the complete detail for one meeting — only if it belongs to
    the authenticated user. A meeting that exists but belongs to
    someone else returns 404, identical to a meeting_id that doesn't
    exist at all (never confirms another user's meeting exists).
    """
    try:
        meeting = persistence_service.get_meeting_detail(db, meeting_id, user_id=current_user.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if meeting is None:
        raise HTTPException(status_code=404, detail=f"No meeting found with id {meeting_id}.")
    return meeting


@router.get("/{meeting_id}/transcript", response_model=TranscriptOut)
def get_meeting_transcript(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return just the transcript for one meeting — only if it belongs to the authenticated user."""
    try:
        meeting = persistence_service.get_meeting_detail(db, meeting_id, user_id=current_user.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if meeting is None:
        raise HTTPException(status_code=404, detail=f"No meeting found with id {meeting_id}.")
    if meeting.transcript is None:
        raise HTTPException(status_code=404, detail="This meeting has no transcript.")
    return meeting.transcript


@router.get("/{meeting_id}/summary", response_model=SummaryOut)
def get_meeting_summary(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return just the summary for one meeting — only if it belongs to the authenticated user."""
    try:
        meeting = persistence_service.get_meeting_detail(db, meeting_id, user_id=current_user.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if meeting is None:
        raise HTTPException(status_code=404, detail=f"No meeting found with id {meeting_id}.")
    if meeting.summary is None:
        raise HTTPException(status_code=404, detail="This meeting has no summary.")
    return meeting.summary


@router.delete("/{meeting_id}")
def delete_meeting(
    meeting_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a meeting and everything attached to it (cascade) — only if
    it belongs to the authenticated user. Attempting to delete
    someone else's meeting id returns 404 (never deletes, never
    confirms the meeting exists).
    """
    try:
        deleted = persistence_service.delete_meeting(db, meeting_id, user_id=current_user.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if not deleted:
        raise HTTPException(status_code=404, detail=f"No meeting found with id {meeting_id}.")
    return {"status": "deleted", "id": meeting_id}
