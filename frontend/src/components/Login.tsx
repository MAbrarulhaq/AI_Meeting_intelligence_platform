import { useState, FormEvent } from "react";
import Button from "./ui/Button";
import { Field, PasswordField } from "./ui/Input";
import WaveformMark from "./ui/WaveformMark";

const API_BASE_URL = "http://localhost:8000";

interface LoginProps {
  onLoginSuccess: (token: string) => void;
  onSwitchToSignup: () => void;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

function Login({ onLoginSuccess, onSwitchToSignup }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed. Check your email and password.");
      }

      const result = data as TokenResponse;
      onLoginSuccess(result.access_token);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Login failed. Check your email and password."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <aside className="auth-brand" aria-hidden="true">
        <div className="auth-brand-name">Meridian</div>
        <div className="auth-brand-copy">
          <h2>Every meeting, turned into something you can act on.</h2>
          <p>
            Transcripts, speakers, decisions, and action items — organized automatically, so
            nothing said in a meeting gets lost after it ends.
          </p>
          <WaveformMark
            color="rgba(255,255,255,0.85)"
            className="auth-brand-mark"
          />
        </div>
        <div className="auth-brand-foot">meeting intelligence platform</div>
      </aside>

      <div className="auth-form-panel">
        <div className="auth-form-inner">
          <h1>Log in</h1>
          <p className="auth-form-sub">Welcome back. Enter your details to continue.</p>

          <form onSubmit={handleSubmit} noValidate>
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
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button type="submit" block disabled={isLoading}>
              {isLoading ? "Logging in…" : "Log in"}
            </Button>
          </form>

          {errorMessage && (
            <div className="callout-error" role="alert">
              {errorMessage}
            </div>
          )}

          <p className="auth-switch">
            Don't have an account?{" "}
            <button type="button" className="auth-switch-link" onClick={onSwitchToSignup}>
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
