"""
user_repository.py

Pure data-access layer for the User model — no password hashing, no
JWT handling, no business logic. See services/auth_service.py for
that. Same pattern as repositories/meeting_repository.py: this class
adds/flushes but never commits or rolls back — the service layer owns
the transaction boundary.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Data-access methods for User."""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, full_name: str, email: str, password_hash: str) -> User:
        """
        Add a new user to the session and flush so its generated id and
        timestamps are populated. Does NOT commit — the caller controls
        the transaction boundary.
        """
        user = User(full_name=full_name, email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.flush()
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        """Return the user with this email, or None if no such user exists."""
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Return the user with this id, or None if no such user exists."""
        return self.db.get(User, user_id)

    def email_exists(self, email: str) -> bool:
        """Return True if a user with this email is already registered."""
        return self.get_by_email(email) is not None
