"""
main.py

FastAPI application entrypoint. Wires up CORS (so the Vite dev
server on a different port can call this API) and registers routes.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.meetings import router as meetings_router
from app.api.transcribe import router as transcribe_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Meeting Transcription MVP")

# Allow the local Vite dev server to call this API. This is a
# development-only, permissive CORS setup — tighten it before any
# real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcribe_router)
app.include_router(meetings_router)


@app.get("/")
async def health_check():
    """Simple health check so you can confirm the server is up."""
    return {"status": "ok", "service": "meeting-transcription-mvp"}
