// ── 认证工具 ─────────────────────────────────────────────────────
import type { User, AuthTokens } from "@/types";

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
const USER_KEY = "user";

export const auth = {
  setTokens({ access, refresh }: AuthTokens) {
    sessionStorage.setItem(ACCESS_KEY, access);
    sessionStorage.setItem(REFRESH_KEY, refresh);
  },

  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem(ACCESS_KEY);
  },

  getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem(REFRESH_KEY);
  },

  setUser(user: User) {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  getUser(): User | null {
    if (typeof window === "undefined") return null;
    const raw = sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  clear() {
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    sessionStorage.removeItem(USER_KEY);
  },

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  },
};
