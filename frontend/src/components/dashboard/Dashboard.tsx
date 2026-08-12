import { useMeetingsAggregate } from "../../hooks/useMeetingsAggregate";
import { AuthUser } from "../../types/meeting";
import StatCard from "./StatCard";
import { StatCardSkeleton, MeetingRowSkeleton } from "../ui/Skeleton";
import { EmptyState, ErrorState } from "../ui/EmptyState";
import RecentMeetings from "./RecentMeetings";
import DashboardInsights from "./DashboardInsights";
import Button from "../ui/Button";
import { formatHours } from "../../utils/format";

interface DashboardProps {
  user: AuthUser | null;
  onOpenMeeting: (meetingId: string) => void;
  onUploadMeeting: () => void;
  onViewAllMeetings: () => void;
}

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function Dashboard({ user, onOpenMeeting, onUploadMeeting, onViewAllMeetings }: DashboardProps) {
  const { data, isLoading, error, refresh } = useMeetingsAggregate();

  const firstName = user?.full_name?.trim().split(/\s+/)[0];

  return (
    <div className="page-shell">
      <div className="page-head">
        <div>
          <h1>
            {greeting()}
            {firstName ? `, ${firstName}` : ""}
          </h1>
          <p className="page-sub">Turn your conversations into structured, searchable knowledge.</p>
        </div>
        <Button onClick={onUploadMeeting}>+ New Meeting</Button>
      </div>

      {error && !isLoading && (
        <ErrorState body={error} onRetry={refresh} />
      )}

      {!error && isLoading && (
        <>
          <div className="stat-grid">
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </div>
          <section className="section-block">
            <h2>Recent meetings</h2>
            <div className="meeting-row-list">
              <MeetingRowSkeleton />
              <MeetingRowSkeleton />
              <MeetingRowSkeleton />
            </div>
          </section>
        </>
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
          <div className="stat-grid">
            <StatCard label="Total meetings" value={String(data.totalMeetings)} />
            <StatCard
              label="Total duration"
              value={formatHours(data.totalDurationSeconds)}
            />
            <StatCard
              label="Action items"
              value={data.partial ? `${data.totalActionItems}+` : String(data.totalActionItems)}
            />
            <StatCard
              label="Decisions"
              value={data.partial ? `${data.totalDecisions}+` : String(data.totalDecisions)}
            />
          </div>

          <section className="section-block">
            <div className="section-block-head">
              <h2>Recent meetings</h2>
              <button type="button" className="link-btn" onClick={onViewAllMeetings}>
                View all →
              </button>
            </div>
            <RecentMeetings meetings={data.meetings.slice(0, 5)} onOpen={onOpenMeeting} />
          </section>

          <section className="section-block">
            <h2>Meeting intelligence</h2>
            <DashboardInsights
              recentActionItems={data.recentActionItems}
              recentDecisions={data.recentDecisions}
              keyTopicFrequency={data.keyTopicFrequency}
            />
          </section>
        </>
      )}
    </div>
  );
}

export default Dashboard;
