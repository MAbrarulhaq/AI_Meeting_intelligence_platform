import { ReactNode } from "react";

export interface TabItem {
  id: string;
  label: string;
  badge?: number;
}

interface TabsProps {
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
}

export function Tabs({ tabs, activeId, onChange }: TabsProps) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          type="button"
          aria-selected={tab.id === activeId}
          className={`tab ${tab.id === activeId ? "tab-active" : ""}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
          {typeof tab.badge === "number" && tab.badge > 0 && (
            <span className="tab-badge">{tab.badge}</span>
          )}
        </button>
      ))}
    </div>
  );
}

interface TabPanelProps {
  active: boolean;
  children: ReactNode;
}

export function TabPanel({ active, children }: TabPanelProps) {
  if (!active) return null;
  return <div className="tab-panel">{children}</div>;
}
