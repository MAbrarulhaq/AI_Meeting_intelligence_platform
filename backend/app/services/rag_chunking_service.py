"""
rag_chunking_service.py

Chunks a grouped speaker transcript for RAG indexing: ~900 target
tokens per chunk with ~125 tokens of overlap between consecutive
chunks, always breaking on speaker-turn boundaries (never mid-sentence).

Deliberately separate from services/chunking_service.py, which chunks
transcripts for Gemini's Map-Reduce meeting summarization — a
different consumer with a different target size and no overlap
requirement. Sharing one chunker between two purposes with different
tuning would make either one worse; keeping them separate keeps both
simple and independently tunable.
"""

import logging
from typing import List

from app.config import RAG_CHUNK_OVERLAP_TOKENS, RAG_CHUNK_TARGET_TOKENS

logger = logging.getLogger(__name__)

# Same rough approximation used elsewhere in this project (Gemini has
# no bundled offline tokenizer) — good enough for chunk-boundary
# decisions, not used for anything that needs to be exact.
CHARACTERS_PER_TOKEN_ESTIMATE = 4


def _turn_text(turn: dict) -> str:
    """Render one speaker turn as the text that goes into the chunk."""
    speaker = turn.get("speaker", "UNKNOWN")
    text = turn.get("text", "").strip()
    return f"{speaker}: {text}"


def chunk_transcript_for_indexing(
    speaker_transcript: List[dict],
    target_tokens: int = RAG_CHUNK_TARGET_TOKENS,
    overlap_tokens: int = RAG_CHUNK_OVERLAP_TOKENS,
) -> List[dict]:
    """
    Split a grouped speaker transcript into overlapping chunks for
    embedding.

    Algorithm: accumulate speaker turns into the current chunk; once
    adding the next turn would exceed target_tokens, close the current
    chunk, then seed the next chunk with however many trailing turns
    from the just-closed chunk add up to roughly overlap_tokens (so
    context isn't lost at chunk boundaries), and continue from there.
    If the whole transcript is already under target_tokens, this
    produces exactly one chunk — no unnecessary splitting.

    Args:
        speaker_transcript: output of
            transcript_service.group_consecutive_speakers()

    Returns:
        List of {"chunk_number": int, "text": str, "start_time": float,
        "end_time": float}, in chronological order. Empty list if the
        transcript has no usable text.
    """
    turns = [t for t in speaker_transcript if t.get("text", "").strip()]
    if not turns:
        return []

    target_chars = target_tokens * CHARACTERS_PER_TOKEN_ESTIMATE
    overlap_chars = overlap_tokens * CHARACTERS_PER_TOKEN_ESTIMATE

    chunks: List[dict] = []
    current_turns: List[dict] = []
    current_chars = 0

    def flush_current_chunk() -> None:
        if not current_turns:
            return
        text = "\n".join(_turn_text(t) for t in current_turns)
        chunks.append(
            {
                "chunk_number": len(chunks) + 1,
                "text": text,
                "start_time": current_turns[0]["start"],
                "end_time": current_turns[-1]["end"],
            }
        )

    for turn in turns:
        turn_text_len = len(_turn_text(turn))

        if current_turns and current_chars + turn_text_len > target_chars:
            flush_current_chunk()

            # Seed the next chunk with trailing turns from the chunk
            # that was just closed, walking backward until we've
            # covered roughly overlap_chars worth of content.
            overlap_turns: List[dict] = []
            overlap_len = 0
            for prior_turn in reversed(current_turns):
                if overlap_len >= overlap_chars:
                    break
                overlap_turns.insert(0, prior_turn)
                overlap_len += len(_turn_text(prior_turn))

            current_turns = overlap_turns
            current_chars = overlap_len

        current_turns.append(turn)
        current_chars += turn_text_len

    flush_current_chunk()

    logger.info("Transcript chunked into %d chunk(s) for RAG indexing.", len(chunks))
    return chunks
