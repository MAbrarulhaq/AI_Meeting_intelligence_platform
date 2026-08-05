"""
meeting_schemas.py

Pydantic response models for the meetings API. Kept separate from the
SQLAlchemy models in app/models/ on purpose: the API's response shape
shouldn't be tightly coupled to the database schema, and ORM objects
should never be returned directly from a route.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

_PREVIEW_LENGTH = 160


class ActionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    owner: str
    task: str
    deadline: str


class MeetingListItem(BaseModel):
    """One row in the GET /meetings history list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    created_at: datetime
    duration_seconds: Optional[float]
    summary_preview: str


class TranscriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_text: str
    speaker_transcript: List[dict]


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary_text: str


class MeetingDetail(BaseModel):
    """Full payload for GET /meetings/{id}."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    created_at: datetime
    duration_seconds: Optional[float]
    transcript: Optional[TranscriptOut]
    summary: Optional[SummaryOut]
    action_items: List[ActionItemOut]
    decisions: List[str]
    deadlines: List[str]
    key_topics: List[str]


def build_summary_preview(summary_text: str) -> str:
    """Truncate a summary to a short preview for list views."""
    if len(summary_text) <= _PREVIEW_LENGTH:
        return summary_text
    return summary_text[:_PREVIEW_LENGTH].rstrip() + "..."
