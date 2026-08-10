"""
rag_indexing_service.py

Indexes one meeting's transcript AND its meeting intelligence
(summary, action items, decisions, deadlines, key topics) into
ChromaDB — AFTER the meeting has already been saved to PostgreSQL
(called from api/transcribe.py once persistence_service.save_meeting()
succeeds).

Everything is embedded as separate documents in one collection, so a
question like "what did we decide about X" can match a decision
document directly, not just a transcript chunk that happens to
mention it.
"""

import logging
import uuid
from typing import List, Optional

from app.services import embedding_service, vector_store_service
from app.services.rag_chunking_service import chunk_transcript_for_indexing

logger = logging.getLogger(__name__)


def _build_transcript_items(
    meeting_id: uuid.UUID, user_id: uuid.UUID, filename: str, speaker_transcript: List[dict]
) -> List[dict]:
    """One item per transcript chunk (see rag_chunking_service for the chunking itself)."""
    chunks = chunk_transcript_for_indexing(speaker_transcript)
    return [
        {
            "id": f"{meeting_id}-transcript-{chunk['chunk_number']}",
            "text": chunk["text"],
            "metadata": vector_store_service.build_metadata(
                meeting_id=meeting_id,
                user_id=user_id,
                filename=filename,
                content_type="transcript",
                chunk_number=chunk["chunk_number"],
                start_time=chunk["start_time"],
                end_time=chunk["end_time"],
                speaker=chunk["speaker"],
            ),
        }
        for chunk in chunks
    ]


def _build_summary_item(
    meeting_id: uuid.UUID, user_id: uuid.UUID, filename: str, summary_text: str
) -> List[dict]:
    """One item for the whole meeting summary, if there is one."""
    if not summary_text or not summary_text.strip():
        return []
    return [
        {
            "id": f"{meeting_id}-summary",
            "text": summary_text,
            "metadata": vector_store_service.build_metadata(
                meeting_id=meeting_id,
                user_id=user_id,
                filename=filename,
                content_type="summary",
                chunk_number=1,
            ),
        }
    ]


def _build_action_item_items(
    meeting_id: uuid.UUID, user_id: uuid.UUID, filename: str, action_items: List[dict]
) -> List[dict]:
    """One item per action item, phrased as a self-contained sentence for better retrieval."""
    items = []
    for index, action_item in enumerate(action_items, start=1):
        owner = action_item.get("owner", "") or "unspecified"
        task = action_item.get("task", "")
        deadline = action_item.get("deadline", "") or "unspecified"
        if not task.strip():
            continue
        text = f"Action item: {task} (Owner: {owner}, Deadline: {deadline})"
        items.append(
            {
                "id": f"{meeting_id}-action_item-{index}",
                "text": text,
                "metadata": vector_store_service.build_metadata(
                    meeting_id=meeting_id,
                    user_id=user_id,
                    filename=filename,
                    content_type="action_item",
                    chunk_number=index,
                ),
            }
        )
    return items


def _build_simple_text_items(
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
    texts: List[str],
) -> List[dict]:
    """Shared builder for decisions/deadlines/key topics — each is just one plain-text document."""
    items = []
    for index, text in enumerate(texts, start=1):
        if not text or not text.strip():
            continue
        items.append(
            {
                "id": f"{meeting_id}-{content_type}-{index}",
                "text": text,
                "metadata": vector_store_service.build_metadata(
                    meeting_id=meeting_id,
                    user_id=user_id,
                    filename=filename,
                    content_type=content_type,
                    chunk_number=index,
                ),
            }
        )
    return items


def index_meeting_transcript(
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    speaker_transcript: List[dict],
    meeting_intelligence: Optional[dict] = None,
) -> None:
    """
    Chunk/build, embed, and store one meeting's transcript AND its
    meeting intelligence (if provided) in ChromaDB.

    Args:
        meeting_intelligence: the dict returned by
            meeting_service.generate_meeting_intelligence() — keys
            "summary", "action_items", "decisions", "deadlines",
            "key_topics". Optional so this function still works for
            transcript-only indexing if ever called without it.

    Deliberately swallows and logs any failure rather than raising —
    by the time this runs, the meeting already exists safely in
    PostgreSQL, so an embedding or vector-store failure must never
    fail the upload request or lose meeting data. The visible
    consequence of a failure here is that this meeting's content won't
    surface in chatbot answers until it's re-indexed — not that the
    meeting itself is lost.
    """
    try:
        items = _build_transcript_items(meeting_id, user_id, filename, speaker_transcript)

        if meeting_intelligence:
            items += _build_summary_item(
                meeting_id, user_id, filename, meeting_intelligence.get("summary", "")
            )
            items += _build_action_item_items(
                meeting_id, user_id, filename, meeting_intelligence.get("action_items", [])
            )
            items += _build_simple_text_items(
                meeting_id, user_id, filename, "decision", meeting_intelligence.get("decisions", [])
            )
            items += _build_simple_text_items(
                meeting_id, user_id, filename, "deadline", meeting_intelligence.get("deadlines", [])
            )
            items += _build_simple_text_items(
                meeting_id, user_id, filename, "key_topic", meeting_intelligence.get("key_topics", [])
            )

        if not items:
            logger.info("No indexable content for meeting %s - skipping embedding.", meeting_id)
            return

        # One batched embedding call for everything (transcript chunks
        # + summary + action items + decisions + deadlines + key
        # topics together), not one call per item.
        texts = [item["text"] for item in items]
        embeddings = embedding_service.embed_documents(texts)

        vector_store_service.add_documents(items, embeddings)
        logger.info("Indexed meeting %s into Chroma (%d document(s)).", meeting_id, len(items))
    except Exception:
        logger.exception(
            "Failed to index meeting %s into Chroma - the meeting's PostgreSQL "
            "record is unaffected; it just won't be searchable by the chatbot yet.",
            meeting_id,
        )
