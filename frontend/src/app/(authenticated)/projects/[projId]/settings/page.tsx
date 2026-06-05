"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Spinner from "@/components/ui/Spinner";
import Avatar from "@/components/ui/Avatar";
import { timeAgo } from "@/lib/utils";
import type { ProjectStats, Activity, ProjectMember } from "@/types";
import { toast } from "sonner";
import { BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

const PRIORITY_COLORS: Record<string, string> = { urgent: "#ef4444", high: "#f97316", medium: "#f59e0b", low: "#10b981", none: "#71718a" };

export default function SettingsPage() {
  const { projId } = useParams<{ projId: string }>();
  const queryClient = useQueryClient();
  const [memberEmail, setMemberEmail] = useState("");

  const { data: members } = useQuery<ProjectMember[]>({
    queryKey: ["project-members", projId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/members/`);
      return (data as { results?: ProjectMember[] }).results || (Array.isArray(data) ? data as ProjectMember[] : []);
    },
  });

  const { data: activities } = useQuery<Activity[]>({
    queryKey: ["project-activities", projId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/activities/`);
      return (data as { results?: Activity[] }).results || (Array.isArray(data) ? data as Activity[] : []);
    },
  });

  const { data: stats, isLoading } = useQuery<ProjectStats>({
    queryKey: ["stats", projId],
    queryFn: async () => {
      const { data } = await api.get<ProjectStats>(`/projects/${projId}/statistics/`);
      return data;
    },
  });

  const addMember = useMutation({
    mutationFn: () => api.post(`/projects/${projId}/members/`, { email: memberEmail, role: "member" }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["project-members", projId] }); setMemberEmail(""); toast.success("成员已添加"); },
  });

  const removeMember = useMutation({
    mutationFn: (uid: string) => api.delete(`/projects/${projId}/members/${uid}/`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["project-members", projId] }); },
  });

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>;
  if (!stats) return null;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-6">项目统计</h2>

      {/* Overview cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: "总任务", value: stats.total_tasks, color: "text-accent" },
          { label: "已完成", value: stats.completed_tasks, color: "text-success" },
          { label: "已逾期", value: stats.overdue_tasks, color: "text-danger" },
          { label: "完成率", value: `${stats.completion_rate}%`, color: "text-info" },
        ].map((c) => (
          <div key={c.label} className="p-5 bg-surface-1 border border-border rounded-2xl">
            <p className="text-xs text-muted mb-1">{c.label}</p>
            <p className={`text-2xl font-bold font-mono ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* Members */}
      <div className="mb-8 p-5 bg-surface-1 border border-border rounded-2xl">
        <h3 className="text-sm font-semibold mb-4">项目成员 ({members?.length || 0})</h3>
        <div className="space-y-2 mb-4">
          {members?.map((m: ProjectMember) => (
            <div key={m.id} className="flex items-center justify-between px-3 py-2 bg-surface-2 rounded-xl text-sm">
              <div className="flex items-center gap-2">
                <Avatar name={m.user_name} size="sm" />
                <span>{m.user_name}</span>
                <span className="text-xs text-muted">{m.user_email}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">{m.role === "admin" ? "管理员" : m.role === "viewer" ? "只读" : "成员"}</span>
                <button onClick={() => { if (confirm("移除成员？")) removeMember.mutate(m.user); }}
                  className="text-muted hover:text-danger text-xs">移除</button>
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <Input placeholder="输入邮箱添加成员" value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} />
          <Button size="sm" onClick={() => addMember.mutate()} disabled={!memberEmail}>添加</Button>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status distribution */}
        <div className="p-5 bg-surface-1 border border-border rounded-2xl">
          <h3 className="text-sm font-semibold mb-4">状态分布</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={stats.status_distribution}
                dataKey="count"
                nameKey="status__name"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={4}
              >
                {stats.status_distribution.map((entry: { status__name: string; status__color: string; count: number }) => (
                  <Cell key={entry.status__name} fill={entry.status__color} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#1e1e2e", border: "1px solid #252530", borderRadius: "12px", color: "#e4e4ef", fontSize: "12px" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Priority distribution */}
        <div className="p-5 bg-surface-1 border border-border rounded-2xl">
          <h3 className="text-sm font-semibold mb-4">优先级分布</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.priority_distribution}>
              <XAxis dataKey="priority" tick={{ fill: "#71718a", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#71718a", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: "#1e1e2e", border: "1px solid #252530", borderRadius: "12px", color: "#e4e4ef", fontSize: "12px" }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {stats.priority_distribution.map((entry: { priority: string; count: number }) => (
                  <Cell key={entry.priority} fill={PRIORITY_COLORS[entry.priority] || "#71718a"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Project Activity Log */}
      <div className="mt-8 p-6 bg-surface-1 border border-border rounded-2xl">
        <h3 className="text-sm font-semibold mb-4">项目动态</h3>
        <div className="space-y-2">
          {activities?.slice(0, 15).map((a: Activity) => (
            <div key={a.id} className="flex items-center gap-3 text-xs text-muted">
              <Avatar name={a.actor_name} size="sm" />
              <span className="font-medium text-fg">{a.actor_name}</span>
              <span>{a.action === "created" ? "创建了任务" : a.action === "status_changed" ? "变更了状态" : a.action}</span>
              {a.task_title && <span className="text-accent">{a.task_title}</span>}
              <span className="ml-auto">{timeAgo(a.created_at)}</span>
            </div>
          ))}
          {(!activities || activities.length === 0) && (
            <p className="text-sm text-muted">暂无动态</p>
          )}
        </div>
      </div>
    </div>
  );
}
