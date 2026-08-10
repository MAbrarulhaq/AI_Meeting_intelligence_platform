"""
vector_store_service.py

Owns the ChromaDB client and collection — the only module in this
project that imports chromadb directly. Stores ONLY embeddings,
document text, and metadata (meeting_id, user_id, filename, speaker,
content_type, chunk_number, start_time, end_time, created_at). Never
duplicates structured data that already lives in PostgreSQL as the
source of truth (summaries, action items, decisions, etc. are read
from Postgres for meeting history — they're embedded here too, as
separate short documents, purely so the chatbot can retrieve them
semantically; Postgres remains authoritative).

SECURITY: query_chunks() always filters by user_id in the Chroma
query itself (not a Python post-filter) — there is no code path here
that can return another user's documents.
"""

import logging
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import List, Optional

import chromadb

from app.config import CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "meeting_transcript_chunks"


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.ClientAPI:
    """
    Create and cache a single local, persistent Chroma client for the
    process — same caching pattern used for the Whisper model, PyAnnote
    pipeline, and Gemini clients elsewhere in this project.
    """
    logger.info("Opening Chroma persistent client at '%s'...", CHROMA_PERSIST_DIR)
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


@lru_cache(maxsize=1)
def get_collection():
    """Get (or create, on first run) the single collection all meeting documents live in."""
    client = get_chroma_client()
    return client.get_or_create_collection(name=_COLLECTION_NAME)


def add_documents(items: List[dict], embeddings: List[List[float]]) -> None:
    """
    Store a batch of indexable documents (text + embedding + metadata)
    for one meeting — transcript chunks AND/OR summary/action-item/
    decision/deadline/key-topic documents, all going through this one
    generic method rather than separate per-type methods.

    Args:
        items: each dict must already be fully formed with "id" (str),
            "text" (str), and "metadata" (dict). See
            rag_indexing_service.py for how these are built for each
            content type.
        embeddings: one vector per item, same order as items.

    IDs are deterministic per content type (e.g.
    f"{meeting_id}-transcript-{chunk_number}",
    f"{meeting_id}-summary", f"{meeting_id}-decision-{i}"), so
    re-indexing the same meeting overwrites its old documents in
    place rather than duplicating them.
    """
    if not items:
        return

    collection = get_collection()

    ids = [item["id"] for item in items]
    documents = [item["text"] for item in items]
    metadatas = [item["metadata"] for item in items]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    logger.info("Stored %d document(s) in Chroma", len(items))


def build_metadata(
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
    chunk_number: int,
    start_time: float = 0.0,
    end_time: float = 0.0,
    speaker: str = "",
) -> dict:
    """
    Build one document's metadata dict in the shape every document in
    this collection shares, regardless of content_type.

    Args:
        content_type: one of "transcript", "summary", "action_item",
            "decision", "deadline", "key_topic" — lets retrieval and
            citations distinguish what kind of source a match came from.
        start_time / end_time: only meaningful for content_type
            "transcript" (real timestamps from the recording). Default
            to 0.0 for the other types, which aren't tied to a specific
            moment in the audio.
        speaker: comma-joined speaker labels present in a transcript
            chunk; empty string for non-transcript content types,
            which aren't attributed to a specific speaker.
    """
    return {
        "meeting_id": str(meeting_id),
        "user_id": str(user_id),
        "filename": filename,
        "content_type": content_type,
        "chunk_number": chunk_number,
        "start_time": start_time,
        "end_time": end_time,
        "speaker": speaker,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def delete_meeting_chunks(meeting_id: uuid.UUID) -> None:
    """
    Remove all documents belonging to one meeting (transcript chunks
    AND summary/action-item/decision/deadline/key-topic documents).
    Called when a meeting is deleted from PostgreSQL, so the chatbot
    never retrieves (and cites) content from a meeting that no longer
    exists.
    """
    collection = get_collection()
    collection.delete(where={"meeting_id": str(meeting_id)})
    logger.info("Deleted Chroma documents for meeting %s", meeting_id)


def query_chunks(
    query_embedding: List[float],
    user_id: uuid.UUID,
    meeting_id: Optional[uuid.UUID] = None,
    top_k: int = 8,
) -> List[dict]:
    """
    Search for the top_k most relevant documents — ALWAYS filtered by
    user_id in the query itself. If meeting_id is given, additionally
    restricts to that single meeting. Searches across every
    content_type together (transcript chunks, summaries, action
    items, decisions, deadlines, key topics) — whichever is most
    semantically relevant to the query wins, regardless of type.

    Returns:
        List of {"text": str, "metadata": dict, "distance": float},
        best match first. Empty list if nothing matches.

    Raises:
        RuntimeError: if the underlying Chroma query fails (e.g. the
            store is unavailable or corrupted).
    """
    collection = get_collection()

    where_filter: dict
    if meeting_id is not None:
        where_filter = {"$and": [{"user_id": str(user_id)}, {"meeting_id": str(meeting_id)}]}
    else:
        where_filter = {"user_id": str(user_id)}

    logger.info(
        "Searching Chroma (user_id=%s, meeting_id=%s, top_k=%d)", user_id, meeting_id, top_k
    )

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )
    except Exception as exc:
        logger.error("Chroma query failed")
        raise RuntimeError(f"Vector search failed: {exc}") from exc

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]

    documents = documents[0] if documents else []
    metadatas = metadatas[0] if metadatas else []
    distances = distances[0] if distances else []

    logger.info("Retrieved %d document(s) from Chroma", len(documents))

    return [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]
