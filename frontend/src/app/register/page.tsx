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

export default function RegisterPage() {
  const [name, setName] = useState("");
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
      const { data } = await api.post<LoginResponse>("/auth/register/", { email, name, password });
      login(data.user, data.access, data.refresh);
      toast.success("注册成功！欢迎加入 MiniPlane");
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      const friendly = msg?.includes("已存在") ? "该邮箱已被注册，请直接登录" :
                       msg?.includes("密码") ? "密码长度不能少于 6 位" : (msg || "注册失败，请稍后重试");
      setError(friendly);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex w-[480px] bg-surface-1 flex-col justify-between p-12 border-r border-border">
        <div>
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center">
              <span className="text-black font-bold text-lg">M</span>
            </div>
            <span className="font-semibold text-lg tracking-tight">MiniPlane</span>
          </div>
          <h1 className="text-4xl font-bold leading-tight mb-4">
            开始你的<br />团队协作之旅
          </h1>
          <p className="text-muted text-sm leading-relaxed max-w-sm">
            创建账号，加入或创建工作空间，与团队一起高效管理项目。
          </p>
        </div>
        <div className="text-xs text-muted">
          &copy; 2026 MiniPlane — 软件体系结构课程项目
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-bold mb-1">创建账号</h2>
          <p className="text-muted text-sm mb-8">填写信息完成注册</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input label="姓名" placeholder="你的名字" value={name} onChange={(e) => setName(e.target.value)} required />
            <Input label="邮箱" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input label="密码" type="password" placeholder="至少 6 位" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
            {error && (
              <div className="p-3 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm">{error}</div>
            )}
            <Button type="submit" className="w-full" size="lg" disabled={loading}>
              {loading ? "注册中..." : "注册"}
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-muted">
            已有账号？{" "}
            <Link href="/login" className="text-accent hover:text-accent-dim font-medium transition-colors">
              登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
