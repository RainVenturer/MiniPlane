"use client";
import { useParams, usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";

const tabs = (projId: string) => [
  { href: `/projects/${projId}`, label: "看板" },
  { href: `/projects/${projId}/list`, label: "列表" },
  { href: `/projects/${projId}/iterations`, label: "迭代" },
  { href: `/projects/${projId}/modules`, label: "模块" },
  { href: `/projects/${projId}/settings`, label: "统计" },
];

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const { projId } = useParams<{ projId: string }>();
  const pathname = usePathname();

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-1 bg-surface-1 rounded-xl p-1 border border-border w-fit mb-6">
        {tabs(projId).map((t) => (
          <Link
            key={t.href}
            href={t.href}
            className={cn(
              "px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200",
              pathname === t.href
                ? "bg-accent text-black"
                : "text-muted hover:text-fg",
            )}
          >
            {t.label}
          </Link>
        ))}
      </div>
      {children}
    </div>
  );
}
