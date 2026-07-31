"""
transcribe.py

Defines the single POST /transcribe endpoint. Handles receiving the
uploaded file, validating its type, saving it temporarily, calling
the transcription service, and cleaning up afterwards.
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.transcription_service import transcribe_audio
from app.services.diarization_service import diarize_audio
from app.services.transcript_service import (
    merge_transcript,
    group_consecutive_speakers,
    print_merged_transcript,
)

router = APIRouter()

# File extensions we accept, matching the spec (mp4, mp3, wav, m4a).
ALLOWED_EXTENSIONS = {".mp4", ".mp3", ".wav", ".m4a"}

# Directory where uploads are temporarily stored before/while being
# processed. Resolved relative to the backend/ directory so it works
# regardless of the working directory uvicorn is started from.
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def _validate_file_extension(filename: str) -> str:
    """Return the lowercase extension if allowed, else raise a 400."""
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{extension}'. "
                f"Supported types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )
    return extension


@router.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """
    Accept an uploaded meeting recording, transcribe it with Whisper,
    diarize it with PyAnnote, merge both into a speaker-labelled
    transcript, and return everything.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    extension = _validate_file_extension(file.filename)

    temp_filename = f"{uuid.uuid4().hex}{extension}"
    temp_path = UPLOAD_DIR / temp_filename

    try:
        # Stream the upload to disk.
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with open(temp_path, "wb") as f:
            f.write(contents)

        # Run Whisper on the saved file.
        print("File exists before Whisper:", temp_path.exists())
        transcription = transcribe_audio(str(temp_path))
        whisper_segments = transcription["segments"]

        print("File exists after Whisper:", temp_path.exists())

        speaker_segments = diarize_audio(str(temp_path))

        print("File exists after PyAnnote:", temp_path.exists())

        # Merge Whisper's text segments with PyAnnote's speaker segments
        # (maximum-overlap matching), then combine consecutive same-speaker
        # segments into single turns for a readable final transcript.
        merged_transcript = merge_transcript(whisper_segments, speaker_segments)
        speaker_transcript = group_consecutive_speakers(merged_transcript)
        print_merged_transcript(speaker_transcript)

        return {
            "status": "success",
            "text": transcription["text"],
            "segments": whisper_segments,
            "speakers": speaker_segments,
            "merged": merged_transcript,
            "transcript": speaker_transcript,
        }

    except HTTPException:
        raise

    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}"
        )

    finally:
        if temp_path.exists():
            os.remove(temp_path)