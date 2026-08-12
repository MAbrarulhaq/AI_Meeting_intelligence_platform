import { useMemo, useState } from "react";
import { useMeetingsAggregate } from "../../hooks/useMeetingsAggregate";
import { EmptyState, ErrorState } from "../ui/EmptyState";
import { MeetingRowSkeleton } from "../ui/Skeleton";
import Button from "../ui/Button";
import { Badge } from "../ui/Card";
import { formatDate, formatDuration } from "../../utils/format";

interface MeetingsProps {
  onOpenMeeting: (meetingId: string) => void;
  onUploadMeeting: () => void;
}

type SortKey = "newest" | "oldest" | "longest" | "name";

function Meetings({ onOpenMeeting, onUploadMeeting }: MeetingsProps) {
  const { data, isLoading, error, refresh } = useMeetingsAggregate();
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("newest");

  const filteredSorted = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    const filtered = q
      ? data.meetings.filter(
          (m) =>
            m.filename.toLowerCase().includes(q) ||
            m.summary_preview?.toLowerCase().includes(q)
        )
      : data.meetings;

    const sorted = [...filtered];
    switch (sortKey) {
      case "newest":
        sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
      case "oldest":
        sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        break;
      case "longest":
        sorted.sort((a, b) => (b.duration_seconds ?? 0) - (a.duration_seconds ?? 0));
        break;
      case "name":
        sorted.sort((a, b) => a.filename.localeCompare(b.filename));
        break;
    }
    return sorted;
  }, [data, query, sortKey]);

  return (
    <div className="page-shell">
      <div className="page-head">
        <div>
          <h1>Meetings</h1>
          <p className="page-sub">Every meeting you've uploaded, transcribed, and analyzed.</p>
        </div>
        <Button onClick={onUploadMeeting}>+ New Meeting</Button>
      </div>

      {error && !isLoading && <ErrorState body={error} onRetry={refresh} />}

      {!error && isLoading && (
        <div className="meeting-row-list">
          <MeetingRowSkeleton />
          <MeetingRowSkeleton />
          <MeetingRowSkeleton />
          <MeetingRowSkeleton />
        </div>
      )}

      {!error && !isLoading && data && data.totalMeetings === 0 && (
        <EmptyState
          title="No meetings yet"
          body="Upload your first meeting and let the assistant turn it into structured intelligence."
          actionLabel="Upload meeting"
          onAction={onUploadMeeting}
        />
      )}

      {!error && !isLoading && data && data.totalMeetings > 0 && (
        <>
          <div className="meetings-toolbar">
            <input
              className="input meetings-search"
              type="search"
              placeholder="Search meetings…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search meetings"
            />
            <select
              className="input meetings-sort"
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as SortKey)}
              aria-label="Sort meetings"
            >
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
              <option value="longest">Longest first</option>
              <option value="name">Name (A–Z)</option>
            </select>
          </div>

          {filteredSorted.length === 0 ? (
            <EmptyState title="No matching meetings" body="Try a different search term." />
          ) : (
            <div className="meeting-row-list">
              {filteredSorted.map((meeting) => (
                <button
                  type="button"
                  key={meeting.id}
                  className="meeting-row"
                  onClick={() => onOpenMeeting(meeting.id)}
                >
                  <div className="meeting-row-main">
                    <p className="meeting-row-name">{meeting.filename}</p>
                    <span className="meeting-row-meta mono">
                      {formatDate(meeting.created_at)} · {formatDuration(meeting.duration_seconds)}
                    </span>
                    {meeting.summary_preview && (
                      <p className="meeting-row-summary">{meeting.summary_preview}</p>
                    )}
                  </div>
                  <div className="meeting-row-counts">
                    <Badge tone="neutral">Processed</Badge>
                    {meeting.actionItemCount != null && (
                      <Badge>{meeting.actionItemCount} action items</Badge>
                    )}
                    {meeting.decisionCount != null && (
                      <Badge>{meeting.decisionCount} decisions</Badge>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Meetings;
