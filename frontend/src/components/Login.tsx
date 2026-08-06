import { useState, FormEvent } from "react";

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
        throw new Error(data.detail || "Login failed.");
      }

      const result = data as TokenResponse;
      onLoginSuccess(result.access_token);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Log In</h1>
      <div className="upload-card">
        <form onSubmit={handleSubmit}>
          <label style={{ display: "block", marginBottom: "12px" }}>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ display: "block", width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ display: "block", marginBottom: "12px" }}>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ display: "block", width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Logging in..." : "Log In"}
          </button>
        </form>

        {errorMessage && <p className="status error">{errorMessage}</p>}

        <p style={{ marginTop: "16px" }}>
          Don't have an account?{" "}
          <button type="button" onClick={onSwitchToSignup}>
            Sign Up
          </button>
        </p>
      </div>
    </div>
  );
}

export default Login;
