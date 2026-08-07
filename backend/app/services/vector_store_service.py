"""
vector_store_service.py

Owns the ChromaDB client and collection — the only module in this
project that imports chromadb directly. Stores ONLY embeddings, chunk
text, and metadata (meeting_id, user_id, filename, chunk_number,
start_time, end_time, created_at). Never duplicates structured data
that already lives in PostgreSQL (summaries, action items, decisions,
etc. stay exclusively in Postgres — see services/persistence_service.py).

SECURITY: query_chunks() always filters by user_id in the Chroma
query itself (not a Python post-filter) — there is no code path here
that can return another user's chunks.
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
    """Get (or create, on first run) the single collection all meeting chunks live in."""
    client = get_chroma_client()
    return client.get_or_create_collection(name=_COLLECTION_NAME)


def add_chunks(
    meeting_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    chunks: List[dict],
    embeddings: List[List[float]],
) -> None:
    """
    Store a batch of chunks (text + embedding + metadata) for one
    meeting.

    Args:
        chunks: each dict must have chunk_number, text, start_time,
            end_time (see rag_chunking_service.chunk_transcript_for_indexing).
        embeddings: one vector per chunk, same order as chunks.

    IDs are deterministic (f"{meeting_id}-{chunk_number}"), so
    re-indexing the same meeting overwrites its old chunks in place
    rather than duplicating them.
    """
    if not chunks:
        return

    collection = get_collection()
    created_at = datetime.now(timezone.utc).isoformat()

    ids = [f"{meeting_id}-{chunk['chunk_number']}" for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "meeting_id": str(meeting_id),
            "user_id": str(user_id),
            "filename": filename,
            "chunk_number": chunk["chunk_number"],
            "start_time": chunk["start_time"],
            "end_time": chunk["end_time"],
            "created_at": created_at,
        }
        for chunk in chunks
    ]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    logger.info("Stored %d chunk(s) in Chroma for meeting %s", len(chunks), meeting_id)


def delete_meeting_chunks(meeting_id: uuid.UUID) -> None:
    """
    Remove all chunks belonging to one meeting. Called when a meeting
    is deleted from PostgreSQL, so the chatbot never retrieves (and
    cites) content from a meeting that no longer exists.
    """
    collection = get_collection()
    collection.delete(where={"meeting_id": str(meeting_id)})
    logger.info("Deleted Chroma chunks for meeting %s", meeting_id)


def query_chunks(
    query_embedding: List[float],
    user_id: uuid.UUID,
    meeting_id: Optional[uuid.UUID] = None,
    top_k: int = 5,
) -> List[dict]:
    """
    Search for the top_k most relevant chunks — ALWAYS filtered by
    user_id in the query itself. If meeting_id is given, additionally
    restricts to that single meeting.

    Returns:
        List of {"text": str, "metadata": dict, "distance": float},
        best match first. Empty list if nothing matches (e.g. the
        user has no indexed meetings yet, or meeting_id belongs to a
        different user — which looks identical to "not found").

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

    logger.info("Retrieved %d chunk(s) from Chroma", len(documents))

    return [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]
