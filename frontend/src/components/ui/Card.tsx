import { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ className = "", children, ...rest }: CardProps) {
  return (
    <div className={`card ${className}`.trim()} {...rest}>
      {children}
    </div>
  );
}

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: "neutral" | "accent" | "signal" | "danger";
  children: ReactNode;
}

export function Badge({ tone = "neutral", className = "", children, ...rest }: BadgeProps) {
  const toneClass = tone === "neutral" ? "" : `badge-${tone}`;
  return (
    <span className={`badge ${toneClass} ${className}`.trim()} {...rest}>
      {children}
    </span>
  );
}
