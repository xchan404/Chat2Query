/**
 * Auth API client — typed wrappers for /api/auth/* endpoints.
 * Source of truth: openapi.json — do not reconstruct shapes from memory.
 *
 * POST /api/auth/login   → LoginRequest  → TokenPair
 * POST /api/auth/refresh → RefreshRequest → TokenPair
 * GET  /api/auth/me      → (bearer)       → UserOut
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Shapes from openapi.json ──────────────────────────────────────────────────

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserOut {
  id: string;
  tenant_id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  roles: string[];
  created_at: string | null;
}

// ── Helper ────────────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  init: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message: string =
      body?.detail ??
      (Array.isArray(body?.detail)
        ? body.detail.map((d: { msg: string }) => d.msg).join(", ")
        : "Request failed");
    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

// ── Endpoints ─────────────────────────────────────────────────────────────────

export async function login(req: LoginRequest): Promise<TokenPair> {
  return apiFetch<TokenPair>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function refreshTokens(req: RefreshRequest): Promise<TokenPair> {
  return apiFetch<TokenPair>("/api/auth/refresh", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function getMe(accessToken: string): Promise<UserOut> {
  return apiFetch<UserOut>("/api/auth/me", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}
