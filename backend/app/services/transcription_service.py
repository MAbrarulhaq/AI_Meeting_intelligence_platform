"""
transcription_service.py

Responsible for turning an audio/video file on disk into text using
OpenAI's Whisper model. The Whisper model is expensive to load into
memory, so we load it exactly once (on first use) and reuse it for
every subsequent request.
"""

import whisper
from functools import lru_cache


# Whisper model size to use. "base" is a good balance of speed vs.
# accuracy for an MVP running on CPU.
WHISPER_MODEL_SIZE = "small"


@lru_cache(maxsize=1)
def get_whisper_model():
    """
    Load and cache the Whisper model.

    Using lru_cache(maxsize=1) means the (slow) model load only
    happens once per server process, on the first call. Every
    later call returns the already-loaded model instantly.
    """
    print(f"Loading Whisper '{WHISPER_MODEL_SIZE}' model (first request only)...")
    model = whisper.load_model(WHISPER_MODEL_SIZE)
    print("Whisper model loaded.")
    return model


def transcribe_audio(file_path: str) -> str:
    """
    Transcribe the audio/video file at `file_path` and return the
    resulting text.

    Raises:
        RuntimeError: if Whisper fails to process the file (e.g. the
            file is corrupted, unreadable, or ffmpeg can't decode it).
    """
    model = get_whisper_model()
    print("Now transcribing the audio.")


    try:
        # fp16=False keeps this safe on machines without a supported
        # GPU (Whisper otherwise warns/falls back automatically, but
        # being explicit avoids noisy warnings on CPU-only setups).
        result = model.transcribe(file_path, language="en", fp16=False)
    except Exception as exc:
        # Wrap the low-level Whisper/ffmpeg error in a clearer message
        # for the API layer to surface to the frontend.
        raise RuntimeError(f"Whisper failed to transcribe the file: {exc}") from exc

    transcription_text = result.get("text", "").strip()
    segments = result.get("segments", [])

    if not transcription_text:
        raise RuntimeError("Whisper returned an empty transcription.")

    return{
        "text": transcription_text,
        "segments": segments
    }

