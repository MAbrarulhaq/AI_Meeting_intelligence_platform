"""
model.py

Responsible ONLY for creating and caching the Gemini chat model via
LangChain. No prompt or chain logic lives here — see prompt.py and
summarizer.py for that.
"""

import logging
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GEMINI_MODEL, GEMINI_TEMPERATURE, require_google_api_key

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_gemini_model() -> ChatGoogleGenerativeAI:
    """
    Create and cache the Gemini chat model — same caching pattern used
    for the Whisper model and PyAnnote pipeline elsewhere in this
    project (lru_cache means this only runs once per server process).

    Raises:
        RuntimeError: if GOOGLE_API_KEY isn't configured.
    """
    api_key = require_google_api_key()

    logger.info("Loading Gemini model '%s'...", GEMINI_MODEL)
    
    model = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=api_key,
        temperature=GEMINI_TEMPERATURE,
    )
    logger.info("Gemini model cached.")
    logger.info("Gemini model initialized successfully.")
    return model