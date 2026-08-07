import { useState, useEffect, useCallback, ChangeEvent, FormEvent } from "react";
import { authFetch } from "../auth";
import ChatAssistant from "./ChatAssistant";

// Backend base URL. Hardcoded for the MVP since there's only one
// environment to worry about (local dev).
const API_BASE_URL = "http://localhost:8000";

interface WhisperSegment {
  id: number;
  start: number;
  end: number;
  text: string;
}

interface MergedSegment {
  speaker: string;
  start: number;
  end: number;
  text: string;
}

interface ActionItem {
  owner: string;
  task: string;
  deadline: string;
}

interface TranscribeResponse {
  status: string;
  meeting_id: string;
  text: string;
  segments: WhisperSegment[];
  merged: MergedSegment[];
  transcript: MergedSegment[];
  summary: string;
  action_items: ActionItem[];
  decisions: string[];
  deadlines: string[];
  key_topics: string[];
}

// ---------------------------------------------------------------------
// Phase 5: Meeting History types, matching backend/app/schemas/meeting_schemas.py
// ---------------------------------------------------------------------

interface MeetingListItem {
  id: string;
  filename: string;
  created_at: string;
  duration_seconds: number | null;
  summary_preview: string;
}

interface MeetingDetail {
  id: string;
  filename: string;
  created_at: string;
  duration_seconds: number | null;
  transcript: { full_text: string; speaker_transcript: MergedSegment[] } | null;
  summary: { summary_text: string } | null;
  action_items: ActionItem[];
  decisions: string[];
  deadlines: string[];
  key_topics: string[];
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleString();
}

interface AuthUser {
  id: string;
  full_name: string;
  email: string;
  created_at: string;
}

interface TranscriptionProps {
  currentUser: AuthUser | null;
  onLogout: () => void;
}

function Transcription({ currentUser, onLogout }: TranscriptionProps) {
  // --- Upload / transcription state (unchanged from Phase 4) ---
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transcription, setTranscription] = useState<string>("");
  const [segments, setSegments] = useState<WhisperSegment[]>([]);
  const [mergedTranscript, setMergedTranscript] = useState<MergedSegment[]>([]);
  const [speakerTranscript, setSpeakerTranscript] = useState<MergedSegment[]>([]);
  const [summary, setSummary] = useState<string>("");
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [decisions, setDecisions] = useState<string[]>([]);
  const [deadlines, setDeadlines] = useState<string[]>([]);
  const [keyTopics, setKeyTopics] = useState<string[]>([]);

  // --- Meeting History state (Phase 5) ---
  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [selectedMeeting, setSelectedMeeting] = useState<MeetingDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchMeetings = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await authFetch(`${API_BASE_URL}/meetings`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to load meeting history.");
      }
      setMeetings(data as MeetingListItem[]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load meeting history.";
      setHistoryError(message);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Load the meeting history once when the page first loads.
  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  const handleViewDetails = async (meetingId: string) => {
    setDetailLoading(true);
    setHistoryError(null);
    try {
      const response = await authFetch(`${API_BASE_URL}/meetings/${meetingId}`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to load meeting details.");
      }
      setSelectedMeeting(data as MeetingDetail);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load meeting details.";
      setHistoryError(message);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDeleteMeeting = async (meetingId: string) => {
    setDeletingId(meetingId);
    setHistoryError(null);
    try {
      const response = await authFetch(`${API_BASE_URL}/meetings/${meetingId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to delete meeting.");
      }
      // Remove it from the list, and clear the detail view if it was open.
      setMeetings((prev) => prev.filter((m) => m.id !== meetingId));
      setSelectedMeeting((prev) => (prev && prev.id === meetingId ? null : prev));
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to delete meeting.";
      setHistoryError(message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    // Clear stale results when a new file is picked.
    setErrorMessage(null);
    setTranscription("");
    setSegments([]);
    setMergedTranscript([]);
    setSpeakerTranscript([]);
    setSummary("");
    setActionItems([]);
    setDecisions([]);
    setDeadlines([]);
    setKeyTopics([]);
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
    setMergedTranscript([]);
    setSpeakerTranscript([]);
    setSummary("");
    setActionItems([]);
    setDecisions([]);
    setDeadlines([]);
    setKeyTopics([]);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await authFetch(`${API_BASE_URL}/transcribe`, {
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
        setMergedTranscript(result.merged);
        setSpeakerTranscript(result.transcript);
        setSummary(result.summary);
        setActionItems(result.action_items);
        setDecisions(result.decisions);
        setDeadlines(result.deadlines);
        setKeyTopics(result.key_topics);

      // Phase 5: the meeting was just persisted to PostgreSQL -
      // refresh the history list so it shows up immediately.
      fetchMeetings();
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Meeting Transcription (Whisper MVP)</h1>
        <div style={{ textAlign: "right" }}>
          {currentUser && (
            <p style={{ margin: "0 0 6px 0", fontSize: "0.85rem", color: "#666" }}>
              Logged in as {currentUser.full_name} ({currentUser.email})
            </p>
          )}
          <button type="button" onClick={onLogout}>
            Logout
          </button>
        </div>
      </div>

      {/* ============================================================
          Upload Meeting
          ============================================================ */}
      <h2 style={{ marginTop: "8px" }}>Upload Meeting</h2>
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

        {speakerTranscript.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h2>Speaker Transcript</h2>

          {speakerTranscript.map((entry, index) => (
            <div
              key={index}
              style={{
                border: "1px solid #ddd",
                padding: "12px 14px",
                marginBottom: "10px",
                borderRadius: "8px",
              }}
            >
              <strong>
                {entry.speaker} — {entry.start.toFixed(2)}s → {entry.end.toFixed(2)}s
              </strong>

            <p style={{ marginBottom: 0 }}>{entry.text}</p>
        </div>
    ))}
  </div>
)}

        {speakerTranscript.length > 0 && (
        <div style={{ marginTop: "32px" }}>
          <h2>Meeting Summary</h2>
          <p>{summary || "No summary available."}</p>

          <h2>Action Items</h2>
          {actionItems.length === 0 ? (
            <p className="status">No action items found.</p>
          ) : (
            actionItems.map((item, index) => (
              <div
                key={index}
                style={{
                  border: "1px solid #ddd",
                  padding: "12px 14px",
                  marginBottom: "10px",
                  borderRadius: "8px",
                }}
              >
                <p style={{ margin: "0 0 4px 0" }}>
                  <strong>Owner:</strong> {item.owner || "Not specified"}
                </p>
                <p style={{ margin: "0 0 4px 0" }}>
                  <strong>Task:</strong> {item.task}
                </p>
                <p style={{ margin: 0 }}>
                  <strong>Deadline:</strong> {item.deadline || "Not specified"}
                </p>
              </div>
            ))
          )}

          <h2>Decisions</h2>
          {decisions.length === 0 ? (
            <p className="status">No decisions found.</p>
          ) : (
            <ul>
              {decisions.map((decision, index) => (
                <li key={index}>{decision}</li>
              ))}
            </ul>
          )}

          <h2>Deadlines</h2>
          {deadlines.length === 0 ? (
            <p className="status">No deadlines found.</p>
          ) : (
            <ul>
              {deadlines.map((deadline, index) => (
                <li key={index}>{deadline}</li>
              ))}
            </ul>
          )}

          <h2>Key Topics</h2>
          {keyTopics.length === 0 ? (
            <p className="status">No key topics found.</p>
          ) : (
            <ul>
              {keyTopics.map((topic, index) => (
                <li key={index}>{topic}</li>
              ))}
            </ul>
          )}
        </div>
        )}

        {(mergedTranscript.length > 0 || segments.length > 0) && (
        <details style={{ marginTop: "24px" }}>
          <summary style={{ cursor: "pointer", color: "#555" }}>
            Debug: raw per-segment output
          </summary>

          {mergedTranscript.length > 0 && (
          <div style={{ marginTop: "16px" }}>
            <h3>Merged (per Whisper segment, ungrouped)</h3>

            {mergedTranscript.map((entry, index) => (
              <div
                key={index}
                style={{
                  border: "1px solid #eee",
                  padding: "8px 10px",
                  marginBottom: "6px",
                  borderRadius: "6px",
                  fontSize: "0.9rem",
                }}
              >
                <strong>
                  {entry.speaker} — {entry.start.toFixed(2)}s → {entry.end.toFixed(2)}s
                </strong>
                <p style={{ marginBottom: 0 }}>{entry.text}</p>
              </div>
            ))}
          </div>
          )}

          {segments.length > 0 && (
          <div style={{ marginTop: "16px" }}>
            <h3>Whisper Segments (no speaker labels)</h3>

            {segments.map((segment) => (
              <div
                key={segment.id}
                style={{
                  border: "1px solid #eee",
                  padding: "8px 10px",
                  marginBottom: "6px",
                  borderRadius: "6px",
                  fontSize: "0.9rem",
                }}
              >
                <strong>
                  {segment.start.toFixed(2)}s → {segment.end.toFixed(2)}s
                </strong>
                <p style={{ marginBottom: 0 }}>{segment.text}</p>
              </div>
            ))}
          </div>
          )}
        </details>
)}

      </div>

      {/* ============================================================
          Meeting History (Phase 5)
          ============================================================ */}
      <h2 style={{ marginTop: "40px" }}>Meeting History</h2>
      <div className="upload-card">
        {historyLoading && <p className="status">Loading meeting history...</p>}
        {historyError && <p className="status error">{historyError}</p>}

        {!historyLoading && meetings.length === 0 && (
          <p className="status">No meetings saved yet — upload one above.</p>
        )}

        {meetings.map((meeting) => (
          <div
            key={meeting.id}
            style={{
              border: "1px solid #ddd",
              padding: "12px 14px",
              marginBottom: "10px",
              borderRadius: "8px",
            }}
          >
            <p style={{ margin: "0 0 4px 0" }}>
              <strong>{meeting.filename}</strong>
            </p>
            <p style={{ margin: "0 0 8px 0", fontSize: "0.85rem", color: "#666" }}>
              Uploaded {formatDate(meeting.created_at)}
              {meeting.duration_seconds != null &&
                ` — ${meeting.duration_seconds.toFixed(0)}s`}
            </p>
            <p style={{ margin: "0 0 10px 0" }}>
              {meeting.summary_preview || "No summary available."}
            </p>
            <button
              type="button"
              onClick={() => handleViewDetails(meeting.id)}
              style={{ marginRight: "8px" }}
            >
              View Details
            </button>
            <button
              type="button"
              onClick={() => handleDeleteMeeting(meeting.id)}
              disabled={deletingId === meeting.id}
              style={{ background: "#c0392b" }}
            >
              {deletingId === meeting.id ? "Deleting..." : "Delete"}
            </button>
          </div>
        ))}

        {detailLoading && <p className="status">Loading meeting details...</p>}

        {selectedMeeting && (
          <div style={{ marginTop: "24px", borderTop: "1px solid #ddd", paddingTop: "20px" }}>
            <h3>{selectedMeeting.filename}</h3>
            <p style={{ fontSize: "0.85rem", color: "#666" }}>
              Uploaded {formatDate(selectedMeeting.created_at)}
            </p>

            <h4>Summary</h4>
            <p>{selectedMeeting.summary?.summary_text || "No summary available."}</p>

            <h4>Speaker Transcript</h4>
            {selectedMeeting.transcript && selectedMeeting.transcript.speaker_transcript.length > 0 ? (
              selectedMeeting.transcript.speaker_transcript.map((entry, index) => (
                <div
                  key={index}
                  style={{
                    border: "1px solid #eee",
                    padding: "8px 10px",
                    marginBottom: "6px",
                    borderRadius: "6px",
                    fontSize: "0.9rem",
                  }}
                >
                  <strong>
                    {entry.speaker} — {entry.start.toFixed(2)}s → {entry.end.toFixed(2)}s
                  </strong>
                  <p style={{ marginBottom: 0 }}>{entry.text}</p>
                </div>
              ))
            ) : (
              <p className="status">No transcript available.</p>
            )}

            <h4>Action Items</h4>
            {selectedMeeting.action_items.length === 0 ? (
              <p className="status">No action items found.</p>
            ) : (
              selectedMeeting.action_items.map((item, index) => (
                <div
                  key={index}
                  style={{
                    border: "1px solid #eee",
                    padding: "8px 10px",
                    marginBottom: "6px",
                    borderRadius: "6px",
                    fontSize: "0.9rem",
                  }}
                >
                  <p style={{ margin: "0 0 4px 0" }}>
                    <strong>Owner:</strong> {item.owner || "Not specified"}
                  </p>
                  <p style={{ margin: "0 0 4px 0" }}>
                    <strong>Task:</strong> {item.task}
                  </p>
                  <p style={{ margin: 0 }}>
                    <strong>Deadline:</strong> {item.deadline || "Not specified"}
                  </p>
                </div>
              ))
            )}

            <h4>Decisions</h4>
            {selectedMeeting.decisions.length === 0 ? (
              <p className="status">No decisions found.</p>
            ) : (
              <ul>
                {selectedMeeting.decisions.map((decision, index) => (
                  <li key={index}>{decision}</li>
                ))}
              </ul>
            )}

            <h4>Deadlines</h4>
            {selectedMeeting.deadlines.length === 0 ? (
              <p className="status">No deadlines found.</p>
            ) : (
              <ul>
                {selectedMeeting.deadlines.map((deadline, index) => (
                  <li key={index}>{deadline}</li>
                ))}
              </ul>
            )}

            <h4>Key Topics</h4>
            {selectedMeeting.key_topics.length === 0 ? (
              <p className="status">No key topics found.</p>
            ) : (
              <ul>
                {selectedMeeting.key_topics.map((topic, index) => (
                  <li key={index}>{topic}</li>
                ))}
              </ul>
            )}

            <button type="button" onClick={() => setSelectedMeeting(null)}>
              Close Details
            </button>
          </div>
        )}
      </div>

      {/* ============================================================
          AI Meeting Assistant (Phase 7 — RAG chatbot)
          ============================================================ */}
      <h2 style={{ marginTop: "40px" }}>AI Meeting Assistant</h2>
      <ChatAssistant meetings={meetings.map((m) => ({ id: m.id, filename: m.filename }))} />
    </div>
  );
}

export default Transcription;
