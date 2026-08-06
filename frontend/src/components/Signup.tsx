import { useState, FormEvent } from "react";

const API_BASE_URL = "http://localhost:8000";

interface SignupProps {
  onSignupSuccess: (token: string) => void;
  onSwitchToLogin: () => void;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

const fieldStyle: React.CSSProperties = {
  display: "block",
  width: "100%",
  padding: "8px",
  marginTop: "4px",
  boxSizing: "border-box",
};

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
    <div className="container">
      <h1>Sign Up</h1>
      <div className="upload-card">
        <form onSubmit={handleSubmit}>
          <label style={{ display: "block", marginBottom: "12px" }}>
            Full Name
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              style={fieldStyle}
            />
          </label>
          <label style={{ display: "block", marginBottom: "12px" }}>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={fieldStyle}
            />
          </label>
          <label style={{ display: "block", marginBottom: "12px" }}>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              style={fieldStyle}
            />
          </label>
          <label style={{ display: "block", marginBottom: "12px" }}>
            Confirm Password
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              style={fieldStyle}
            />
          </label>
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Signing up..." : "Sign Up"}
          </button>
        </form>

        {errorMessage && <p className="status error">{errorMessage}</p>}

        <p style={{ marginTop: "16px" }}>
          Already have an account?{" "}
          <button type="button" onClick={onSwitchToLogin}>
            Log In
          </button>
        </p>
      </div>
    </div>
  );
}

export default Signup;
