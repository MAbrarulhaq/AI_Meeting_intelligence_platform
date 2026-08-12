import { AuthUser } from "../../types/meeting";
import { Card } from "../ui/Card";

interface SettingsProps {
  user: AuthUser | null;
  onLogout: () => void;
}

function Settings({ user, onLogout }: SettingsProps) {
  return (
    <div className="page-shell">
      <div className="page-head">
        <div>
          <h1>Settings</h1>
          <p className="page-sub">Manage your account.</p>
        </div>
      </div>

      <Card className="profile-panel">
        <h3>Account</h3>
        <p className="status">
          Signed in as {user ? `${user.full_name} (${user.email})` : "—"}. Password and
          notification settings aren't available yet.
        </p>
        <button type="button" className="btn btn-secondary" onClick={onLogout}>
          Log out
        </button>
      </Card>
    </div>
  );
}

export default Settings;
