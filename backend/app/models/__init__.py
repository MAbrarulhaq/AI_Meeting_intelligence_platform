"""
Importing every model here ensures they're all registered on
Base.metadata as soon as `app.models` is imported — required for
Alembic's env.py to see the full schema, and for SQLAlchemy to
resolve the string-based relationship() references between them.
"""

from app.models.action_item import ActionItem
from app.models.deadline import Deadline
from app.models.decision import Decision
from app.models.key_topic import KeyTopic
from app.models.meeting import Meeting
from app.models.summary import Summary
from app.models.transcript import Transcript

__all__ = [
    "ActionItem",
    "Deadline",
    "Decision",
    "KeyTopic",
    "Meeting",
    "Summary",
    "Transcript",
]
