"""
rag_service.py

Retrieval-augmented generation for the chatbot: embeds the user's
question, searches ChromaDB (always scoped to the authenticated
user), builds a context string from the retrieved chunks, and asks
Gemini to answer using ONLY that context.

Error handling here mirrors llm/summarizer.py's _safe_invoke pattern.
It's duplicated (not imported from summarizer.py) deliberately —
summarizer.py is a working Phase 4 module this project explicitly
asked not to be modified, and the two call sites want a plain text
answer vs. summarizer.py's structured-output Pydantic result, so
sharing the helper would mean changing summarizer.py's signature for
a phase that isn't supposed to touch it.
"""

import logging
import uuid
from typing import List, Optional

from google.genai import errors as genai_errors
from langchain_core.exceptions import OutputParserException

from app.llm.model import get_gemini_model
from app.llm.prompt import RAG_ANSWER_PROMPT
from app.services import embedding_service, vector_store_service

logger = logging.getLogger(__name__)

NO_CONTEXT_ANSWER = "I couldn't find that information in your meeting history."


def _safe_invoke_text(chain, payload: dict, step_name: str) -> str:
    """
    Invoke an LCEL chain that returns a plain-text Gemini response.
    Supports both string and list-based Gemini content formats.
    """
    try:
        response = chain.invoke(payload)
        content = response.content

        # Gemini/LangChain may return plain text directly.
        if isinstance(content, str):
            return content.strip()

        # Newer Gemini response format:
        # [{"type": "text", "text": "..."}]
        if isinstance(content, list):
            text_parts = []

            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            text_parts.append(text)

                elif hasattr(block, "text"):
                    text = block.text
                    if text:
                        text_parts.append(text)

            return "\n".join(text_parts).strip()

        # Final fallback — guarantee a string.
        return str(content).strip()

    except OutputParserException as exc:
        raise RuntimeError(
            f"Gemini's response could not be parsed during {step_name}."
        ) from exc

    except genai_errors.ClientError as exc:
        code = getattr(exc, "code", None)

        if code in (401, 403):
            raise RuntimeError(
                f"Gemini authentication failed during {step_name}. "
                "Check GOOGLE_API_KEY."
            ) from exc

        if code == 429:
            raise RuntimeError(
                f"Gemini rate limit reached during {step_name}. "
                "Please wait and try again."
            ) from exc

        raise RuntimeError(
            f"Gemini rejected the request during {step_name}: {exc}"
        ) from exc

    except genai_errors.ServerError as exc:
        raise RuntimeError(
            f"Gemini is currently unavailable during {step_name}. "
            "Please try again shortly."
        ) from exc

    except genai_errors.APIError as exc:
        raise RuntimeError(
            f"Gemini returned an error during {step_name}: {exc}"
        ) from exc

    except Exception as exc:
        raise RuntimeError(
            f"Unexpected error during {step_name}: {exc}"
        ) from exc
def retrieve_relevant_chunks(
    question: str,
    user_id: uuid.UUID,
    meeting_id: Optional[uuid.UUID] = None,
    top_k: int = 5,
) -> List[dict]:
    """
    Embed the question and search ChromaDB for the most relevant
    chunks.

    Args:
        user_id: the authenticated user's id. Passed straight into
            vector_store_service.query_chunks(), which filters by it
            inside the Chroma query itself — this function can never
            return another user's chunks, regardless of meeting_id.
        meeting_id: if given, restricts the search to one meeting
            (still additionally filtered by user_id).

    Returns:
        List of {"text", "metadata", "distance"} dicts, best match
        first. Empty list if nothing relevant is found.
    """
    query_embedding = embedding_service.embed_query(question)
    return vector_store_service.query_chunks(
        query_embedding=query_embedding,
        user_id=user_id,
        meeting_id=meeting_id,
        top_k=top_k,
    )


def _build_context(chunks: List[dict]) -> str:
    """Turn retrieved chunks into the context block inserted into the RAG prompt."""
    blocks = []
    for chunk in chunks:
        meta = chunk["metadata"]
        blocks.append(f"[Source: {meta['filename']}, chunk {meta['chunk_number']}]\n{chunk['text']}")
    return "\n\n".join(blocks)


def _build_history_text(history: Optional[List[dict]]) -> str:
    """
    Format prior conversation turns for the prompt's {history} slot.
    Expects dicts already truncated to the last few exchanges by the
    caller (see chat_service.answer_question) — this function doesn't
    re-truncate, it only formats.
    """
    if not history:
        return "(none)"
    lines = [f"{turn['role'].capitalize()}: {turn['content']}" for turn in history]
    return "\n".join(lines)


def generate_answer(question: str, chunks: List[dict], history: Optional[List[dict]] = None) -> str:
    """
    Ask Gemini to answer the question using ONLY the retrieved chunks
    as context — never Gemini's general knowledge. Prior conversation
    turns (if any) are included only to help resolve follow-up
    references, not as a source of facts.

    Returns the fixed "couldn't find" message without calling Gemini
    at all if no chunks were retrieved (nothing to ground an answer
    in, so there's no point spending a request).
    """
    if not chunks:
        return NO_CONTEXT_ANSWER

    context = _build_context(chunks)
    history_text = _build_history_text(history)
    chain = RAG_ANSWER_PROMPT | get_gemini_model()

    logger.info("Generating RAG answer from %d chunk(s), %d prior turn(s)...", len(chunks), len(history or []))
    answer = _safe_invoke_text(
        chain,
        {"context": context, "question": question, "history": history_text},
        "RAG answer generation",
    )
    logger.info("RAG answer generated.")
    return answer
