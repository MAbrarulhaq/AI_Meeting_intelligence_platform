import { AuthUser } from "../../types/meeting";
import { Card } from "../ui/Card";
import { formatDate } from "../../utils/format";

interface ProfileProps {
  user: AuthUser | null;
}

function Profile({ user }: ProfileProps) {
  return (
    <div className="page-shell">
      <div className="page-head">
        <div>
          <h1>Profile</h1>
          <p className="page-sub">Your account details.</p>
        </div>
      </div>

      <Card className="profile-panel">
        {!user ? (
          <p className="status">Profile information isn't available right now.</p>
        ) : (
          <dl className="profile-fields">
            <div className="profile-field">
              <dt>Full name</dt>
              <dd>{user.full_name}</dd>
            </div>
            <div className="profile-field">
              <dt>Email</dt>
              <dd>{user.email}</dd>
            </div>
            <div className="profile-field">
              <dt>Member since</dt>
              <dd className="mono">{formatDate(user.created_at)}</dd>
            </div>
          </dl>
        )}
      </Card>
    </div>
  );
}

export default Profile;
