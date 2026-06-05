// ── 工具函数 ──────────────────────────────────────────────────────
import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return "刚刚";
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} 天前`;
  return formatDate(dateStr);
}

export function priorityColor(p: string): string {
  const map: Record<string, string> = {
    urgent: "bg-red-500/20 text-red-400 border-red-500/30",
    high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    low: "bg-green-500/20 text-green-400 border-green-500/30",
    none: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  };
  return map[p] || map.none;
}

export function priorityLabel(p: string): string {
  const map: Record<string, string> = {
    urgent: "紧急",
    high: "高",
    medium: "中",
    low: "低",
    none: "无",
  };
  return map[p] || p;
}
