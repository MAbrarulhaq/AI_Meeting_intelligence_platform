import { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
  icon?: ReactNode;
}

function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className="stat-card">
      <span className="stat-card-label">{label}</span>
      <span className="stat-card-value mono">{value}</span>
      {hint && <span className="stat-card-hint">{hint}</span>}
    </div>
  );
}

export default StatCard;
