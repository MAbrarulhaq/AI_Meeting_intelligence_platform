# Meeting Transcription MVP (Whisper only)

Single-page React app → FastAPI backend → OpenAI Whisper (`base` model).
Upload a recording, get the transcription back. No auth, no DB, no other
AI features — just the transcription pipeline, per spec.

## Structure

```
meeting-transcriber/
  backend/
    requirements.txt
    uploads/                      # temp storage, auto-cleaned per request
    app/
      main.py                     # FastAPI app + CORS
      api/transcribe.py           # POST /transcribe route
      services/transcription_service.py  # Whisper model + transcribe logic
  frontend/
    package.json
    src/App.tsx                   # the entire UI
```

## 1. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

FFmpeg must be installed and on your PATH (you said it already is).

Run it:

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000` — you should see `{"status": "ok", ...}`.

The **first** transcription request will be slow because it downloads and
loads the Whisper `base` model (~140MB) into memory. Every request after
that reuses the cached model.

## 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`.

## 3. Test it

1. Start the backend (port 8000), then the frontend (port 5173).
2. On the page, pick a short `.mp3`/`.wav`/`.m4a`/`.mp4` file.
3. Click "Upload & Transcribe".
4. Wait for the loading message to clear — transcription appears in the box.
5. Try an unsupported file type (e.g. `.txt`) to confirm you get a clean
   error message instead of a crash.

## Workflow recap

`User picks file → clicks upload → React sends multipart/form-data POST to
/transcribe → FastAPI saves it to backend/uploads/ → transcription_service
runs Whisper on it → text is returned as JSON → React renders it → temp
file is deleted.`

## Known limitations (intentional, for this milestone)

- No persistence — refresh the page and the transcription is gone.
- No speaker diarization — it's a single blob of text, not per-speaker.
- No progress bar — just an indeterminate "processing" message; long
  recordings can take a while on CPU.
- `base` model favors speed over accuracy — larger models (`small`,
  `medium`) transcribe better but slower.
- CORS is wide open to `localhost:5173` only, for local dev — not
  production-hardened.
- No file size cap — a very large upload will just take a long time / use
  a lot of memory.

## What I'd extend first

1. **Progress feedback** — stream partial progress (or at least an
   estimated time) instead of a static "processing" message; long files
   currently look frozen.
2. **Async/background processing** — right now `/transcribe` blocks until
   Whisper finishes. For real meeting-length audio, move this to a
   background task/queue (e.g. FastAPI `BackgroundTasks` + polling, or
   Celery) so the request doesn't time out.
3. **Persistence** — save the transcript (and maybe the audio) to a
   database so it survives a refresh — this is the natural next
   milestone before adding summaries/diarization/RAG.
4. **File size / duration limits** — reject absurdly large uploads before
   they hit Whisper, with a clear error.
