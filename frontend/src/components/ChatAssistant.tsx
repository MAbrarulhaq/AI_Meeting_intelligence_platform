import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { authFetch } from "../auth";

const API_BASE_URL = "http://localhost:8000";

interface MeetingOption {
  id: string;
  filename: string;
}

interface ChatSource {
  meeting_id: string;
  filename: string;
  chunk_number: number;
  reference_text: string;
  confidence: number | null;
}

interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  sources?: ChatSource[];
  isError?: boolean;
}

interface ChatAssistantProps {
  // Reuses the meeting list already loaded by Transcription.tsx for
  // the "Selected Meeting" scope dropdown — no separate fetch needed.
  meetings: MeetingOption[];
}

function ChatAssistant({ meetings }: ChatAssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [scopeMeetingId, setScopeMeetingId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to the latest message whenever the conversation changes.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const sendMessage = async () => {
    const question = input.trim();
    if (!question || isSending) {
      return;
    }

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setIsSending(true);

    try {
      const response = await authFetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          meeting_id: scopeMeetingId || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "The assistant couldn't answer that.");
      }

      const result = data as ChatResponse;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "The assistant couldn't answer that.";
      setMessages((prev) => [...prev, { role: "assistant", text: message, isError: true }]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter sends; Shift+Enter inserts a newline.
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="upload-card" style={{ display: "flex", flexDirection: "column" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "12px",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <span style={{ fontSize: "0.85rem", color: "#666" }}>Search scope</span>
        <select
          value={scopeMeetingId}
          onChange={(e) => setScopeMeetingId(e.target.value)}
          style={{ padding: "6px", borderRadius: "6px" }}
        >
          <option value="">All Meetings</option>
          {meetings.map((meeting) => (
            <option key={meeting.id} value={meeting.id}>
              {meeting.filename}
            </option>
          ))}
        </select>
      </div>

      {/* Scrollable message list */}
      <div
        style={{
          height: "420px",
          overflowY: "auto",
          border: "1px solid #eee",
          borderRadius: "8px",
          padding: "12px",
          background: "#fafafa",
        }}
      >
        {messages.length === 0 && (
          <p className="status">
            Ask about any of your meetings — e.g. "What did we decide about the launch date?"
          </p>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              display: "flex",
              justifyContent: message.role === "user" ? "flex-end" : "flex-start",
              marginBottom: "12px",
            }}
          >
            <div
              style={{
                maxWidth: "80%",
                padding: "10px 14px",
                borderRadius: "12px",
                background: message.role === "user" ? "#1a1a1a" : "white",
                color: message.role === "user" ? "white" : message.isError ? "#c0392b" : "#1a1a1a",
                border: message.role === "assistant" ? "1px solid #ddd" : "none",
                whiteSpace: "pre-wrap",
              }}
            >
              <p style={{ margin: 0 }}>{message.text}</p>

              {message.sources && message.sources.length > 0 && (
                <div style={{ marginTop: "10px", borderTop: "1px solid #eee", paddingTop: "8px" }}>
                  {message.sources.map((source, sourceIndex) => (
                    <div
                      key={sourceIndex}
                      style={{ fontSize: "0.8rem", color: "#666", marginBottom: "4px" }}
                    >
                      <strong>Source:</strong> {source.filename} — Chunk {source.chunk_number}
                      {source.confidence != null && ` (relevance: ${source.confidence})`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isSending && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "12px" }}>
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "12px",
                background: "white",
                border: "1px solid #ddd",
                color: "#666",
              }}
            >
              Thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input row */}
      <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your meetings... (Enter to send, Shift+Enter for a new line)"
          rows={2}
          style={{
            flex: 1,
            padding: "10px",
            borderRadius: "8px",
            border: "1px solid #ddd",
            resize: "vertical",
            fontFamily: "inherit",
            fontSize: "0.95rem",
          }}
        />
        <button type="button" onClick={sendMessage} disabled={isSending || !input.trim()}>
          {isSending ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

export default ChatAssistant;
