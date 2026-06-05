// ── 全局 UI 状态 ─────────────────────────────────────────────────
import { create } from "zustand";

interface AppState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  taskDetailId: string | null;
  openTaskDetail: (id: string) => void;
  closeTaskDetail: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  taskDetailId: null,
  openTaskDetail: (id) => set({ taskDetailId: id }),
  closeTaskDetail: () => set({ taskDetailId: null }),
}));
