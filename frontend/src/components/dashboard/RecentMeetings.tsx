import { Badge } from "../ui/Card";
import { MeetingWithCounts } from "../../services/meetings";
import { formatDate, formatDuration } from "../../utils/format";

interface RecentMeetingsProps {
  meetings: MeetingWithCounts[];
  onOpen: (meetingId: string) => void;
}

function RecentMeetings({ meetings, onOpen }: RecentMeetingsProps) {
  return (
    <div className="meeting-row-list">
      {meetings.map((meeting) => (
        <button
          type="button"
          key={meeting.id}
          className="meeting-row"
          onClick={() => onOpen(meeting.id)}
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
            {meeting.actionItemCount != null && meeting.actionItemCount > 0 && (
              <Badge>{meeting.actionItemCount} action items</Badge>
            )}
            {meeting.decisionCount != null && meeting.decisionCount > 0 && (
              <Badge>{meeting.decisionCount} decisions</Badge>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}

export default RecentMeetings;
