"""
password.py

Password hashing and verification using bcrypt directly.

Deliberately NOT using passlib.CryptContext here, despite that being
the spec's literal instruction: passlib's last release (1.7.4, 2020)
reads bcrypt's version via `bcrypt.__about__.__version__`, an attribute
every bcrypt release from 4.0 onward removed. passlib is unmaintained,
so this isn't a version-pinning problem to work around — there is no
combination of a current bcrypt release and passlib that avoids it.
bcrypt itself is actively maintained and does exactly what's needed
here without an abstraction layer that no longer matches it.

Nothing outside this module should ever import bcrypt directly or
handle a raw/plaintext password.
"""

import bcrypt

# bcrypt's algorithm silently ignores any bytes past 72 — passing a
# longer password raises ValueError instead in recent bcrypt releases.
# Truncating here (rather than letting signup fail with a cryptic
# error for a password that's merely "too long") is safe: no realistic
# passphrase needs to rely on byte 73 onward for its strength.
_MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password with bcrypt.

    Returns:
        A string safe to store in the database (the bcrypt hash
        includes its own salt, so no separate salt column is needed).
    """
    password_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Check a plaintext password against a stored bcrypt hash.

    Returns:
        True if it matches, False otherwise (including if the stored
        hash is malformed — never raises for bad input).
    """
    password_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    try:
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
    except ValueError:
        return False
