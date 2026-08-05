"""
base.py

The declarative base class every ORM model inherits from. Kept in its
own tiny module (rather than in connection.py or a models file) so
both `app/models/*` and `migrations/env.py` can import it without
pulling in the engine or any model-specific code.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models in this project."""

    pass
