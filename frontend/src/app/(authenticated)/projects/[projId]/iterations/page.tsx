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
import { priorityColor, priorityLabel, formatDate, cn } from "@/lib/utils";
import type { Iteration, Task } from "@/types";
import { toast } from "sonner";

export default function IterationsPage() {
  const { projId } = useParams<{ projId: string }>();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [selectedIterId, setSelectedIterId] = useState<string | null>(null);
  const [showEdit, setShowEdit] = useState(false);
  const [editingIter, setEditingIter] = useState<Iteration | null>(null);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["iterations", projId] });
    queryClient.invalidateQueries({ queryKey: ["tasks", projId] });
    queryClient.invalidateQueries({ queryKey: ["tasks", projId, "list"] });
  };

  const { data: iterations, isLoading } = useQuery<Iteration[]>({
    queryKey: ["iterations", projId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/iterations/`);
      return (data as { results?: Iteration[] }).results || (Array.isArray(data) ? data as Iteration[] : []);
    },
  });

  const { data: allTasks } = useQuery<Task[]>({
    queryKey: ["tasks", projId, "list"],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/tasks/`, { params: { page_size: 200 } });
      return (data as { results?: Task[] }).results || [];
    },
  });

  const updateIteration = useMutation({
    mutationFn: () => api.put(`/iterations/${editingIter!.id}/`, {
      name, description: desc, start_date: startDate, end_date: endDate,
    }),
    onSuccess: () => { invalidate(); setShowEdit(false); setEditingIter(null); toast.success("迭代已更新"); },
    onError: () => toast.error("更新失败"),
  });

  const deleteIteration = useMutation({
    mutationFn: (id: string) => api.delete(`/iterations/${id}/`),
    onSuccess: () => { invalidate(); toast.success("迭代已删除"); },
  });

  const createIteration = useMutation({
    mutationFn: () => api.post(`/projects/${projId}/iterations/`, { name, description: desc, start_date: startDate, end_date: endDate }),
    onSuccess: () => { invalidate(); setShowCreate(false); setName(""); setDesc(""); setStartDate(""); setEndDate(""); toast.success("迭代创建成功"); },
    onError: () => toast.error("创建失败"),
  });

  const addTasksMutation = useMutation({
    mutationFn: ({ iterId, taskIds }: { iterId: string; taskIds: string[] }) =>
      api.post(`/iterations/${iterId}/tasks/`, { task_ids: taskIds }),
    onSuccess: () => { invalidate(); setSelectedIterId(null); toast.success("任务已加入迭代"); },
    onError: () => toast.error("操作失败"),
  });

  const removeTaskFromIteration = useMutation({
    mutationFn: (taskId: string) => api.put(`/tasks/${taskId}/`, { iteration: null }),
    onSuccess: () => invalidate(),
  });

  const tasks = allTasks || [];

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">迭代管理</h2>
        <Button onClick={() => setShowCreate(true)} size="sm">+ 创建迭代</Button>
      </div>

      {iterations?.map((iter: Iteration) => {
        const iterTasks = tasks.filter((t: Task) => t.iteration === iter.id);
        const pct = iterTasks.length > 0
          ? Math.round((iterTasks.filter((t: Task) => t.status_type === "completed").length / iterTasks.length) * 100)
          : 0;

        return (
          <div key={iter.id} className="mb-4 p-4 bg-surface-1 border border-border rounded-2xl">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{iter.name}</h3>
                  <Badge color={iter.is_active ? "bg-success/10 text-success border-success/20" : "bg-surface-2 text-muted border-border"}>
                    {iter.is_active ? "进行中" : "已结束"}
                  </Badge>
                </div>
                <p className="text-xs text-muted mt-0.5">{formatDate(iter.start_date)} — {formatDate(iter.end_date)}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="ghost" onClick={() => {
                  setEditingIter(iter); setName(iter.name); setDesc(iter.description || "");
                  setStartDate(iter.start_date); setEndDate(iter.end_date); setShowEdit(true);
                }}>编辑</Button>
                <Button size="sm" variant="ghost" onClick={() => { if (confirm("删除迭代？")) deleteIteration.mutate(iter.id); }}>删除</Button>
                <Button size="sm" variant="secondary" onClick={() => setSelectedIterId(iter.id)}>+ 添加任务</Button>
              </div>
            </div>

            {/* Progress bar */}
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden">
                <div className="h-full bg-accent rounded-full transition-all" style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-muted font-mono">{pct}%</span>
            </div>
            <p className="text-xs text-muted mb-3">{iter.completed_count}/{iter.task_count} 任务完成</p>

            {/* Tasks in this iteration */}
            {iterTasks.length > 0 ? (
              <div className="space-y-1">
                {iterTasks.map((t: Task) => (
                  <div key={t.id} className="flex items-center justify-between px-3 py-2 bg-surface-2 rounded-xl text-sm group">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: t.status_color }} />
                      <span className="truncate">{t.title}</span>
                      <span className={cn("text-[10px] px-1 py-0.5 rounded font-semibold border shrink-0", priorityColor(t.priority))}>{priorityLabel(t.priority)}</span>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <span className="text-xs text-muted shrink-0">{t.assignee_name || "未分配"}</span>
                      <button onClick={() => { if (confirm("从迭代移除？")) removeTaskFromIteration.mutate(t.id); }}
                        className="text-muted hover:text-danger text-xs opacity-0 group-hover:opacity-100 transition-opacity">×</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted">暂无任务</p>
            )}
          </div>
        );
      })}
      {iterations?.length === 0 && (
        <div className="text-center py-12 text-muted text-sm">暂无迭代计划</div>
      )}

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="创建迭代">
        <div className="space-y-4">
          <Input label="迭代名称" value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：Sprint 1" />
          <Input label="描述" value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="迭代目标" />
          <div className="grid grid-cols-2 gap-4">
            <Input label="开始日期" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            <Input label="结束日期" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
            <Button onClick={() => createIteration.mutate()} disabled={!name || !startDate || !endDate || createIteration.isPending}>
              {createIteration.isPending ? "创建中..." : "创建"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal open={showEdit} onClose={() => { setShowEdit(false); setEditingIter(null); }} title="编辑迭代">
        <div className="space-y-4">
          <Input label="迭代名称" value={name} onChange={(e) => setName(e.target.value)} />
          <Input label="描述" value={desc} onChange={(e) => setDesc(e.target.value)} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="开始日期" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            <Input label="结束日期" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => { setShowEdit(false); setEditingIter(null); }}>取消</Button>
            <Button onClick={() => updateIteration.mutate()} disabled={!name || !startDate || !endDate}>
              {updateIteration.isPending ? "保存中..." : "保存"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Add Tasks Modal */}
      <Modal open={!!selectedIterId} onClose={() => setSelectedIterId(null)} title="添加任务到迭代">
        <div className="space-y-2 max-h-96 overflow-auto">
          {tasks.filter((t: Task) => !t.iteration || t.iteration !== selectedIterId).slice(0, 50).map((t: Task) => (
            <div key={t.id} className="flex items-center justify-between px-3 py-2 bg-surface-2 rounded-xl text-sm">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: t.status_color }} />
                <span className="truncate">{t.title}</span>
              </div>
              <Button size="sm" onClick={() => addTasksMutation.mutate({ iterId: selectedIterId!, taskIds: [t.id] })}>
                加入
              </Button>
            </div>
          ))}
          {tasks.filter((t: Task) => !t.iteration || t.iteration !== selectedIterId).length === 0 && (
            <p className="text-sm text-muted text-center py-8">所有任务已加入迭代</p>
          )}
        </div>
      </Modal>
    </div>
  );
}
