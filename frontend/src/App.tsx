import { useState, useEffect } from "react";
import Login from "./components/Login";
import Signup from "./components/Signup";
import Transcription from "./components/Transcription";
import { authFetch, clearStoredToken, getStoredToken, storeToken } from "./auth";

const API_BASE_URL = "http://localhost:8000";

type View = "login" | "signup" | "app";

interface AuthUser {
  id: string;
  full_name: string;
  email: string;
  created_at: string;
}

function App() {
  const [view, setView] = useState<View>("login");
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);

  // On page load: if a token is already stored, validate it against
  // /auth/me before deciding whether to show Login or the app. This
  // is what makes a refresh keep you logged in instead of always
  // bouncing back to the login page.
  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setCheckingSession(false);
      return;
    }

    authFetch(`${API_BASE_URL}/auth/me`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Session expired.");
        }
        const user = (await response.json()) as AuthUser;
        setCurrentUser(user);
        setView("app");
      })
      .catch(() => {
        clearStoredToken();
      })
      .finally(() => setCheckingSession(false));
  }, []);

  // Shared by both Login and Signup success handlers: store the token,
  // then fetch the profile so the UI has the user's name/email.
  const handleAuthSuccess = async (token: string) => {
    storeToken(token);
    const response = await authFetch(`${API_BASE_URL}/auth/me`);
    if (response.ok) {
      const user = (await response.json()) as AuthUser;
      setCurrentUser(user);
    }
    setView("app");
  };

  const handleLogout = () => {
    clearStoredToken();
    setCurrentUser(null);
    setView("login");
  };

  if (checkingSession) {
    return (
      <div className="container">
        <p className="status">Loading...</p>
      </div>
    );
  }

  if (view === "login") {
    return (
      <Login
        onLoginSuccess={handleAuthSuccess}
        onSwitchToSignup={() => setView("signup")}
      />
    );
  }

  if (view === "signup") {
    return (
      <Signup
        onSignupSuccess={handleAuthSuccess}
        onSwitchToLogin={() => setView("login")}
      />
    );
  }

  return <Transcription currentUser={currentUser} onLogout={handleLogout} />;
}

export default App;
