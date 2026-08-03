"use client";

/**
 * AuthContext — provides the current user, auth state, login/logout actions,
 * and silent refresh scheduling.
 *
 * Silent refresh: we decode the access_token JWT to read its `exp` claim
 * and schedule a refresh 60 seconds before expiry. This keeps sessions alive
 * without the user noticing. On every mount we also check the stored token
 * and restore the session if valid (or refresh if expired).
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { login as apiLogin, refreshTokens, getMe, type UserOut } from "@/lib/api/auth";
import { tokenStorage } from "@/lib/auth/tokenStorage";

// ── JWT decode (no library needed — we just read the payload) ────────────────

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const payloadB64 = token.split(".")[1];
    if (!payloadB64) return null;
    // Base64url → Base64 → JSON
    const padded = payloadB64.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(padded);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function getTokenExpMs(token: string): number | null {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== "number") return null;
  return payload.exp * 1000; // seconds → ms
}

// ── Context shape ─────────────────────────────────────────────────────────────

interface AuthContextValue {
  user: UserOut | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Schedule a silent refresh 60s before expiry
  const scheduleRefresh = useCallback((accessToken: string) => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }

    const expMs = getTokenExpMs(accessToken);
    if (!expMs) return;

    const nowMs = Date.now();
    const msUntilRefresh = expMs - nowMs - 60_000; // 60s buffer

    if (msUntilRefresh <= 0) {
      // Already expired or about to — refresh immediately
      void performRefresh();
      return;
    }

    refreshTimerRef.current = setTimeout(() => {
      void performRefresh();
    }, msUntilRefresh);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const performRefresh = useCallback(async () => {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) {
      logout();
      return;
    }

    try {
      const tokens = await refreshTokens({ refresh_token: refreshToken });
      tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
      scheduleRefresh(tokens.access_token);
    } catch {
      // Refresh failed — force re-login
      logout();
    }
  }, [scheduleRefresh]); // eslint-disable-line react-hooks/exhaustive-deps

  const logout = useCallback(() => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
    tokenStorage.clearTokens();
    setUser(null);
    router.push("/login");
  }, [router]);

  // On mount: restore session from stored tokens
  useEffect(() => {
    const restore = async () => {
      const accessToken = tokenStorage.getAccessToken();
      if (!accessToken) {
        setIsLoading(false);
        return;
      }

      // Check if expired — if so, try refresh first
      const expMs = getTokenExpMs(accessToken);
      if (expMs && Date.now() >= expMs) {
        await performRefresh();
        setIsLoading(false);
        return;
      }

      try {
        const me = await getMe(accessToken);
        setUser(me);
        scheduleRefresh(accessToken);
      } catch {
        // Token invalid on server — clear and redirect
        tokenStorage.clearTokens();
      } finally {
        setIsLoading(false);
      }
    };

    void restore();

    return () => {
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(
    async (username: string, password: string) => {
      const tokens = await apiLogin({ username, password });
      tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);

      const me = await getMe(tokens.access_token);
      setUser(me);
      scheduleRefresh(tokens.access_token);

      router.push("/chat");
    },
    [router, scheduleRefresh]
  );

  const getAccessToken = useCallback(() => tokenStorage.getAccessToken(), []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return ctx;
}
