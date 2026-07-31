"""
diarization_service.py

Responsible for figuring out "who spoke when" in an audio file using
PyAnnote's pretrained speaker diarization pipeline.

This module is intentionally independent from transcription_service.py
for this phase — it takes the same file path Whisper already used, but
does not know or care about Whisper's output. Merging the two happens
later in Phase 3 (transcript_service.py).
"""

import os
import subprocess
import tempfile
from functools import lru_cache

from dotenv import load_dotenv
from pyannote.audio import Pipeline

# Load variables from your .env file (specifically HF_TOKEN) into the
# process environment. Safe to call even if some variables are already set.
load_dotenv()

# The gated HuggingFace pipeline that does segmentation + embedding +
# clustering under the hood to produce speaker turns.
DIARIZATION_MODEL_NAME = "pyannote/speaker-diarization-3.1"


@lru_cache(maxsize=1)
def get_diarization_pipeline() -> Pipeline:
    """
    Load and cache the PyAnnote diarization pipeline.

    Why caching matters here (same idea as Whisper's get_whisper_model):
    loading this pipeline means downloading/initializing several
    sub-models (segmentation, embedding, clustering). That's slow and
    memory-heavy, so we only want to do it once per server process —
    not once per upload. lru_cache(maxsize=1) stores the single
    resulting Pipeline object and returns it instantly on every call
    after the first.

    Raises:
        RuntimeError: if HF_TOKEN is missing, or the model fails to
            load (commonly because the gated model terms haven't been
            accepted on HuggingFace for both speaker-diarization-3.1
            and segmentation-3.0).
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError(
            "HF_TOKEN is not set. Add it to your backend/.env file — "
            "it's required to download the gated pyannote model."
        )

    print(f"Loading PyAnnote pipeline '{DIARIZATION_MODEL_NAME}' (first request only)...")
    try:
        pipeline = Pipeline.from_pretrained(
            DIARIZATION_MODEL_NAME,
            use_auth_token=hf_token,
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to load the PyAnnote pipeline. Common causes: "
            "invalid HF_TOKEN, or the gated model terms haven't been "
            "accepted for 'pyannote/speaker-diarization-3.1' and "
            f"'pyannote/segmentation-3.0' on HuggingFace. Original error: {exc}"
        ) from exc

    print("PyAnnote pipeline loaded.")
    return pipeline


def _convert_to_wav(file_path: str) -> str:
    """
    Convert any input audio/video file to a temporary 16kHz mono WAV file.

    Why this is needed: PyAnnote loads audio through `soundfile`, which
    only understands uncompressed/lossless containers (wav, flac, ogg).
    It cannot decode compressed containers like mp4, m4a, or mp3 —
    that's the "Format not recognised" error. Whisper doesn't hit this
    because it calls ffmpeg internally; PyAnnote does not, so we do the
    conversion ourselves here using the ffmpeg binary already required
    for Whisper.

    Returns:
        Path to a temporary .wav file. Caller is responsible for
        deleting it once diarization is done.

    Raises:
        RuntimeError: if ffmpeg is missing or the conversion fails.
    """
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)  # we only need the path; ffmpeg will write to it

    command = [
        "ffmpeg",
        "-y",  # overwrite the empty temp file ffmpeg just created
        "-i", file_path,
        "-ar", "16000",  # PyAnnote's pipelines expect 16kHz audio
        "-ac", "1",      # mono
        wav_path,
    ]

    result = subprocess.run(command, capture_output=True)

    if result.returncode != 0:
        # Clean up the (empty/partial) temp file before raising.
        if os.path.exists(wav_path):
            os.remove(wav_path)
        stderr_text = result.stderr.decode(errors="ignore")
        raise RuntimeError(
            f"ffmpeg failed to convert '{file_path}' to WAV for diarization: {stderr_text}"
        )

    return wav_path


def diarize_audio(file_path: str) -> list[dict]:
    """
    Run speaker diarization on the audio file at `file_path`.

    Accepts the SAME saved upload path that transcribe_audio() uses —
    no separate upload, no separate endpoint. Internally converts to a
    temporary WAV file first (see _convert_to_wav), since PyAnnote
    can't read compressed containers directly.

    Returns:
        A list of speaker segments, e.g.:
        [
            {"speaker": "SPEAKER_00", "start": 0.00, "end": 5.20},
            {"speaker": "SPEAKER_01", "start": 5.20, "end": 9.85},
            ...
        ]

    Raises:
        RuntimeError: if conversion or the pipeline fails.
    """
    pipeline = get_diarization_pipeline()
    wav_path = _convert_to_wav(file_path)

    try:
        diarization_result = pipeline(wav_path)
    except Exception as exc:
        raise RuntimeError(f"PyAnnote failed to diarize the file: {exc}") from exc
    finally:
        # Always clean up the temp WAV, whether diarization succeeded or not.
        if os.path.exists(wav_path):
            os.remove(wav_path)

    speaker_segments: list[dict] = []

    # itertracks yields (Segment, track_id, speaker_label) tuples in
    # chronological order.
    for turn, _, speaker in diarization_result.itertracks(yield_label=True):
        segment = {
            "speaker": speaker,
            "start": round(turn.start, 2),
            "end": round(turn.end, 2),
        }
        speaker_segments.append(segment)

        # Step 4 requirement: print each segment to the terminal for
        # manual verification.
        print(f"{segment['speaker']}")
        print(f"{segment['start']:.2f} --> {segment['end']:.2f}\n")

    return speaker_segments