"""
connection.py

Builds and caches the SQLAlchemy engine (which owns the connection
pool). Only engine/pool setup lives here — sessions live in
session.py, models live in app/models/.
"""

import logging
from app.config import require_database_url
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import require_database_url

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Create and cache the SQLAlchemy engine — same lazy-caching pattern
    used for the Whisper model, PyAnnote pipeline, and Gemini client
    elsewhere in this project.

    Lazy on purpose: the app can still start up (and serve Whisper/
    PyAnnote/Gemini requests) even if the database isn't configured or
    reachable yet. The error only surfaces on the first actual DB
    operation, not at import time.

    Raises:
        RuntimeError: if the database isn't configured (see
            config.require_database_url).
    """
    database_url = require_database_url()
    print(database_url)

    logger.info("Creating database engine...")
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # detect and transparently replace dead connections
        pool_size=5,
        max_overflow=10,
        future=True,
    )
    logger.info("Database engine created.")
    return engine
