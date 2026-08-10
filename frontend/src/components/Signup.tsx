import { useState, FormEvent } from "react";
import Button from "./ui/Button";
import { Field, PasswordField } from "./ui/Input";
import WaveformMark from "./ui/WaveformMark";

const API_BASE_URL = "http://localhost:8000";

interface SignupProps {
  onSignupSuccess: (token: string) => void;
  onSwitchToLogin: () => void;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

function Signup({ onSignupSuccess, onSwitchToLogin }: SignupProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setErrorMessage(null);

    if (!fullName.trim() || !email.trim() || !password || !confirmPassword) {
      setErrorMessage("All fields are required.");
      return;
    }
    if (password.length < 8) {
      setErrorMessage("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name: fullName, email, password }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Sign up failed.");
      }

      const result = data as TokenResponse;
      onSignupSuccess(result.access_token);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Sign up failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <aside className="auth-brand" aria-hidden="true">
        <div className="auth-brand-name">Meridian</div>
        <div className="auth-brand-copy">
          <h2>Stop re-reading meetings to find what was decided.</h2>
          <p>
            Upload a recording and get a searchable transcript, a summary, and every action item,
            decision, and deadline — pulled out automatically.
          </p>
          <WaveformMark color="rgba(255,255,255,0.85)" className="auth-brand-mark" />
        </div>
        <div className="auth-brand-foot">meeting intelligence platform</div>
      </aside>

      <div className="auth-form-panel">
        <div className="auth-form-inner">
          <h1>Create your account</h1>
          <p className="auth-form-sub">Start turning meetings into a searchable record.</p>

          <form onSubmit={handleSubmit} noValidate>
            <Field
              label="Full name"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
            <Field
              label="Email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <PasswordField
              label="Password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              hint="At least 8 characters."
              required
            />
            <PasswordField
              label="Confirm password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

            <Button type="submit" block disabled={isLoading}>
              {isLoading ? "Creating account…" : "Create account"}
            </Button>
          </form>

          {errorMessage && (
            <div className="callout-error" role="alert">
              {errorMessage}
            </div>
          )}

          <p className="auth-switch">
            Already have an account?{" "}
            <button type="button" className="auth-switch-link" onClick={onSwitchToLogin}>
              Log in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Signup;
