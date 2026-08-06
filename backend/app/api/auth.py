"""
auth.py

Authentication routes: register, login, and "who am I". Routes only
validate the request, call auth_service, and shape the response — no
SQL, no password hashing, no JWT logic here.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.auth_schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from app.security.dependencies import get_current_user
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new account and return a token for it immediately (signup logs you in)."""
    try:
        user = auth_service.register_user(
            db, full_name=payload.full_name, email=payload.email, password=payload.password
        )
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    token = auth_service.issue_token_for_user(user)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Verify credentials and return a fresh access token."""
    try:
        user = auth_service.authenticate_user(db, email=payload.email, password=payload.password)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    token = auth_service.issue_token_for_user(user)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Return the authenticated user's profile. Used by the frontend on
    page load to validate a token it already has in localStorage.
    """
    return current_user
