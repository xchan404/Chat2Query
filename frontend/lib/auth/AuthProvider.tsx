"use client";

/**
 * AuthProvider & TenantContext — provides current authenticated UserOut context,
 * login, logout, and automated silent token refresh before JWT expiration.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { authApi, type UserOut, type LoginRequest } from "@/lib/api/auth";

interface AuthContextType {
  user: UserOut | null;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  login: async () => {},
  logout: async () => {},
  refresh: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);

  const clearRefreshTimer = useCallback(() => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
  }, []);

  const parseJwtExp = (token: string): number | null => {
    try {
      const payloadBase64 = token.split(".")[1];
      if (!payloadBase64) return null;
      const decodedJson = atob(payloadBase64);
      const payload = JSON.parse(decodedJson);
      return typeof payload.exp === "number" ? payload.exp : null;
    } catch {
      return null;
    }
  };

  const scheduleSilentRefresh = useCallback((accessToken: string) => {
    clearRefreshTimer();
    const expUnix = parseJwtExp(accessToken);
    if (!expUnix) return;

    const nowMs = Date.now();
    const expMs = expUnix * 1000;
    // Schedule refresh 60 seconds before expiration
    const refreshDelayMs = Math.max(expMs - nowMs - 60_000, 5000);

    refreshTimerRef.current = setTimeout(async () => {
      try {
        const tokens = await authApi.refresh();
        if (tokens.access_token) {
          scheduleSilentRefresh(tokens.access_token);
        }
      } catch {
        /* Failed to refresh silently — session expired */
        setUser(null);
      }
    }, refreshDelayMs);
  }, [clearRefreshTimer]);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const userData = await authApi.me();
      setUser(userData);
      // Automatically refresh token on mount to obtain access_token and schedule silent refresh timer
      const tokens = await authApi.refresh();
      if (tokens.access_token) {
        scheduleSilentRefresh(tokens.access_token);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [scheduleSilentRefresh]);

  useEffect(() => {
    fetchCurrentUser();
    return () => clearRefreshTimer();
  }, [fetchCurrentUser, clearRefreshTimer]);

  const login = async (credentials: LoginRequest) => {
    const tokens = await authApi.login(credentials);
    if (tokens.access_token) {
      scheduleSilentRefresh(tokens.access_token);
    }
    const userData = await authApi.me();
    setUser(userData);
    router.push("/chat");
  };

  const logout = async () => {
    clearRefreshTimer();
    try {
      await authApi.logout();
    } catch {
      /* ignore */
    }
    setUser(null);
    router.push("/login");
  };

  const refresh = async () => {
    const tokens = await authApi.refresh();
    if (tokens.access_token) {
      scheduleSilentRefresh(tokens.access_token);
    }
    const userData = await authApi.me();
    setUser(userData);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
