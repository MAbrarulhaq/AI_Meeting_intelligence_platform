interface SkeletonProps {
  width?: string;
  height?: string;
  className?: string;
}

export function Skeleton({ width = "100%", height = "16px", className = "" }: SkeletonProps) {
  return (
    <span
      className={`skeleton ${className}`.trim()}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}

/** A skeleton shaped like a meeting row, for list loading states. */
export function MeetingRowSkeleton() {
  return (
    <div className="meeting-row meeting-row-skeleton">
      <div style={{ flex: 1 }}>
        <Skeleton width="60%" height="14px" />
        <div style={{ height: 8 }} />
        <Skeleton width="40%" height="12px" />
      </div>
      <Skeleton width="70px" height="24px" />
    </div>
  );
}

/** A skeleton shaped like a stat card, for dashboard loading states. */
export function StatCardSkeleton() {
  return (
    <div className="stat-card">
      <Skeleton width="50%" height="12px" />
      <div style={{ height: 12 }} />
      <Skeleton width="70%" height="28px" />
    </div>
  );
}
