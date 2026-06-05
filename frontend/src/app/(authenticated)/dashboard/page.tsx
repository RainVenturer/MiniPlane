"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import api from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Spinner from "@/components/ui/Spinner";
import type { Workspace } from "@/types";
import { toast } from "sonner";

export default function DashboardPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editingWs, setEditingWs] = useState<Workspace | null>(null);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const queryClient = useQueryClient();

  const { data: workspaces, isLoading } = useQuery<Workspace[]>({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const { data } = await api.get("/workspaces/");
      return (data as { results?: Workspace[] }).results || (Array.isArray(data) ? data as Workspace[] : []);
    },
  });

  const createWs = useMutation({
    mutationFn: () => api.post("/workspaces/", { name, description: desc }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      setShowCreate(false); setName(""); setDesc("");
      toast.success("工作空间创建成功");
    },
    onError: () => toast.error("创建失败"),
  });

  const updateWs = useMutation({
    mutationFn: () => api.put(`/workspaces/${editingWs!.id}/`, { name, description: desc }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      setShowEdit(false); setEditingWs(null);
      toast.success("工作空间已更新");
    },
  });

  const deleteWs = useMutation({
    mutationFn: (id: string) => api.delete(`/workspaces/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      toast.success("工作空间已删除");
    },
  });

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>;

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold">我的工作空间</h2>
          <p className="text-muted text-sm mt-1">选择或创建一个工作空间开始协作</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>+ 创建工作空间</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workspaces?.map((ws: Workspace) => (
          <div key={ws.id} className="group relative p-6 bg-surface-1 border border-border rounded-2xl hover:border-accent/30 hover:bg-surface-2 transition-all duration-300">
            <Link href={`/workspaces/${ws.id}`} className="block">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center text-accent font-bold text-lg">
                {ws.name[0]}
              </div>
              <div>
                <h3 className="font-semibold group-hover:text-accent transition-colors">{ws.name}</h3>
                <p className="text-xs text-muted">{ws.slug}</p>
              </div>
            </div>
            {ws.description && <p className="text-sm text-muted line-clamp-2 mb-3">{ws.description}</p>}
            <div className="flex items-center gap-3 text-xs text-muted">
              <span>{ws.member_count} 位成员</span>
              <span>·</span>
              <span>所有者 {ws.owner_name}</span>
            </div>
            </Link>
            <div className="absolute top-3 right-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button size="sm" variant="ghost" onClick={(e) => {
                e.preventDefault(); setEditingWs(ws); setName(ws.name); setDesc(ws.description || ""); setShowEdit(true);
              }}>编辑</Button>
              <Button size="sm" variant="ghost" onClick={(e) => {
                e.preventDefault(); if (confirm("删除工作空间？")) deleteWs.mutate(ws.id);
              }}>删除</Button>
            </div>
          </div>
        ))}
      </div>

      {workspaces?.length === 0 && (
        <div className="text-center py-20">
          <p className="text-muted mb-4">还没有工作空间</p>
          <Button onClick={() => setShowCreate(true)}>创建第一个工作空间</Button>
        </div>
      )}

      {/* Edit Modal */}
      <Modal open={showEdit} onClose={() => { setShowEdit(false); setEditingWs(null); }} title="编辑工作空间">
        <div className="space-y-4">
          <Input label="工作空间名称" value={name} onChange={(e) => setName(e.target.value)} />
          <Input label="描述" value={desc} onChange={(e) => setDesc(e.target.value)} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => { setShowEdit(false); setEditingWs(null); }}>取消</Button>
            <Button onClick={() => updateWs.mutate()} disabled={!name}>保存</Button>
          </div>
        </div>
      </Modal>

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="创建工作空间">
        <div className="space-y-4">
          <Input label="工作空间名称" value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：开发团队" />
          <Input label="描述（可选）" value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="简要描述工作空间用途" />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
            <Button onClick={() => createWs.mutate()} disabled={!name || createWs.isPending}>
              {createWs.isPending ? "创建中..." : "创建"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
