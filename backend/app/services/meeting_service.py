"""
meeting_service.py

Orchestrates meeting intelligence generation. Decides between a
single Gemini request or Map-Reduce chunking based on transcript
size, then flattens the Pydantic result into the plain dict shape
the API route (and frontend) already expect.

This is the ONLY function the API route calls for Phase 4 — it
doesn't need to know anything about LangChain, Gemini, or chunking.
"""

import logging
from typing import List

from app.llm.schemas import MeetingIntelligence
from app.llm.summarizer import reduce_intelligence, summarize_chunk, summarize_transcript
from app.services.chunking_service import (
    chunk_speaker_transcript,
    estimate_token_count,
    format_speaker_transcript,
    needs_chunking,
)

logger = logging.getLogger(__name__)


def _empty_intelligence() -> dict:
    """Structured result returned when there's no transcript content to analyze."""
    return {
        "summary": "No meeting content available to analyze.",
        "action_items": [],
        "decisions": [],
        "deadlines": [],
        "key_topics": [],
    }


def _to_response_dict(result: MeetingIntelligence) -> dict:
    """
    Flatten the Pydantic MeetingIntelligence into the plain dict shape
    the API/frontend expect: decisions/deadlines/key_topics as plain
    string lists (not lists of {"decision": "..."} objects), matching
    the response contract already wired into transcribe.py and App.tsx.
    """
    return {
        "summary": result.summary,
        "action_items": [item.model_dump() for item in result.action_items],
        "decisions": [d.decision for d in result.decisions],
        "deadlines": [d.deadline for d in result.deadlines],
        "key_topics": [t.topic for t in result.key_topics],
    }


def generate_meeting_intelligence(speaker_transcript: List[dict]) -> dict:
    """
    Public entrypoint used by the API route. Takes the grouped speaker
    transcript and returns structured meeting intelligence as a plain
    dict — a single Gemini request for short meetings, Map-Reduce
    chunking for long ones.

    Args:
        speaker_transcript: output of
            transcript_service.group_consecutive_speakers()

    Returns:
        dict with keys: summary, action_items, decisions, deadlines, key_topics

    Raises:
        RuntimeError: on any unrecoverable failure (missing config,
            Gemini errors, invalid output). The API route is
            responsible for turning this into an HTTP error response.
    """
    if not speaker_transcript:
        logger.info("Empty transcript - skipping Gemini call")
        return _empty_intelligence()

    transcript_text = format_speaker_transcript(speaker_transcript)
    if not transcript_text.strip():
        logger.info("Transcript had no usable text - skipping Gemini call")
        return _empty_intelligence()

    logger.info(
        "Transcript size: %d characters (~%d tokens estimated)",
        len(transcript_text),
        estimate_token_count(transcript_text),
    )

    if not needs_chunking(transcript_text):
        result = summarize_transcript(transcript_text)
        

        return _to_response_dict(result)

    # Long transcript - Map-Reduce.
    chunks = chunk_speaker_transcript(speaker_transcript)
    partial_results: List[MeetingIntelligence] = []

    for index, chunk_text in enumerate(chunks, start=1):
        try:
            partial = summarize_chunk(chunk_text, index, len(chunks))
        except RuntimeError as exc:
            # Fail loudly with context about which chunk failed, rather
            # than silently producing an incomplete meeting summary.
            raise RuntimeError(f"Failed to analyze chunk {index}/{len(chunks)}: {exc}") from exc
        partial_results.append(partial)

    final_result = reduce_intelligence(partial_results)
    return _to_response_dict(final_result)