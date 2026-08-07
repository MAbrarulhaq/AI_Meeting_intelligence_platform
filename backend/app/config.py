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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

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


# ---------------------------------------------------------------------
# Database configuration (Phase 5)
# ---------------------------------------------------------------------

# Either set DATABASE_URL directly, or set the individual DATABASE_*
# variables below and it's assembled automatically. DATABASE_URL takes
# priority if both are present.
_DATABASE_URL_ENV = os.getenv("DATABASE_URL")

DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "meeting_intelligence")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")


def _build_database_url() -> str | None:
    """Assemble a SQLAlchemy database URL from config, or None if unconfigured."""
    if _DATABASE_URL_ENV:
        return _DATABASE_URL_ENV
    if not (DATABASE_HOST and DATABASE_NAME and DATABASE_USER):
        return None
    # postgresql+psycopg: uses the psycopg (v3) driver, per the spec's
    # preference over psycopg2.
    return (
        f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )


DATABASE_URL = _build_database_url()


def require_database_url() -> str:
    """
    Return the assembled database URL, or raise a clear error if the
    database isn't configured at all.

    Called lazily, from database/connection.py, the first time a DB
    connection is actually needed.
    """
    if not DATABASE_URL:
        raise RuntimeError(
            "Database is not configured. Set DATABASE_URL, or set "
            "DATABASE_HOST / DATABASE_NAME / DATABASE_USER (and optionally "
            "DATABASE_PASSWORD / DATABASE_PORT) in your backend/.env file."
        )
    return DATABASE_URL


# ---------------------------------------------------------------------
# JWT / authentication configuration (Phase 6)
# ---------------------------------------------------------------------

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # default 24h


def require_jwt_secret_key() -> str:
    """
    Return the configured JWT signing secret, or raise a clear error if
    it's missing.

    Called lazily, from security/jwt.py, the first time a token is
    actually created or decoded — so the rest of the app (Whisper,
    PyAnnote, Gemini, unauthenticated routes) keeps working even if
    this isn't configured yet.
    """
    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY is not set. Add it to your backend/.env file "
            "(use a long, random string — e.g. `openssl rand -hex 32`)."
        )
    return JWT_SECRET_KEY


# ---------------------------------------------------------------------
# RAG / Vector store configuration (Phase 7)
# ---------------------------------------------------------------------

# Gemini's embedding model, used only for turning text into vectors -
# distinct from GEMINI_MODEL above, which generates chat/JSON answers.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

# Local, on-disk ChromaDB store. A PersistentClient (not a separate
# Chroma server) keeps this consistent with the project's local-dev-
# friendly setup elsewhere (e.g. PostgreSQL is the only external
# service actually required to run this app).
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

# Chunk sizing for the RAG index (distinct from services/chunking_service.py,
# which chunks for Gemini's Map-Reduce summarization with different,
# larger targets and no overlap - these two chunkers serve different
# purposes and are intentionally not shared).
RAG_CHUNK_TARGET_TOKENS = int(os.getenv("RAG_CHUNK_TARGET_TOKENS", "900"))
RAG_CHUNK_OVERLAP_TOKENS = int(os.getenv("RAG_CHUNK_OVERLAP_TOKENS", "125"))

# How many chunks to retrieve per chat question.
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
