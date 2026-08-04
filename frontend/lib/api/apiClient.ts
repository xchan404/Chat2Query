/**
 * Shared authenticated fetch helper.
 * Reads the access token from tokenStorage and injects it as Bearer.
 * Throws an Error with message from the backend's `detail` field on non-2xx.
 */

import { tokenStorage } from "@/lib/auth/tokenStorage";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const token = tokenStorage.getAccessToken();

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body?.detail)) {
        message = body.detail.map((d: { msg: string }) => d.msg).join("; ");
      }
    } catch {
      /* ignore parse error */
    }
    throw new ApiError(message, res.status);
  }

  // Handle 204 No Content
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}
