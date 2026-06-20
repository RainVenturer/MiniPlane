"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import type { LoginResponse } from "@/types";
import { toast } from "sonner";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuthStore();
  const router = useRouter();

  // 已登录用户直接跳转主页
  useEffect(() => {
    if (isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post<LoginResponse>("/auth/login/", { email, password });
      login(data.user, data.access, data.refresh);
      toast.success(`欢迎回来，${data.user.name}`);
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      const friendly = msg?.includes("邮箱或密码") ? "邮箱或密码错误，请重试" :
                       msg?.includes("禁用") ? "账号已被禁用，请联系管理员" : (msg || "登录失败，请检查网络连接");
      setError(friendly);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left — branding */}
      <div className="hidden lg:flex w-[480px] bg-surface-1 flex-col justify-between p-12 border-r border-border">
        <div>
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center">
              <span className="text-black font-bold text-lg">M</span>
            </div>
            <span className="font-semibold text-lg tracking-tight">MiniPlane</span>
          </div>
          <h1 className="text-4xl font-bold leading-tight mb-4">
            轻量级<br />团队项目协作
          </h1>
          <p className="text-muted text-sm leading-relaxed max-w-sm">
            统一工作空间内完成项目管理、任务流转、迭代管理和进度分析。
            让团队协作更高效。
          </p>
        </div>
        <div className="text-xs text-muted">
          &copy; 2026 MiniPlane — 软件体系结构课程项目
        </div>
      </div>

      {/* Right — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-bold mb-1">欢迎回来</h2>
          <p className="text-muted text-sm mb-8">登录你的账号以继续</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="邮箱"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              label="密码"
              type="password"
              placeholder="输入密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && (
              <div className="p-3 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm">{error}</div>
            )}
            <Button type="submit" className="w-full" size="lg" disabled={loading}>
              {loading ? "登录中..." : "登录"}
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-muted">
            还没有账号？{" "}
            <Link href="/register" className="text-accent hover:text-accent-dim font-medium transition-colors">
              注册
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
