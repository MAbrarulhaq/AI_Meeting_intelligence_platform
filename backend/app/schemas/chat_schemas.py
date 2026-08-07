"""
chat_schemas.py

Pydantic request/response models for the RAG chatbot endpoint.
"""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /chat request body. Never carries a user id — ownership
    comes exclusively from the authenticated JWT (see api/chat.py)."""

    question: str = Field(min_length=1, max_length=2000)
    meeting_id: Optional[uuid.UUID] = Field(
        default=None,
        description="If set, restrict the search to this one meeting instead of all of the user's meetings.",
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
