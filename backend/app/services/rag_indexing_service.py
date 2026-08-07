"""
rag_indexing_service.py

Indexes one meeting's transcript into ChromaDB, AFTER it has already
been saved to PostgreSQL (called from api/transcribe.py once
persistence_service.save_meeting() succeeds).
"""

import logging
import uuid
from typing import List

from app.services import embedding_service, vector_store_service
from app.services.rag_chunking_service import chunk_transcript_for_indexing

logger = logging.getLogger(__name__)


def index_meeting_transcript(
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    speaker_transcript: List[dict],
) -> None:
    """
    Chunk, embed, and store one meeting's transcript in ChromaDB.

    Deliberately swallows and logs any failure rather than raising —
    by the time this runs, the meeting already exists safely in
    PostgreSQL, so an embedding or vector-store failure must never
    fail the upload request or lose meeting data. The visible
    consequence of a failure here is that this meeting's content won't
    surface in chatbot answers until it's re-indexed — not that the
    meeting itself is lost. This is a deliberate reading of "if
    embedding fails, meeting should still exist in PostgreSQL."
    """
    try:
        chunks = chunk_transcript_for_indexing(speaker_transcript)
        if not chunks:
            logger.info("No indexable content for meeting %s - skipping embedding.", meeting_id)
            return

        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.embed_documents(texts)

        vector_store_service.add_chunks(
            meeting_id=meeting_id,
            user_id=user_id,
            filename=filename,
            chunks=chunks,
            embeddings=embeddings,
        )
        logger.info("Indexed meeting %s into Chroma (%d chunk(s)).", meeting_id, len(chunks))
    except Exception:
        logger.exception(
            "Failed to index meeting %s into Chroma - the meeting's PostgreSQL "
            "record is unaffected; it just won't be searchable by the chatbot yet.",
            meeting_id,
        )
