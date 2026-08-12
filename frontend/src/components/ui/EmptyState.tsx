import { ReactNode } from "react";
import Button from "./Button";

interface EmptyStateProps {
  title: string;
  body: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: ReactNode;
}

export function EmptyState({ title, body, actionLabel, onAction, icon }: EmptyStateProps) {
  return (
    <div className="empty-state">
      {icon}
      <h3>{title}</h3>
      <p>{body}</p>
      {actionLabel && onAction && <Button onClick={onAction}>{actionLabel}</Button>}
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  body: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Something went wrong", body, onRetry }: ErrorStateProps) {
  return (
    <div className="empty-state empty-state-error" role="alert">
      <h3>{title}</h3>
      <p>{body}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
