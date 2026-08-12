import { useState } from "react";
import Navbar from "./layout/Navbar";
import Dashboard from "./dashboard/Dashboard";
import Meetings from "./meetings/Meetings";
import MeetingDetails from "./meetings/MeetingDetails";
import MeetingUpload from "./meetings/MeetingUpload";
import Analytics from "./analytics/Analytics";
import Profile from "./account/Profile";
import Settings from "./account/Settings";
import { AuthUser } from "../types/meeting";
import { AuthenticatedPage, NavTarget } from "../types/navigation";

interface AuthenticatedAppProps {
  currentUser: AuthUser | null;
  onLogout: () => void;
}

function AuthenticatedApp({ currentUser, onLogout }: AuthenticatedAppProps) {
  const [page, setPage] = useState<AuthenticatedPage>("dashboard");
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null);

  const navigate = (target: NavTarget) => {
    setPage(target.page);
    if (target.meetingId) setSelectedMeetingId(target.meetingId);
  };

  const openMeeting = (meetingId: string) => {
    setSelectedMeetingId(meetingId);
    setPage("meeting-details");
  };

  return (
    <div className="authenticated-app">
      <Navbar user={currentUser} activePage={page} onNavigate={navigate} onLogout={onLogout} />

      <main className="authenticated-main">
        {page === "dashboard" && (
          <Dashboard
            user={currentUser}
            onOpenMeeting={openMeeting}
            onUploadMeeting={() => setPage("upload")}
            onViewAllMeetings={() => setPage("meetings")}
          />
        )}

        {page === "meetings" && (
          <Meetings onOpenMeeting={openMeeting} onUploadMeeting={() => setPage("upload")} />
        )}

        {page === "meeting-details" && selectedMeetingId && (
          <MeetingDetails
            meetingId={selectedMeetingId}
            onBack={() => setPage("meetings")}
            onDeleted={() => {
              setSelectedMeetingId(null);
              setPage("meetings");
            }}
          />
        )}

        {page === "upload" && (
          <MeetingUpload onUploaded={openMeeting} onCancel={() => setPage("dashboard")} />
        )}

        {page === "analytics" && <Analytics />}

        {page === "profile" && <Profile user={currentUser} />}

        {page === "settings" && <Settings user={currentUser} onLogout={onLogout} />}
      </main>
    </div>
  );
}

export default AuthenticatedApp;
