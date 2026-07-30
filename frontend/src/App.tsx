import { useState, ChangeEvent, FormEvent } from "react";

// Backend base URL. Hardcoded for the MVP since there's only one
// environment to worry about (local dev).
const API_BASE_URL = "http://localhost:8000";

interface WhisperSegment {
  id: number;
  start: number;
  end: number;
  text: string;
}

interface TranscribeResponse {
  status: string;
  text: string;
  segments: WhisperSegment[];
}

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transcription, setTranscription] = useState<string>("");
  const [segments, setSegments] = useState<WhisperSegment[]>([]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    // Clear stale results when a new file is picked.
    setErrorMessage(null);
    setTranscription("");
    setSegments([]);
  };

  const handleUpload = async (event: FormEvent) => {
    event.preventDefault();

    if (!selectedFile) {
      setErrorMessage("Please choose a file first.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setTranscription("");
    setSegments([]);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(`${API_BASE_URL}/transcribe`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        // FastAPI's HTTPException responses put the message in `detail`.
        throw new Error(data.detail || "Transcription failed.");
      }

      const result = data as TranscribeResponse;
        setTranscription(result.text);
        setSegments(result.segments);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong while uploading.";
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Meeting Transcription (Whisper MVP)</h1>

      <div className="upload-card">
        <form onSubmit={handleUpload}>
          <input
            type="file"
            accept=".mp4,.mp3,.wav,.m4a"
            onChange={handleFileChange}
          />
          <button type="submit" disabled={isLoading || !selectedFile}>
            {isLoading ? "Transcribing..." : "Upload & Transcribe"}
          </button>
        </form>

        {isLoading && (
          <p className="status">
            Processing audio with Whisper — this can take a bit for longer
            recordings...
          </p>
        )}

        {errorMessage && <p className="status error">{errorMessage}</p>}

        <textarea
          className="transcription-box"
          placeholder="Transcription will appear here..."
          value={transcription}
          readOnly
        />

        {segments.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h2>Whisper Segments</h2>

          {segments.map((segment) => (
            <div
              key={segment.id}
              style={{
                border: "1px solid #ddd",
                padding: "10px",
                marginBottom: "10px",
                borderRadius: "8px",
              }}
            >
              <strong>
                {segment.start.toFixed(2)}s → {segment.end.toFixed(2)}s
              </strong>

            <p>{segment.text}</p>
        </div>
    ))}
  </div>
)}



      </div>
    </div>
  );
}

export default App;
