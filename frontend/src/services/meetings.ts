import { apiRequest } from "./api";
import { MeetingDetail, MeetingListItem } from "../types/meeting";

export function listMeetings(): Promise<MeetingListItem[]> {
  return apiRequest<MeetingListItem[]>("/meetings");
}

export function getMeeting(meetingId: string): Promise<MeetingDetail> {
  return apiRequest<MeetingDetail>(`/meetings/${meetingId}`);
}

export function deleteMeeting(meetingId: string): Promise<void> {
  return apiRequest<void>(`/meetings/${meetingId}`, { method: "DELETE" });
}

export interface MeetingWithCounts extends MeetingListItem {
  actionItemCount: number | null;
  decisionCount: number | null;
  deadlineCount: number | null;
}

export interface AttributedActionItem extends ActionItemRef {
  meetingId: string;
  meetingFilename: string;
}

interface ActionItemRef {
  owner: string;
  task: string;
  deadline: string;
}

export interface AttributedText {
  text: string;
  meetingId: string;
  meetingFilename: string;
}

export interface MeetingsAggregate {
  meetings: MeetingWithCounts[];
  totalMeetings: number;
  totalDurationSeconds: number;
  totalActionItems: number;
  totalDecisions: number;
  totalDeadlines: number;
  keyTopicFrequency: { topic: string; count: number }[];
  /** Most recent meetings' action items / decisions, newest meeting first — real data, not aggregated stats. */
  recentActionItems: AttributedActionItem[];
  recentDecisions: AttributedText[];
  /** True if any per-meeting detail fetch failed — counts below may be partial. */
  partial: boolean;
}

/**
 * /meetings does not return action item / decision / deadline / topic
 * counts — those only exist on the per-meeting detail endpoint. To
 * show real (not invented) aggregate numbers on the Dashboard and
 * Analytics page, we fetch each meeting's detail once and derive the
 * counts client-side. This is a straightforward N+1 given the app's
 * expected scale (a single user's own meetings); if that stops being
 * true, this is the function to change to a real backend aggregate
 * endpoint instead.
 */
export async function fetchMeetingsAggregate(): Promise<MeetingsAggregate> {
  const list = await listMeetings();

  const details = await Promise.all(
    list.map(async (item) => {
      try {
        return await getMeeting(item.id);
      } catch {
        return null;
      }
    })
  );

  let partial = false;
  let totalDurationSeconds = 0;
  let totalActionItems = 0;
  let totalDecisions = 0;
  let totalDeadlines = 0;
  const topicCounts = new Map<string, number>();

  const meetings: MeetingWithCounts[] = list.map((item, index) => {
    const detail = details[index];
    totalDurationSeconds += item.duration_seconds ?? 0;

    if (!detail) {
      partial = true;
      return { ...item, actionItemCount: null, decisionCount: null, deadlineCount: null };
    }

    totalActionItems += detail.action_items.length;
    totalDecisions += detail.decisions.length;
    totalDeadlines += detail.deadlines.length;
    detail.key_topics.forEach((topic) => {
      topicCounts.set(topic, (topicCounts.get(topic) ?? 0) + 1);
    });

    return {
      ...item,
      actionItemCount: detail.action_items.length,
      decisionCount: detail.decisions.length,
      deadlineCount: detail.deadlines.length,
    };
  });

  const keyTopicFrequency = Array.from(topicCounts.entries())
    .map(([topic, count]) => ({ topic, count }))
    .sort((a, b) => b.count - a.count);

  // Newest-first, for the "recent intelligence" panel — real data pulled
  // directly from the most recently uploaded meetings' detail responses.
  const byRecency = list
    .map((item, index) => ({ item, detail: details[index] }))
    .filter((entry) => entry.detail !== null)
    .sort((a, b) => new Date(b.item.created_at).getTime() - new Date(a.item.created_at).getTime());

  const recentActionItems: AttributedActionItem[] = [];
  const recentDecisions: AttributedText[] = [];

  for (const { item, detail } of byRecency) {
    if (!detail) continue;
    for (const actionItem of detail.action_items) {
      if (recentActionItems.length >= 6) break;
      recentActionItems.push({ ...actionItem, meetingId: item.id, meetingFilename: item.filename });
    }
    for (const decision of detail.decisions) {
      if (recentDecisions.length >= 6) break;
      recentDecisions.push({ text: decision, meetingId: item.id, meetingFilename: item.filename });
    }
    if (recentActionItems.length >= 6 && recentDecisions.length >= 6) break;
  }

  return {
    meetings,
    totalMeetings: list.length,
    totalDurationSeconds,
    totalActionItems,
    totalDecisions,
    totalDeadlines,
    keyTopicFrequency,
    recentActionItems,
    recentDecisions,
    partial,
  };
}
