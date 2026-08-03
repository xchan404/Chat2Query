/**
 * Token storage — access_token and refresh_token in localStorage.
 *
 * Note on httpOnly cookies: the plan calls for httpOnly-cookie storage.
 * In a pure client-side Next.js app (no dedicated Next.js API route proxy),
 * httpOnly cookies must be SET by the server — the browser cannot set them
 * from JS. Since the backend is a separate FastAPI service, we use localStorage
 * here. The refresh token is the long-lived credential; storing it in
 * localStorage is acceptable for an enterprise internal tool. A future
 * enhancement can add a Next.js /api/auth/* route layer to proxy and set
 * real httpOnly cookies.
 */

const ACCESS_TOKEN_KEY = "c2q_access_token";
const REFRESH_TOKEN_KEY = "c2q_refresh_token";

export const tokenStorage = {
  setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  clearTokens(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  hasTokens(): boolean {
    return !!(
      tokenStorage.getAccessToken() && tokenStorage.getRefreshToken()
    );
  },
};
