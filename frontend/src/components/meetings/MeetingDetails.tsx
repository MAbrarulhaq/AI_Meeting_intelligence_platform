import { useEffect, useState } from "react";
import { getMeeting, deleteMeeting } from "../../services/meetings";
import { toErrorMessage } from "../../services/api";
import { MeetingDetail } from "../../types/meeting";
import { formatDateTime, formatDuration } from "../../utils/format";
import { Card, Badge } from "../ui/Card";
import Button from "../ui/Button";
import { ErrorState } from "../ui/EmptyState";
import { Skeleton } from "../ui/Skeleton";
import { Tabs, TabPanel, TabItem } from "../ui/Tabs";
import ChatAssistant from "../ChatAssistant";

interface MeetingDetailsProps {
  meetingId: string;
  onBack: () => void;
  onDeleted: () => void;
}

type TabId = "summary" | "transcript" | "action-items" | "decisions" | "deadlines" | "topics" | "assistant";

function MeetingDetails({ meetingId, onBack, onDeleted }: MeetingDetailsProps) {
  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("summary");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    setMeeting(null);
    setActiveTab("summary");

    getMeeting(meetingId)
      .then((detail) => {
        if (!cancelled) setMeeting(detail);
      })
      .catch((err) => {
        if (!cancelled) setError(toErrorMessage(err, "Failed to load this meeting."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [meetingId]);

  const handleDelete = async () => {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteMeeting(meetingId);
      onDeleted();
    } catch (err) {
      setDeleteError(toErrorMessage(err, "Failed to delete this meeting."));
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="page-shell">
        <Skeleton width="240px" height="28px" />
        <div style={{ height: 24 }} />
        <Card className="meeting-details-panel">
          <Skeleton width="100%" height="16px" />
          <div style={{ height: 10 }} />
          <Skeleton width="90%" height="16px" />
          <div style={{ height: 10 }} />
          <Skeleton width="70%" height="16px" />
        </Card>
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="page-shell">
        <button type="button" className="link-btn" onClick={onBack}>
          ← Back to meetings
        </button>
        <ErrorState body={error || "This meeting could not be found."} />
      </div>
    );
  }

  const tabs: TabItem[] = [
    { id: "summary", label: "Summary" },
    { id: "transcript", label: "Transcript" },
    { id: "action-items", label: "Action Items", badge: meeting.action_items.length },
    { id: "decisions", label: "Decisions", badge: meeting.decisions.length },
    { id: "deadlines", label: "Deadlines", badge: meeting.deadlines.length },
    { id: "topics", label: "Key Topics", badge: meeting.key_topics.length },
    { id: "assistant", label: "AI Assistant" },
  ];

  return (
    <div className="page-shell">
      <button type="button" className="link-btn" onClick={onBack}>
        ← Back to meetings
      </button>

      <div className="page-head meeting-details-head">
        <div>
          <h1>{meeting.filename}</h1>
          <p className="page-sub mono">
            {formatDateTime(meeting.created_at)} · {formatDuration(meeting.duration_seconds)}
          </p>
        </div>
        <div className="meeting-details-actions">
          {!confirmingDelete ? (
            <Button variant="secondary" onClick={() => setConfirmingDelete(true)}>
              Delete
            </Button>
          ) : (
            <div className="delete-confirm">
              <span>Delete this meeting?</span>
              <Button variant="secondary" size="sm" onClick={() => setConfirmingDelete(false)}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleDelete} disabled={isDeleting}>
                {isDeleting ? "Deleting…" : "Confirm"}
              </Button>
            </div>
          )}
        </div>
      </div>

      {deleteError && (
        <div className="callout-error" role="alert">
          {deleteError}
        </div>
      )}

      <Tabs tabs={tabs} activeId={activeTab} onChange={(id) => setActiveTab(id as TabId)} />

      <TabPanel active={activeTab === "summary"}>
        <Card className="meeting-details-panel">
          <p>{meeting.summary?.summary_text || "No summary available."}</p>
        </Card>
      </TabPanel>

      <TabPanel active={activeTab === "transcript"}>
        <Card className="meeting-details-panel">
          {meeting.transcript && meeting.transcript.speaker_transcript.length > 0 ? (
            <div className="transcript-list">
              {meeting.transcript.speaker_transcript.map((entry, index) => (
                <div className="transcript-entry" key={index}>
                  <span className="transcript-entry-speaker mono">
                    {entry.speaker} · {entry.start.toFixed(0)}s–{entry.end.toFixed(0)}s
                  </span>
                  <p>{entry.text}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="status">No transcript available.</p>
          )}
        </Card>
      </TabPanel>

      <TabPanel active={activeTab === "action-items"}>
        <Card className="meeting-details-panel">
          {meeting.action_items.length === 0 ? (
            <p className="status">No action items were identified in this meeting.</p>
          ) : (
            <div className="action-item-list">
              {meeting.action_items.map((item, index) => (
                <div className="action-item-row" key={index}>
                  <p className="action-item-task">{item.task}</p>
                  <div className="action-item-meta">
                    <Badge>{item.owner || "Unassigned"}</Badge>
                    {item.deadline && <Badge tone="signal">{item.deadline}</Badge>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </TabPanel>

      <TabPanel active={activeTab === "decisions"}>
        <Card className="meeting-details-panel">
          {meeting.decisions.length === 0 ? (
            <p className="status">No decisions were identified in this meeting.</p>
          ) : (
            <ul className="plain-list">
              {meeting.decisions.map((decision, index) => (
                <li key={index}>{decision}</li>
              ))}
            </ul>
          )}
        </Card>
      </TabPanel>

      <TabPanel active={activeTab === "deadlines"}>
        <Card className="meeting-details-panel">
          {meeting.deadlines.length === 0 ? (
            <p className="status">No deadlines were identified.</p>
          ) : (
            <ul className="plain-list">
              {meeting.deadlines.map((deadline, index) => (
                <li key={index}>{deadline}</li>
              ))}
            </ul>
          )}
        </Card>
      </TabPanel>

      <TabPanel active={activeTab === "topics"}>
        <Card className="meeting-details-panel">
          {meeting.key_topics.length === 0 ? (
            <p className="status">No key topics found.</p>
          ) : (
            <div className="insights-topic-cloud">
              {meeting.key_topics.map((topic, index) => (
                <Badge key={index} tone="accent">
                  {topic}
                </Badge>
              ))}
            </div>
          )}
        </Card>
      </TabPanel>

      <TabPanel active={activeTab === "assistant"}>
        <ChatAssistant
          meetings={[{ id: meeting.id, filename: meeting.filename }]}
          initialScopeMeetingId={meeting.id}
          lockScope
        />
      </TabPanel>
    </div>
  );
}

export default MeetingDetails;
