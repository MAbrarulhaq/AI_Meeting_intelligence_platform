import { useState } from "react";
import AccountMenu from "./AccountMenu";
import Button from "../ui/Button";
import { AuthenticatedPage, NavTarget } from "../../types/navigation";
import { AuthUser } from "../../types/meeting";

interface NavbarProps {
  user: AuthUser | null;
  activePage: AuthenticatedPage;
  onNavigate: (target: NavTarget) => void;
  onLogout: () => void;
}

const NAV_LINKS: { page: AuthenticatedPage; label: string }[] = [
  { page: "dashboard", label: "Dashboard" },
  { page: "meetings", label: "Meetings" },
  { page: "analytics", label: "Analytics" },
];

function Navbar({ user, activePage, onNavigate, onLogout }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (page: AuthenticatedPage) =>
    page === activePage || (page === "meetings" && activePage === "meeting-details");

  return (
    <header className="app-navbar">
      <div className="app-navbar-inner">
        <button
          type="button"
          className="app-navbar-logo"
          onClick={() => onNavigate({ page: "dashboard" })}
        >
          Meridian
        </button>

        <nav className="app-navbar-links" aria-label="Primary">
          {NAV_LINKS.map((link) => (
            <button
              key={link.page}
              type="button"
              className={`app-navbar-link ${isActive(link.page) ? "app-navbar-link-active" : ""}`}
              onClick={() => onNavigate({ page: link.page })}
            >
              {link.label}
            </button>
          ))}
        </nav>

        <div className="app-navbar-right">
          <Button
            variant="secondary"
            size="sm"
            className="app-navbar-upload-btn"
            onClick={() => onNavigate({ page: "upload" })}
          >
            + New Meeting
          </Button>
          <AccountMenu
            user={user}
            onNavigate={(page) => onNavigate({ page })}
            onLogout={onLogout}
          />
          <button
            type="button"
            className="app-navbar-burger"
            aria-label="Open menu"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((v) => !v)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </div>

      {mobileOpen && (
        <nav className="app-navbar-mobile" aria-label="Primary mobile">
          {NAV_LINKS.map((link) => (
            <button
              key={link.page}
              type="button"
              className={`app-navbar-mobile-link ${
                isActive(link.page) ? "app-navbar-link-active" : ""
              }`}
              onClick={() => {
                setMobileOpen(false);
                onNavigate({ page: link.page });
              }}
            >
              {link.label}
            </button>
          ))}
          <button
            type="button"
            className="app-navbar-mobile-link"
            onClick={() => {
              setMobileOpen(false);
              onNavigate({ page: "upload" });
            }}
          >
            + New Meeting
          </button>
          <button
            type="button"
            className="app-navbar-mobile-link"
            onClick={() => {
              setMobileOpen(false);
              onNavigate({ page: "profile" });
            }}
          >
            Profile
          </button>
          <button
            type="button"
            className="app-navbar-mobile-link"
            onClick={() => {
              setMobileOpen(false);
              onNavigate({ page: "settings" });
            }}
          >
            Settings
          </button>
          <button
            type="button"
            className="app-navbar-mobile-link app-navbar-mobile-link-danger"
            onClick={onLogout}
          >
            Log out
          </button>
        </nav>
      )}
    </header>
  );
}

export default Navbar;
