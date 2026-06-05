import { cn } from "@/lib/utils";

export default function Avatar({
  name, src, size = "md",
}: { name: string; src?: string; size?: "sm" | "md" | "lg" }) {
  const initials = name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
  const sizeCls = { sm: "w-6 h-6 text-[10px]", md: "w-8 h-8 text-xs", lg: "w-10 h-10 text-sm" };
  if (src) {
    return <img src={src} alt={name} className={cn("rounded-full object-cover", sizeCls[size])} />;
  }
  return (
    <div className={cn(
      "rounded-full bg-surface-3 border border-border flex items-center justify-center font-semibold text-muted",
      sizeCls[size],
    )}>{initials}</div>
  );
}
