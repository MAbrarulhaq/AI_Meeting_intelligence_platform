"""
chunking_service.py

Splits a long grouped speaker transcript into token-aware chunks for
Map-Reduce processing when it's too large for a single Gemini request.
Chunk boundaries always fall on speaker-turn edges, never mid-sentence,
and chronological order is preserved.

Lives in services/ rather than llm/ deliberately: this is business
logic about how *this app's* transcripts are structured (a list of
speaker turns), not something specific to the LLM or LangChain.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Gemini 2.5 Flash's context window is large, but chunks are kept
# deliberately small for cost, latency, and output-quality reasons —
# a very large single context tends to produce vaguer, less specific
# summaries than focused chunks processed via Map-Reduce.
MAX_CHUNK_CHARACTERS = 12_000

# There's no official offline Gemini tokenizer bundled with the SDK,
# so this uses a standard rough approximation (~4 characters per
# token, consistent with most English-language LLM tokenizers) purely
# to log an estimate. It does not need to be exact — actual chunking
# is done by character count, which is deterministic and sufficient.
CHARACTERS_PER_TOKEN_ESTIMATE = 4


def estimate_token_count(text: str) -> int:
    """Rough token estimate, used only for logging/visibility."""
    return max(1, len(text) // CHARACTERS_PER_TOKEN_ESTIMATE)


def format_speaker_transcript(speaker_transcript: List[dict]) -> str:
    """
    Convert the grouped speaker transcript into plain readable
    conversation text — the same representation used for both the
    single-request and chunked paths, e.g.:

        SPEAKER_00:
        Hello everyone.

        SPEAKER_01:
        Good morning.

    Args:
        speaker_transcript: output of
            transcript_service.group_consecutive_speakers()

    Returns:
        A formatted string. Empty string if there's no usable text.
    """
    lines = []
    for entry in speaker_transcript:
        speaker = entry.get("speaker", "UNKNOWN")
        text = entry.get("text", "").strip()
        if not text:
            continue
        lines.append(f"{speaker}:\n{text}")
    return "\n\n".join(lines)


def needs_chunking(transcript_text: str) -> bool:
    """Decide whether the transcript is small enough for a single request."""
    return len(transcript_text) > MAX_CHUNK_CHARACTERS


def chunk_speaker_transcript(speaker_transcript: List[dict]) -> List[str]:
    """
    Split the grouped speaker transcript into chunks, each under
    MAX_CHUNK_CHARACTERS, breaking only on speaker-turn boundaries
    (never mid-sentence) and preserving chronological order.

    Args:
        speaker_transcript: output of
            transcript_service.group_consecutive_speakers()

    Returns:
        A list of formatted transcript-text chunks, in chronological order.
    """
    chunks: List[str] = []
    current_lines: List[str] = []
    current_length = 0

    for entry in speaker_transcript:
        speaker = entry.get("speaker", "UNKNOWN")
        text = entry.get("text", "").strip()
        if not text:
            continue

        turn_text = f"{speaker}:\n{text}"

        # Close out the current chunk before adding this turn if doing
        # so would exceed the limit — unless the chunk is still empty,
        # in which case an unusually long single turn just becomes its
        # own (oversized) chunk rather than being split mid-sentence.
        if current_lines and current_length + len(turn_text) > MAX_CHUNK_CHARACTERS:
            chunks.append("\n\n".join(current_lines))
            current_lines = []
            current_length = 0

        current_lines.append(turn_text)
        current_length += len(turn_text)

    if current_lines:
        chunks.append("\n\n".join(current_lines))

    logger.info("Transcript chunked into %d chunk(s).", len(chunks))
    return chunks