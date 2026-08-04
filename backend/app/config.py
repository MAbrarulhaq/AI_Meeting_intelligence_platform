"""
config.py

Centralized configuration. All environment-variable reads for the
Gemini/LangChain integration live here, so no other module calls
os.getenv() directly for these values.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------
# Gemini / LangChain configuration (Phase 4)
# ---------------------------------------------------------------------

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configurable model name - never hardcoded in llm/model.py.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))


def require_google_api_key() -> str:
    """
    Return the configured Google AI Studio API key, or raise a clear
    error if it's missing.

    Called lazily (only when a Gemini request is actually made), not
    at import time — so the rest of the app (Whisper, PyAnnote) keeps
    working even if Gemini isn't configured yet.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your backend/.env file "
            "(get a key from Google AI Studio)."
        )
    return GOOGLE_API_KEY