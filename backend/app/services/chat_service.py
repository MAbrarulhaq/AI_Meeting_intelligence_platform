"""
chat_service.py

Orchestrates one chat turn: retrieve relevant chunks (scoped to the
authenticated user), generate an answer grounded in them, and shape
the response — including source citations — for the API layer.
"""

import logging
import uuid
from typing import List, Optional

from app.config import RAG_HISTORY_MAX_EXCHANGES, RAG_TOP_K
from app.schemas.chat_schemas import ChatHistoryMessage, ChatResponse, ChatSource
from app.services import rag_service

logger = logging.getLogger(__name__)


def _distance_to_confidence(distance: Optional[float]) -> Optional[float]:
    """
    Rough, non-calibrated relevance score from Chroma's vector
    distance: smaller distance -> higher confidence. Clamped to
    [0, 1]. This is a heuristic for display purposes only, not a
    true probability.
    """
    if distance is None:
        return None
    return round(max(0.0, min(1.0, 1.0 - distance)), 3)


def _truncate_history(history: List[ChatHistoryMessage]) -> List[dict]:
    """
    Keep only the last RAG_HISTORY_MAX_EXCHANGES exchanges (one
    exchange = one user turn + one assistant turn = 2 messages),
    regardless of how much history the client sent. Enforced here,
    server-side, so conversation memory can't grow the prompt
    unboundedly no matter what the frontend does.
    """
    max_messages = RAG_HISTORY_MAX_EXCHANGES * 2
    trimmed = history[-max_messages:] if max_messages > 0 else []
    return [{"role": turn.role, "content": turn.content} for turn in trimmed]


def answer_question(
    user_id: uuid.UUID,
    question: str,
    meeting_id: Optional[uuid.UUID] = None,
    history: Optional[List[ChatHistoryMessage]] = None,
) -> ChatResponse:
    """
    Answer one chat question, scoped entirely to user_id.

    Args:
        user_id: the authenticated user's id (current_user.id from the
            route's get_current_user dependency) — the ONLY source of
            the ownership filter. This function never accepts or
            trusts a user id from the client.
        meeting_id: if given, restricts retrieval to that one meeting.
            If it belongs to a different user, retrieval simply
            returns zero chunks (see vector_store_service.query_chunks)
            — never another user's content, and no error that would
            reveal whether that meeting id exists.
        history: recent prior turns from the frontend, oldest first.
            Truncated to the last RAG_HISTORY_MAX_EXCHANGES exchanges
            here regardless of how much is sent — conversation memory
            is capped server-side, not just by frontend convention.

    Returns:
        ChatResponse with the answer and its source citations. If no
        relevant chunks are found, returns the fixed "couldn't find"
        message with an empty sources list — never a crash.

    Raises:
        RuntimeError: if retrieval or generation fails unrecoverably
            (e.g. Chroma unavailable, Gemini error). The route turns
            this into an HTTP error.
    """
    trimmed_history = _truncate_history(history or [])

    try:
        chunks = rag_service.retrieve_relevant_chunks(
            question=question, user_id=user_id, meeting_id=meeting_id, top_k=RAG_TOP_K
        )
    except RuntimeError:
        raise
    except Exception as exc:
        logger.error("Vector search failed for user %s", user_id)
        raise RuntimeError(f"Search is temporarily unavailable: {exc}") from exc

    if not chunks:
        logger.info("No relevant chunks found for user %s", user_id)
        return ChatResponse(answer=rag_service.NO_CONTEXT_ANSWER, sources=[])

    answer = rag_service.generate_answer(question, chunks, history=trimmed_history)

    sources = [
        ChatSource(
            meeting_id=uuid.UUID(chunk["metadata"]["meeting_id"]),
            filename=chunk["metadata"]["filename"],
            chunk_number=chunk["metadata"]["chunk_number"],
            reference_text=chunk["text"][:280],
            confidence=_distance_to_confidence(chunk.get("distance")),
        )
        for chunk in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)
