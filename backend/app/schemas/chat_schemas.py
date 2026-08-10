"""
chat_schemas.py

Pydantic request/response models for the RAG chatbot endpoint.
"""

import uuid
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatHistoryMessage(BaseModel):
    """One prior turn in the conversation, sent by the frontend for follow-up questions."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    """POST /chat request body. Never carries a user id — ownership
    comes exclusively from the authenticated JWT (see api/chat.py)."""

    question: str = Field(min_length=1, max_length=2000)
    meeting_id: Optional[uuid.UUID] = Field(
        default=None,
        description="If set, restrict the search to this one meeting instead of all of the user's meetings.",
    )
    history: List[ChatHistoryMessage] = Field(
        default_factory=list,
        description="Recent prior turns, oldest first. Truncated server-side to the last "
        "RAG_HISTORY_MAX_EXCHANGES exchanges regardless of how much is sent here.",
    )


class ChatSource(BaseModel):
    """One citation backing part of the chatbot's answer."""

    meeting_id: uuid.UUID
    filename: str
    chunk_number: int
    reference_text: str
    confidence: Optional[float] = Field(
        default=None,
        description="Rough relevance score in [0, 1], higher is more relevant. Approximate — derived from vector distance, not a calibrated probability.",
    )


class ChatResponse(BaseModel):
    """POST /chat response."""

    answer: str
    sources: List[ChatSource] = Field(default_factory=list)
