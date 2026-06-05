"use client";
import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { useAppStore } from "@/stores/appStore";
import { useNotificationStore } from "@/stores/notificationStore";
import api from "@/lib/api";
import { wsClient } from "@/lib/websocket";
import { auth } from "@/lib/auth";
import { timeAgo } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Notification } from "@/types";

export default function TopBar() {
  const pathname = usePathname();
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);
  const { notifications, unreadCount, setNotifications, addNotification, markRead, markAllRead } =
    useNotificationStore();
  const [notifOpen, setNotifOpen] = useState(false);

  // Fetch notifications
  useEffect(() => {
    api.get("/notifications/").then(({ data }) => {
      const list = (data as { results?: Notification[] }).results || (Array.isArray(data) ? data as Notification[] : []);
      setNotifications(list);
    }).catch(() => {});
  }, [setNotifications]);

  // WebSocket for real-time notifications
  useEffect(() => {
    const token = auth.getAccessToken();
    if (!token) return;
    wsClient.connect("/notifications/", token);
    const unsub = wsClient.on("*", (msg) => {
      const n = msg as Notification;
      addNotification(n);
    });
    return () => { unsub(); wsClient.disconnect(); };
  }, [addNotification]);

  // Page title from path
  const getTitle = () => {
    if (pathname === "/dashboard") return "我的工作空间";
    if (pathname.match(/\/workspaces\//)) return "项目列表";
    if (pathname.match(/\/projects\/.*\/list/)) return "列表视图";
    if (pathname.match(/\/projects\/.*\/iterations/)) return "迭代管理";
    if (pathname.match(/\/projects\/.*\/modules/)) return "模块管理";
    if (pathname.match(/\/projects\/.*\/settings/)) return "项目设置";
    if (pathname.match(/\/projects\//)) return "看板";
    return "";
  };

  return (
    <header className="h-14 bg-surface-1 border-b border-border flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="w-8 h-8 rounded-lg bg-surface-2 hover:bg-surface-3 flex items-center justify-center text-muted hover:text-fg transition-all"
        >
          ☰
        </button>
        <h1 className="text-sm font-semibold tracking-wide">{getTitle()}</h1>
      </div>

      <div className="flex items-center gap-2">
        {/* Notification bell */}
        <div className="relative">
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            className={cn(
              "w-8 h-8 rounded-lg bg-surface-2 hover:bg-surface-3 flex items-center justify-center text-muted hover:text-fg transition-all relative",
              notifOpen && "bg-surface-3 text-fg",
            )}
          >
            🔔
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-danger text-white text-[10px] font-bold flex items-center justify-center animate-bell">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {/* Dropdown */}
          {notifOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setNotifOpen(false)} />
              <div className="absolute right-0 top-12 z-50 w-80 bg-surface-1 border border-border rounded-2xl shadow-2xl animate-fade-in">
                <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                  <span className="text-sm font-semibold">通知</span>
                  {unreadCount > 0 && (
                    <button onClick={() => {
                      api.post("/notifications/read-all/").then(() => markAllRead()).catch(() => {});
                    }} className="text-xs text-accent hover:text-accent-dim transition-colors">
                      全部已读
                    </button>
                  )}
                </div>
                <div className="max-h-80 overflow-auto">
                  {notifications.length === 0 ? (
                    <p className="text-sm text-muted text-center py-8">暂无通知</p>
                  ) : (
                    notifications.slice(0, 20).map((n) => (
                      <div
                        key={n.id}
                        onClick={() => { api.patch(`/notifications/${n.id}/read/`).catch(() => {}); markRead(n.id); }}
                        className={cn(
                          "px-4 py-3 border-b border-border last:border-0 hover:bg-surface-2 transition-colors cursor-pointer",
                          !n.is_read && "bg-accent/5",
                        )}
                      >
                        <p className="text-sm">{n.message}</p>
                        <p className="text-xs text-muted mt-1">{timeAgo(n.created_at)}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
