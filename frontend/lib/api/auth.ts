/**
 * Auth API client — calls Next.js auth route handlers that manage httpOnly cookies.
 * Source of truth: openapi.json.
 */

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token?: string;
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

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message: string =
      typeof body?.detail === "string"
        ? body.detail
        : Array.isArray(body?.detail)
        ? body.detail.map((d: { msg: string }) => d.msg).join(", ")
        : `Authentication error (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export const authApi = {
  login: (credentials: LoginRequest): Promise<TokenPair> =>
    authFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),

  refresh: (refresh_token?: string): Promise<TokenPair> =>
    authFetch("/api/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),

  me: (): Promise<UserOut> =>
    authFetch("/api/auth/me", {
      method: "GET",
    }),

  logout: (): Promise<{ message: string }> =>
    authFetch("/api/auth/logout", {
      method: "POST",
    }),
};
