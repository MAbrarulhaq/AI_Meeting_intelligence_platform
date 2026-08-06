// Shared authentication helpers: token storage and a fetch wrapper
// that automatically attaches the Authorization header. Kept in one
// place so no component repeats this logic.

const TOKEN_STORAGE_KEY = "meeting_app_token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

/**
 * Wraps fetch and adds "Authorization: Bearer <token>" automatically
 * when a token is stored. Use this instead of the global fetch for
 * any call that should be authenticated.
 */
export function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(input, { ...init, headers });
}
