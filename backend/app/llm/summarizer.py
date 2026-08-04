"""
summarizer.py

Builds the LangChain LCEL pipelines: PromptTemplate | Gemini (bound to
a structured-output schema) -> MeetingIntelligence. No manual JSON
parsing or string manipulation anywhere here — with_structured_output()
and the Pydantic schemas in schemas.py handle that entirely.

Three entrypoints, matching the three prompts in prompt.py:
- summarize_transcript: single-request path for short transcripts.
- summarize_chunk: Map step, one chunk of a long transcript.
- reduce_intelligence: Reduce step, merges partial results into one.
"""

import logging
from typing import List

from google.genai import errors as genai_errors
from langchain_core.exceptions import OutputParserException

from app.llm.model import get_gemini_model
from app.llm.prompt import MAP_CHUNK_PROMPT, MEETING_ANALYSIS_PROMPT, REDUCE_PROMPT
from app.llm.schemas import MeetingIntelligence

logger = logging.getLogger(__name__)


def _structured_model():
    """Return the Gemini model bound to the MeetingIntelligence output schema."""
    return get_gemini_model().with_structured_output(MeetingIntelligence)


def _safe_invoke(chain, payload: dict, step_name: str) -> MeetingIntelligence:
    """
    Invoke an LCEL chain and translate any failure into a clear
    RuntimeError. Centralizes error handling so summarize_transcript,
    summarize_chunk, and reduce_intelligence don't each repeat it.

    Raises:
        RuntimeError: on auth failure, rate limiting, server errors,
            malformed output, or any other unrecoverable failure.
    """
    try:
        return chain.invoke(payload)
    except OutputParserException as exc:
        raise RuntimeError(
            f"Gemini's response could not be parsed into the expected structure during {step_name}."
        ) from exc
    except genai_errors.ClientError as exc:
        # 4xx errors from the Gemini API - inspect the status code for
        # a more specific, actionable message.
        code = getattr(exc, "code", None)
        if code == 401 or code == 403:
            raise RuntimeError(
                f"Gemini authentication failed during {step_name}. Check that GOOGLE_API_KEY in your .env is valid."
            ) from exc
        if code == 429:
            raise RuntimeError(
                f"Gemini rate limit reached during {step_name}. Please wait a moment and try again."
            ) from exc
        raise RuntimeError(f"Gemini rejected the request during {step_name}: {exc}") from exc
    except genai_errors.ServerError as exc:
        raise RuntimeError(
            f"Gemini is currently unavailable during {step_name}. Please try again shortly."
        ) from exc
    except genai_errors.APIError as exc:
        raise RuntimeError(f"Gemini returned an error during {step_name}: {exc}") from exc
    except Exception as exc:
        # Catch-all so no unexpected exception (network failure, timeout,
        # etc.) ever escapes this module unformatted.
        raise RuntimeError(f"Unexpected error during {step_name}: {exc}") from exc


def summarize_transcript(transcript_text: str) -> MeetingIntelligence:
    """
    Single-request path: the whole transcript fits comfortably within
    one Gemini request. Used when chunking_service determines the
    transcript is small enough (see services/meeting_service.py).
    """
    chain = MEETING_ANALYSIS_PROMPT | _structured_model()
    logger.info("Running single-request meeting analysis...")
    result = _safe_invoke(chain, {"transcript": transcript_text}, "single-request analysis")
    logger.info("Meeting intelligence generated successfully.")
    return result


def summarize_chunk(chunk_text: str, chunk_index: int, chunk_total: int) -> MeetingIntelligence:
    """Map step: analyze one chunk of a long transcript in isolation."""
    chain = MAP_CHUNK_PROMPT | _structured_model()
    logger.info("Running Map phase for chunk %d/%d...", chunk_index, chunk_total)
    return _safe_invoke(
        chain,
        {"transcript": chunk_text, "chunk_index": chunk_index, "chunk_total": chunk_total},
        f"Map phase (chunk {chunk_index}/{chunk_total})",
    )


def reduce_intelligence(partial_results: List[MeetingIntelligence]) -> MeetingIntelligence:
    """
    Reduce step: merge several partial MeetingIntelligence results
    (one per chunk, in chronological order) into a single final
    result, de-duplicated.
    """
    chain = REDUCE_PROMPT | _structured_model()
    logger.info("Running Reduce phase over %d partial result(s)...", len(partial_results))

    partial_json = "\n\n".join(
        f"--- Part {index + 1} ---\n{result.model_dump_json(indent=2)}"
        for index, result in enumerate(partial_results)
    )

    result = _safe_invoke(chain, {"partial_results": partial_json}, "Reduce phase")
    logger.info("Meeting intelligence generated successfully.")
    return result