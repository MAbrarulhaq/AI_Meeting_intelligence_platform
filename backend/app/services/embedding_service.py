"""
embedding_service.py

Generates embeddings via the Gemini Embedding API (gemini-embedding-001),
through LangChain — never OpenAI embeddings. Same caching pattern as
llm/model.py: the client is built once per server process, not once
per request.
"""

import logging
from functools import lru_cache
from typing import List

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import EMBEDDING_MODEL, require_google_api_key

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embeddings_client() -> GoogleGenerativeAIEmbeddings:
    """
    Create and cache the Gemini embeddings client.

    Raises:
        RuntimeError: if GOOGLE_API_KEY isn't configured (reuses the
            same key as the chat model — one Google AI Studio key
            covers both).
    """
    api_key = require_google_api_key()

    logger.info("Loading Gemini embeddings model '%s'...", EMBEDDING_MODEL)
    client = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
    logger.info("Gemini embeddings model cached.")
    return client


def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple chunks of text in one batched call — used when
    indexing a meeting's transcript chunks.

    Returns:
        One embedding vector per input text, same order. Empty list
        if texts is empty (avoids an unnecessary API call).
    """
    if not texts:
        return []

    client = get_embeddings_client()
    logger.info("Generating embeddings for %d chunk(s)...", len(texts))
    embeddings = client.embed_documents(texts)
    logger.info("Embeddings generated for %d chunk(s).", len(embeddings))
    return embeddings


def embed_query(text: str) -> List[float]:
    """Embed a single query string — used for the user's chat question."""
    client = get_embeddings_client()
    return client.embed_query(text)
