import { ChangeEvent, FormEvent, useState } from "react";
import { authFetch } from "../../auth";
import { API_BASE_URL } from "../../services/api";
import Button from "../ui/Button";
import { Card } from "../ui/Card";
import { TranscribeResponse } from "../../types/meeting";

interface MeetingUploadProps {
  onUploaded: (meetingId: string) => void;
  onCancel: () => void;
}

type UploadState = "idle" | "uploading" | "error";

function MeetingUpload({ onUploaded, onCancel }: MeetingUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(event.target.files?.[0] ?? null);
    setErrorMessage(null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedFile) {
      setErrorMessage("Choose a recording first.");
      return;
    }

    setState("uploading");
    setErrorMessage(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await authFetch(`${API_BASE_URL}/transcribe`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed.");
      }

      const result = data as TranscribeResponse;
      onUploaded(result.meeting_id);
    } catch (err) {
      setState("error");
      setErrorMessage(err instanceof Error ? err.message : "Upload failed. Please try again.");
    }
  };

  const isUploading = state === "uploading";

  return (
    <div className="page-shell">
      <div className="page-head">
        <div>
          <h1>New meeting</h1>
          <p className="page-sub">
            Upload a recording. It's transcribed, diarized, and analyzed automatically.
          </p>
        </div>
        <Button variant="ghost" onClick={onCancel} disabled={isUploading}>
          Cancel
        </Button>
      </div>

      <Card className="upload-panel">
        <form onSubmit={handleSubmit}>
          <label className="upload-dropzone" htmlFor="meeting-file">
            <input
              id="meeting-file"
              type="file"
              accept=".mp4,.mp3,.wav,.m4a"
              onChange={handleFileChange}
              disabled={isUploading}
            />
            <span className="upload-dropzone-title">
              {selectedFile ? selectedFile.name : "Choose an audio or video file"}
            </span>
            <span className="upload-dropzone-hint">MP3, WAV, M4A, or MP4</span>
          </label>

          <Button type="submit" block disabled={isUploading || !selectedFile}>
            {isUploading ? "Uploading & processing…" : "Upload & process"}
          </Button>
        </form>

        {isUploading && (
          <p className="status upload-status">
            Transcribing with Whisper, identifying speakers, and generating meeting intelligence
            with Gemini — this can take a few minutes for longer recordings. Don't close this tab.
          </p>
        )}

        {errorMessage && (
          <div className="callout-error" role="alert">
            {errorMessage}
          </div>
        )}
      </Card>
    </div>
  );
}

export default MeetingUpload;
