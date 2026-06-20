"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { Toaster } from "sonner";
import { useAuthStore } from "@/stores/authStore";

function AuthHydrator({ children }: { children: React.ReactNode }) {
  const hydrate = useAuthStore((s) => s.hydrate);
  useEffect(() => { hydrate(); }, [hydrate]);

  // 跨标签页同步：另一标签登录/退出时本标签自动刷新
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "access_token" && e.newValue !== e.oldValue) {
        window.location.reload();
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 30000, retry: 1 } },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      <AuthHydrator>
        {children}
      </AuthHydrator>
      <Toaster
        position="top-right"
        theme="dark"
        toastOptions={{
          style: { background: "#1e1e2e", border: "1px solid #252530", color: "#e4e4ef" },
        }}
      />
    </QueryClientProvider>
  );
}
