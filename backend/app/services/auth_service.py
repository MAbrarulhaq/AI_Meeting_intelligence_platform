"""
auth_service.py

Business logic for registration and login. Same pattern as
services/persistence_service.py: owns the transaction boundary around
the repository (commit on success, rollback on failure), and never
lets a raw SQLAlchemy exception escape this module.
"""

import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.jwt import create_access_token
from app.security.password import hash_password, verify_password

logger = logging.getLogger(__name__)


class EmailAlreadyRegisteredError(Exception):
    """Raised when signing up with an email that's already registered."""


class InvalidCredentialsError(Exception):
    """Raised when login email/password don't match an existing account."""


def register_user(db: Session, full_name: str, email: str, password: str) -> User:
    """
    Register a new user: hash the password, create the row, commit.

    Raises:
        EmailAlreadyRegisteredError: if the email is already taken
            (checked up front, and again via the unique constraint in
            case of a race between two concurrent signups).
        RuntimeError: on any other database failure.
    """
    repo = UserRepository(db)

    if repo.email_exists(email):
        raise EmailAlreadyRegisteredError(f"Email '{email}' is already registered.")

    password_hash = hash_password(password)

    try:
        user = repo.create_user(full_name=full_name, email=email, password_hash=password_hash)
        db.commit()
        logger.info("User registered (id=%s)", user.id)
        return user
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegisteredError(f"Email '{email}' is already registered.") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("User registration failed")
        raise RuntimeError(f"Failed to register user: {exc}") from exc


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Verify credentials and return the matching user.

    Raises:
        InvalidCredentialsError: if the email doesn't exist OR the
            password doesn't match — deliberately the same error and
            message for both cases, so a failed login never reveals
            whether a given email is registered.
    """
    user = UserRepository(db).get_by_email(email)

    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Incorrect email or password.")

    return user


def issue_token_for_user(user: User) -> str:
    """Create a signed access token for an already-authenticated user."""
    return create_access_token(subject=str(user.id))
