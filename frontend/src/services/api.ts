import { authFetch } from "../auth";

// Same base URL every existing component already hardcodes. Centralized
// here so new pages don't repeat the literal string.
export const API_BASE_URL = "http://localhost:8000";

export class ApiError extends Error {}

/**
 * Runs an authFetch call and returns parsed JSON, or throws an ApiError
 * with the backend's `detail` message — the same FastAPI HTTPException
 * convention every existing component already relies on.
 */
export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await authFetch(`${API_BASE_URL}${path}`, init);
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const message = (data && (data as { detail?: string }).detail) || "Something went wrong.";
    throw new ApiError(message);
  }

  return data as T;
}

export function toErrorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}
