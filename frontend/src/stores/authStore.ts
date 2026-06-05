// ── 认证状态管理 ─────────────────────────────────────────────────
import { create } from "zustand";
import type { User } from "@/types";
import { auth } from "@/lib/auth";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User) => void;
  login: (user: User, access: string, refresh: string) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) => set({ user }),

  login: (user, access, refresh) => {
    auth.setTokens({ access, refresh });
    auth.setUser(user);
    set({ user, isAuthenticated: true });
  },

  logout: () => {
    auth.clear();
    set({ user: null, isAuthenticated: false });
  },

  hydrate: () => {
    const user = auth.getUser();
    const hasToken = auth.isAuthenticated();
    set({ user, isAuthenticated: !!user && hasToken, isLoading: false });
  },
}));
