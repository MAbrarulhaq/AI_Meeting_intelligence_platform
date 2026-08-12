export type AuthenticatedPage =
  | "dashboard"
  | "meetings"
  | "meeting-details"
  | "upload"
  | "analytics"
  | "profile"
  | "settings";

export interface NavTarget {
  page: AuthenticatedPage;
  meetingId?: string;
}
