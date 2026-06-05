import { cn } from "@/lib/utils";

export default function Badge({
  children, className, color,
}: { children: React.ReactNode; className?: string; color?: string }) {
  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border tracking-wide",
      color || "bg-surface-2 text-muted border-border",
      className,
    )}>
      {children}
    </span>
  );
}
