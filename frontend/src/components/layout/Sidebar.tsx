"use client";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/authStore";
import { useAppStore } from "@/stores/appStore";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const mainLinks = [
  { href: "/dashboard", label: "工作空间", icon: "⊞" },
  { href: "/settings", label: "个人设置", icon: "⚙" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { sidebarOpen } = useAppStore();

  if (!sidebarOpen) return null;

  return (
    <aside className="w-60 bg-surface-1 border-r border-border flex flex-col shrink-0">
      {/* Logo */}
      <div className="h-14 flex items-center gap-2.5 px-4 border-b border-border">
        <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center shrink-0">
          <span className="text-black font-bold text-xs">M</span>
        </div>
        <span className="font-semibold text-sm tracking-tight">MiniPlane</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {mainLinks.map((l) => {
          const active = pathname === l.href || pathname.startsWith(l.href + "/");
          return (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                active
                  ? "bg-accent/10 text-accent"
                  : "text-muted hover:text-fg hover:bg-surface-2",
              )}
            >
              <span className="text-base w-5 text-center">{l.icon}</span>
              {l.label}
            </Link>
          );
        })}
      </nav>

      {/* User footer */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-8 h-8 rounded-full bg-surface-3 border border-border flex items-center justify-center text-xs font-semibold text-muted">
            {user?.name?.slice(0, 2).toUpperCase() || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted truncate">{user?.email}</p>
          </div>
          <button
            onClick={() => {
              import("@/lib/api").then((m) => {
                const refresh = sessionStorage.getItem("refresh_token");
                if (refresh) m.default.post("/auth/logout/", { refresh }).catch(() => {});
              });
              logout(); router.push("/login"); toast.success("已退出登录");
            }}
            className="text-muted hover:text-danger transition-colors text-sm"
            title="退出登录"
          >
            ↵
          </button>
        </div>
      </div>
    </aside>
  );
}
