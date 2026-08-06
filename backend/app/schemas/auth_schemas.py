"""
auth_schemas.py

Pydantic request/response models for authentication. UserResponse
never includes password_hash — it's not even a field on this model,
so there's no way to accidentally serialize it.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """POST /auth/register request body."""

    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """POST /auth/login request body."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user profile — returned by /auth/register, /auth/login, /auth/me."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    """Returned by /auth/register and /auth/login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Shape of the decoded JWT payload (for typing/reference, not enforced at decode time)."""

    sub: Optional[str] = None
    exp: Optional[int] = None
