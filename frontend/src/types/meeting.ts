// Shared types for the meeting domain. Mirrors the shapes already
// consumed by Transcription.tsx (which matches
// backend/app/schemas/meeting_schemas.py) — kept in one place so the
// dashboard, meetings list, and meeting details page can't drift from
// what the backend actually returns.

export interface WhisperSegment {
  id: number;
  start: number;
  end: number;
  text: string;
}

export interface MergedSegment {
  speaker: string;
  start: number;
  end: number;
  text: string;
}

export interface ActionItem {
  owner: string;
  task: string;
  deadline: string;
}

export interface TranscribeResponse {
  status: string;
  meeting_id: string;
  text: string;
  segments: WhisperSegment[];
  merged: MergedSegment[];
  transcript: MergedSegment[];
  summary: string;
  action_items: ActionItem[];
  decisions: string[];
  deadlines: string[];
  key_topics: string[];
}

export interface MeetingListItem {
  id: string;
  filename: string;
  created_at: string;
  duration_seconds: number | null;
  summary_preview: string;
}

export interface MeetingDetail {
  id: string;
  filename: string;
  created_at: string;
  duration_seconds: number | null;
  transcript: { full_text: string; speaker_transcript: MergedSegment[] } | null;
  summary: { summary_text: string } | null;
  action_items: ActionItem[];
  decisions: string[];
  deadlines: string[];
  key_topics: string[];
}

export interface AuthUser {
  id: string;
  full_name: string;
  email: string;
  created_at: string;
}
