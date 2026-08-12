import { useEffect, useRef, useState } from "react";
import { AuthUser } from "../../types/meeting";

interface AccountMenuProps {
  user: AuthUser | null;
  onNavigate: (page: "profile" | "settings") => void;
  onLogout: () => void;
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase() || "?";
}

function AccountMenu({ user, onNavigate, onLogout }: AccountMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const displayName = user?.full_name || "Your account";

  return (
    <div className="account-menu" ref={ref}>
      <button
        type="button"
        className="account-menu-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span className="account-avatar">{initials(displayName)}</span>
        <span className="account-menu-name">{displayName}</span>
      </button>

      {open && (
        <div className="account-menu-panel" role="menu">
          <div className="account-menu-header">
            <p className="account-menu-header-name">{displayName}</p>
            {user?.email && <p className="account-menu-header-email">{user.email}</p>}
          </div>
          <button
            type="button"
            role="menuitem"
            className="account-menu-item"
            onClick={() => {
              setOpen(false);
              onNavigate("profile");
            }}
          >
            Profile
          </button>
          <button
            type="button"
            role="menuitem"
            className="account-menu-item"
            onClick={() => {
              setOpen(false);
              onNavigate("settings");
            }}
          >
            Settings
          </button>
          <div className="account-menu-divider" />
          <button
            type="button"
            role="menuitem"
            className="account-menu-item account-menu-item-danger"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
          >
            Log out
          </button>
        </div>
      )}
    </div>
  );
}

export default AccountMenu;
