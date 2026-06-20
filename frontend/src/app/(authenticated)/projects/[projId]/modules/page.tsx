"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import { priorityColor, priorityLabel } from "@/lib/utils";
import type { Module, Task } from "@/types";
import { toast } from "sonner";

export default function ModulesPage() {
  const { projId } = useParams<{ projId: string }>();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editingModule, setEditingModule] = useState<Module | null>(null);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["modules", projId] });
    queryClient.invalidateQueries({ queryKey: ["tasks", projId] });
    queryClient.invalidateQueries({ queryKey: ["tasks", projId, "list"] });
  };

  const { data: modules, isLoading } = useQuery<Module[]>({
    queryKey: ["modules", projId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/modules/`);
      return (data as { results?: Module[] }).results || (Array.isArray(data) ? data as Module[] : []);
    },
  });

  const { data: allTasks } = useQuery<Task[]>({
    queryKey: ["tasks", projId, "list"],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/tasks/`, { params: { page_size: 200 } });
      return (data as { results?: Task[] }).results || (Array.isArray(data) ? data as Task[] : []);
    },
  });

  const updateModule = useMutation({
    mutationFn: () => api.put(`/modules/${editingModule!.id}/`, { name, description: desc }),
    onSuccess: () => { invalidate(); setShowEdit(false); setEditingModule(null); toast.success("模块已更新"); },
  });

  const createModule = useMutation({
    mutationFn: () => api.post(`/projects/${projId}/modules/`, { name, description: desc }),
    onSuccess: () => { invalidate(); setShowCreate(false); setName(""); setDesc(""); toast.success("模块创建成功"); },
  });

  const removeTaskFromModule = useMutation({
    mutationFn: (taskId: string) => api.put(`/tasks/${taskId}/`, { module: null }),
    onSuccess: () => invalidate(),
  });

  const deleteModule = useMutation({
    mutationFn: (id: string) => api.delete(`/modules/${id}/`),
    onSuccess: () => invalidate(),
  });

  const tasks = allTasks || [];

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">模块管理</h2>
        <Button onClick={() => setShowCreate(true)} size="sm">+ 创建模块</Button>
      </div>

      {modules?.map((m: Module) => {
        const modTasks = tasks.filter((t: Task) => t.module === m.id);
        return (
          <div key={m.id} className="mb-4 p-4 bg-surface-1 border border-border rounded-2xl group">
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{m.name}</h3>
                  <Badge>{modTasks.length} 个任务</Badge>
                  {m.lead_name && <span className="text-xs text-muted">负责人: {m.lead_name}</span>}
                </div>
                {m.description && <p className="text-sm text-muted mt-1">{m.description}</p>}
              </div>
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => {
                  setEditingModule(m); setName(m.name); setDesc(m.description || ""); setShowEdit(true);
                }} className="text-xs text-muted hover:text-accent transition-colors">编辑</button>
                <button onClick={() => { if (confirm("确定删除模块？")) deleteModule.mutate(m.id); }}
                  className="text-xs text-muted hover:text-danger transition-colors">删除</button>
              </div>
            </div>

            {/* Tasks in this module */}
            {modTasks.length > 0 ? (
              <div className="space-y-1 mt-3">
                {modTasks.map((t: Task) => (
                  <div key={t.id} className="flex items-center justify-between px-3 py-2 bg-surface-2 rounded-xl text-sm task-group group">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: t.status_color }} />
                      <span className="truncate">{t.title}</span>
                      <span className="text-[10px] px-1 py-0.5 rounded font-semibold border shrink-0" style={{
                        color: priorityColor(t.priority).match(/text-\w+-\d+/)?.[0] ? "" : "",
                      }}>
                        <Badge color={priorityColor(t.priority)}>{priorityLabel(t.priority)}</Badge>
                      </span>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <span className="text-xs text-muted shrink-0">{t.assignee_name || "未分配"}</span>
                      <button onClick={() => { if (confirm("从模块移除？")) removeTaskFromModule.mutate(t.id); }}
                        className="text-muted hover:text-danger text-xs opacity-0 group-hover:opacity-100 transition-opacity">×</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted mt-2">暂无任务<span className="ml-1 text-xs">（创建或编辑任务时可选择此模块）</span></p>
            )}
          </div>
        );
      })}
      {modules?.length === 0 && (
        <div className="text-center py-12 text-muted text-sm">暂无模块</div>
      )}

      {/* Edit Modal */}
      <Modal open={showEdit} onClose={() => { setShowEdit(false); setEditingModule(null); }} title="编辑模块">
        <div className="space-y-4">
          <Input label="模块名称" value={name} onChange={(e) => setName(e.target.value)} />
          <Input label="描述" value={desc} onChange={(e) => setDesc(e.target.value)} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => { setShowEdit(false); setEditingModule(null); }}>取消</Button>
            <Button onClick={() => updateModule.mutate()} disabled={!name}>{updateModule.isPending ? "保存中..." : "保存"}</Button>
          </div>
        </div>
      </Modal>

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="创建模块">
        <div className="space-y-4">
          <Input label="模块名称" value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：用户认证" />
          <Input label="描述" value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="模块描述" />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
            <Button onClick={() => createModule.mutate()} disabled={!name || createModule.isPending}>
              {createModule.isPending ? "创建中..." : "创建"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
