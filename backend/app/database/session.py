"""
session.py

Provides a cached session factory and get_db(), a FastAPI dependency
that yields one Session per request and guarantees it's closed
afterward — regardless of whether the request succeeded or raised.
"""

import logging
from functools import lru_cache
from typing import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import get_engine

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_session_factory() -> sessionmaker:
    """
    Build and cache the sessionmaker. Cached (not built at import time)
    for the same reason get_engine() is lazy — so importing this module
    doesn't require the database to be configured yet.
    """
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a Session for the lifetime of one
    request. Commit/rollback is the caller's responsibility (see
    repositories/meeting_repository.py) — this only guarantees the
    session is always closed afterward.
    """
    session_factory = _get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
