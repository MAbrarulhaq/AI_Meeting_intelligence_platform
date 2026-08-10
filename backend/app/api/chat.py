"""
chat.py

RAG chatbot endpoint. Thin route — all retrieval/generation logic
lives in services/chat_service.py (which delegates to rag_service.py,
embedding_service.py, and vector_store_service.py). No SQLAlchemy or
Chroma code here.

SECURITY: current_user comes exclusively from the verified JWT via
get_current_user. The request body (ChatRequest) has no user_id
field, and none would be trusted if it did — ownership is determined
the same way as every other endpoint in this project.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.schemas.chat_schemas import ChatRequest, ChatResponse
from app.security.dependencies import get_current_user
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    """Answer a question about the authenticated user's own meetings."""
    try:
        return chat_service.answer_question(
            user_id=current_user.id,
            question=payload.question,
            meeting_id=payload.meeting_id,
            history=payload.history,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
