import { Badge, Card } from "../ui/Card";
import { AttributedActionItem, AttributedText } from "../../services/meetings";

interface DashboardInsightsProps {
  recentActionItems: AttributedActionItem[];
  recentDecisions: AttributedText[];
  keyTopicFrequency: { topic: string; count: number }[];
}

function DashboardInsights({
  recentActionItems,
  recentDecisions,
  keyTopicFrequency,
}: DashboardInsightsProps) {
  const hasAnything =
    recentActionItems.length > 0 || recentDecisions.length > 0 || keyTopicFrequency.length > 0;

  if (!hasAnything) {
    return (
      <Card className="insights-panel">
        <h3>Meeting intelligence</h3>
        <p className="status">
          Action items, decisions, and topics will appear here once a meeting has been processed.
        </p>
      </Card>
    );
  }

  return (
    <div className="insights-grid">
      <Card className="insights-panel">
        <h3>Latest action items</h3>
        {recentActionItems.length === 0 ? (
          <p className="status">No action items found yet.</p>
        ) : (
          <ul className="insights-list">
            {recentActionItems.map((item, index) => (
              <li key={index}>
                <p className="insights-item-primary">{item.task}</p>
                <span className="insights-item-meta mono">
                  {item.owner || "Unassigned"} · {item.meetingFilename}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card className="insights-panel">
        <h3>Latest decisions</h3>
        {recentDecisions.length === 0 ? (
          <p className="status">No decisions found yet.</p>
        ) : (
          <ul className="insights-list">
            {recentDecisions.map((item, index) => (
              <li key={index}>
                <p className="insights-item-primary">{item.text}</p>
                <span className="insights-item-meta mono">{item.meetingFilename}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card className="insights-panel">
        <h3>Frequent topics</h3>
        {keyTopicFrequency.length === 0 ? (
          <p className="status">No key topics found yet.</p>
        ) : (
          <div className="insights-topic-cloud">
            {keyTopicFrequency.slice(0, 10).map((t) => (
              <Badge key={t.topic} tone="accent">
                {t.topic} · {t.count}
              </Badge>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export default DashboardInsights;
