"""
jwt.py

JWT creation and decoding using python-jose. No HTTP handling and no
database lookups here — see security/dependencies.py for how this
gets turned into an authenticated request.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, require_jwt_secret_key


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    """
    Create a signed JWT for the given subject (the user's id, as a string
    — the standard "sub" claim).

    Args:
        subject: typically str(user.id).
        expires_minutes: overrides the configured default expiry if given.

    Returns:
        The encoded JWT string.
    """
    expire_delta = timedelta(
        minutes=expires_minutes if expires_minutes is not None else JWT_EXPIRE_MINUTES
    )
    expire_at = datetime.now(timezone.utc) + expire_delta
    payload = {"sub": subject, "exp": expire_at}
    return jwt.encode(payload, require_jwt_secret_key(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT's signature and expiry.

    Raises:
        jose.JWTError: if the token is invalid, expired, or tampered
            with. Callers (security/dependencies.py) catch this and
            turn it into a 401.
    """
    return jwt.decode(token, require_jwt_secret_key(), algorithms=[JWT_ALGORITHM])
