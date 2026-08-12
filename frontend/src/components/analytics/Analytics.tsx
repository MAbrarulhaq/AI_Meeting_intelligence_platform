import { useMemo } from "react";
import { useMeetingsAggregate } from "../../hooks/useMeetingsAggregate";
import { EmptyState, ErrorState } from "../ui/EmptyState";
import { Skeleton } from "../ui/Skeleton";
import { Card } from "../ui/Card";
import StatCard from "../dashboard/StatCard";
import { BarChart } from "../ui/BarChart";
import { formatHours } from "../../utils/format";

function Analytics() {
  const { data, isLoading, error, refresh } = useMeetingsAggregate();

  const meetingsByMonth = useMemo(() => {
    if (!data) return [];
    const counts = new Map<string, number>();
    data.meetings.forEach((m) => {
      const date = new Date(m.created_at);
      const label = date.toLocaleDateString(undefined, { month: "short" });
      counts.set(label, (counts.get(label) ?? 0) + 1);
    });
    return Array.from(counts.entries()).map(([label, value]) => ({ label, value }));
  }, [data]);

  return (
    <div className="page-shell">
      <div className="page-head">
        <div>
          <h1>Analytics</h1>
          <p className="page-sub">Patterns across the meetings you've processed.</p>
        </div>
      </div>

      {error && !isLoading && <ErrorState body={error} onRetry={refresh} />}

      {!error && isLoading && (
        <div className="stat-grid">
          <Skeleton height="80px" />
          <Skeleton height="80px" />
          <Skeleton height="80px" />
          <Skeleton height="80px" />
        </div>
      )}

      {!error && !isLoading && data && data.totalMeetings === 0 && (
        <EmptyState
          title="Not enough meeting data yet"
          body="Upload a few meetings and analytics will appear here automatically."
        />
      )}

      {!error && !isLoading && data && data.totalMeetings > 0 && (
        <>
          <div className="stat-grid">
            <StatCard label="Total meetings" value={String(data.totalMeetings)} />
            <StatCard label="Total duration" value={formatHours(data.totalDurationSeconds)} />
            <StatCard
              label="Average duration"
              value={formatHours(data.totalDurationSeconds / data.totalMeetings)}
            />
            <StatCard
              label="Action items"
              value={data.partial ? `${data.totalActionItems}+` : String(data.totalActionItems)}
            />
          </div>

          <section className="section-block">
            <h2>Meetings uploaded</h2>
            <Card className="chart-panel">
              {meetingsByMonth.length > 1 ? (
                <BarChart data={meetingsByMonth} />
              ) : (
                <p className="status">
                  Upload meetings across more than one month to see this trend.
                </p>
              )}
            </Card>
          </section>

          <section className="section-block">
            <h2>Meeting intelligence totals</h2>
            <Card className="chart-panel">
              <BarChart
                data={[
                  { label: "Action items", value: data.totalActionItems },
                  { label: "Decisions", value: data.totalDecisions },
                  { label: "Deadlines", value: data.totalDeadlines },
                ]}
              />
            </Card>
          </section>

          <section className="section-block">
            <h2>Most frequent topics</h2>
            {data.keyTopicFrequency.length === 0 ? (
              <p className="status">No key topics found yet.</p>
            ) : (
              <Card className="chart-panel">
                <BarChart data={data.keyTopicFrequency.slice(0, 8).map((t) => ({ label: t.topic, value: t.count }))} />
              </Card>
            )}
          </section>

          {data.partial && (
            <p className="field-hint">
              Some meeting details couldn't be loaded, so totals above may be a lower bound.
            </p>
          )}
        </>
      )}
    </div>
  );
}

export default Analytics;
