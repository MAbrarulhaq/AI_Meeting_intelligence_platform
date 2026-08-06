"""
dependencies.py

FastAPI dependencies for authentication. get_current_user() is what
protects a route — add `current_user: User = Depends(get_current_user)`
to any endpoint's signature to require a valid JWT.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.jwt import decode_access_token

# Reads the "Authorization: Bearer <token>" header. auto_error=True
# means FastAPI itself returns 401 if the header is missing entirely,
# before this function's body even runs.
_bearer_scheme = HTTPBearer(auto_error=True)


def _unauthorized() -> HTTPException:
    """One consistent 401 for every way a token can fail to validate."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Verify the bearer token from the Authorization header and return
    the authenticated User.

    Raises:
        HTTPException(401): if the token is missing, invalid, expired,
            references a user id that isn't a valid UUID, or that user
            no longer exists.
    """
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise _unauthorized()

    subject = payload.get("sub")
    if subject is None:
        raise _unauthorized()

    try:
        user_id = uuid.UUID(subject)
    except (ValueError, TypeError):
        raise _unauthorized()

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise _unauthorized()

    return user
