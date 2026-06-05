"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import api from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Spinner from "@/components/ui/Spinner";
import Badge from "@/components/ui/Badge";
import type { Project, WorkspaceMember } from "@/types";
import { toast } from "sonner";

export default function WorkspacePage() {
  const { wsId } = useParams<{ wsId: string }>();
  const queryClient = useQueryClient();
  const [showProject, setShowProject] = useState(false);
  const [showMember, setShowMember] = useState(false);
  const [projName, setProjName] = useState("");
  const [projIdt, setProjIdt] = useState("");
  const [projDesc, setProjDesc] = useState("");
  const [memberEmail, setMemberEmail] = useState("");

  // Edit project state
  const [showEditProject, setShowEditProject] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["projects", wsId] });
    queryClient.invalidateQueries({ queryKey: ["members", wsId] });
  };

  const { data: projects, isLoading } = useQuery<Project[]>({
    queryKey: ["projects", wsId],
    queryFn: async () => {
      const { data } = await api.get(`/workspaces/${wsId}/projects/`);
      return (data as { results?: Project[] }).results || (Array.isArray(data) ? data as Project[] : []);
    },
  });

  const { data: members } = useQuery<WorkspaceMember[]>({
    queryKey: ["members", wsId],
    queryFn: async () => {
      const { data } = await api.get(`/workspaces/${wsId}/members/`);
      return (data as { results?: WorkspaceMember[] }).results || (Array.isArray(data) ? data as WorkspaceMember[] : []);
    },
  });

  const createProject = useMutation({
    mutationFn: () => api.post(`/workspaces/${wsId}/projects/`, { name: projName, identifier: projIdt, description: projDesc }),
    onSuccess: () => { invalidate(); setShowProject(false); setProjName(""); setProjIdt(""); setProjDesc(""); },
  });

  const updateProject = useMutation({
    mutationFn: () => api.put(`/projects/${editingProject!.id}/`, { name: projName, description: projDesc }),
    onSuccess: () => { invalidate(); setShowEditProject(false); setEditingProject(null); toast.success("项目已更新"); },
  });

  const deleteProject = useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${id}/`),
    onSuccess: () => { invalidate(); toast.success("项目已删除"); },
  });

  const addMember = useMutation({
    mutationFn: () => api.post(`/workspaces/${wsId}/members/`, { email: memberEmail, role: "member" }),
    onSuccess: () => { invalidate(); setMemberEmail(""); },
  });

  const changeMemberRole = useMutation({
    mutationFn: ({ uid, role }: { uid: string; role: string }) =>
      api.put(`/workspaces/${wsId}/members/${uid}/`, { role }),
    onSuccess: () => invalidate(),
  });

  const removeMember = useMutation({
    mutationFn: (uid: string) => api.delete(`/workspaces/${wsId}/members/${uid}/`),
    onSuccess: () => invalidate(),
  });

  const archiveProject = useMutation({
    mutationFn: (id: string) => api.post(`/projects/${id}/archive/`),
    onSuccess: () => invalidate(),
  });

  const restoreProject = useMutation({
    mutationFn: (id: string) => api.post(`/projects/${id}/restore/`),
    onSuccess: () => invalidate(),
  });

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold">项目列表</h2>
          <p className="text-muted text-sm mt-1">{projects?.length || 0} 个项目</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setShowMember(true)}>成员管理</Button>
          <Button onClick={() => setShowProject(true)}>+ 创建项目</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects?.map((p: Project) => (
          <div key={p.id} className="p-5 bg-surface-1 border border-border rounded-2xl hover:border-accent/30 transition-all duration-300 group relative">
            <Link href={`/projects/${p.id}`} className="block">
              <div className="flex items-center gap-2 mb-2">
                <Badge color="bg-accent/10 text-accent border-accent/20">{p.identifier}</Badge>
                {p.is_archived && <Badge color="bg-danger/10 text-danger border-danger/20">已归档</Badge>}
              </div>
              <h3 className="font-semibold group-hover:text-accent transition-colors">{p.name}</h3>
              {p.description && <p className="text-sm text-muted line-clamp-2 mt-1">{p.description}</p>}
              <div className="flex items-center gap-3 text-xs text-muted mt-3">
                <span>{p.task_count} 任务</span>
                <span>{p.member_count} 成员</span>
                {p.lead_name && <span>负责人: {p.lead_name}</span>}
              </div>
            </Link>
            <div className="absolute top-3 right-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button size="sm" variant="ghost" onClick={(e) => {
                e.preventDefault(); setEditingProject(p); setProjName(p.name); setProjDesc(p.description || ""); setShowEditProject(true);
              }}>编辑</Button>
              <Button size="sm" variant="ghost" onClick={(e) => { e.preventDefault(); if (confirm("删除项目？")) deleteProject.mutate(p.id); }}>删除</Button>
              {p.is_archived ? (
                <Button size="sm" variant="ghost" onClick={(e) => { e.preventDefault(); restoreProject.mutate(p.id); }}>恢复</Button>
              ) : (
                <Button size="sm" variant="ghost" onClick={(e) => { e.preventDefault(); archiveProject.mutate(p.id); }}>归档</Button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Create Project Modal */}
      <Modal open={showProject} onClose={() => setShowProject(false)} title="创建项目">
        <div className="space-y-4">
          <Input label="项目名称" value={projName} onChange={(e) => setProjName(e.target.value)} placeholder="例如：MiniPlane" />
          <Input label="标识符" value={projIdt} onChange={(e) => setProjIdt(e.target.value.toUpperCase())} placeholder="例如：MP (字母数字)" />
          <Input label="描述（可选）" value={projDesc} onChange={(e) => setProjDesc(e.target.value)} placeholder="项目描述" />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setShowProject(false)}>取消</Button>
            <Button onClick={() => createProject.mutate()} disabled={!projName || !projIdt || createProject.isPending}>
              {createProject.isPending ? "创建中..." : "创建"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Project Modal */}
      <Modal open={showEditProject} onClose={() => { setShowEditProject(false); setEditingProject(null); }} title="编辑项目">
        <div className="space-y-4">
          <Input label="项目名称" value={projName} onChange={(e) => setProjName(e.target.value)} />
          <Input label="描述" value={projDesc} onChange={(e) => setProjDesc(e.target.value)} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => { setShowEditProject(false); setEditingProject(null); }}>取消</Button>
            <Button onClick={() => updateProject.mutate()} disabled={!projName}>保存</Button>
          </div>
        </div>
      </Modal>

      {/* Members Modal */}
      <Modal open={showMember} onClose={() => setShowMember(false)} title="成员管理">
        <div className="space-y-3">
          {members?.map((m: WorkspaceMember) => (
            <div key={m.id} className="flex items-center justify-between p-3 bg-surface-2 rounded-xl">
              <div>
                <p className="text-sm font-medium">{m.user_name}</p>
                <p className="text-xs text-muted">{m.user_email}</p>
              </div>
              <div className="flex items-center gap-2">
                <select value={m.role} onChange={(e) => changeMemberRole.mutate({ uid: m.user, role: e.target.value })}
                  className="px-2 py-1 text-xs bg-surface-1 border border-border rounded-lg text-fg">
                  <option value="admin">管理员</option>
                  <option value="member">成员</option>
                  <option value="guest">访客</option>
                </select>
                <Button size="sm" variant="ghost" onClick={() => { if (confirm("移除成员？")) removeMember.mutate(m.user); }}>移除</Button>
              </div>
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <Input placeholder="输入邮箱邀请成员" value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} />
            <Button size="sm" onClick={() => addMember.mutate()} disabled={!memberEmail || addMember.isPending}>
              {addMember.isPending ? "邀请中..." : "邀请"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
