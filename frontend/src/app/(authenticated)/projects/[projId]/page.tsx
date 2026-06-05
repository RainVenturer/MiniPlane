"use client";
import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Badge from "@/components/ui/Badge";
import Avatar from "@/components/ui/Avatar";
import Spinner from "@/components/ui/Spinner";

import { priorityColor, priorityLabel, formatDate, cn } from "@/lib/utils";
import type { Task, TaskStatus, Project, Iteration, Module } from "@/types";
import { toast } from "sonner";

export default function KanbanPage() {
  const { projId } = useParams<{ projId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [dragOverCol, setDragOverCol] = useState<string | null>(null);

  // Form state
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [priority, setPriority] = useState("none");
  const [assigneeEmail, setAssigneeEmail] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [iterationId, setIterationId] = useState("");
  const [moduleId, setModuleId] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showStatus, setShowStatus] = useState(false);
  const [statusName, setStatusName] = useState("");
  const [statusColor, setStatusColor] = useState("#6366f1");

  const { data: project } = useQuery<Project>({
    queryKey: ["project", projId],
    queryFn: async () => {
      const { data } = await api.get<Project>(`/projects/${projId}/`);
      return data;
    },
  });

  const { data: statuses } = useQuery<TaskStatus[]>({
    queryKey: ["task-statuses", projId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/task-statuses/`);
      return (data as { results?: TaskStatus[] }).results || (Array.isArray(data) ? data as TaskStatus[] : []);
    },
  });

  const { data: iterations } = useQuery<Iteration[]>({
    queryKey: ["iterations", projId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/iterations/`);
      return (data as { results?: Iteration[] }).results || (Array.isArray(data) ? data as Iteration[] : []);
    },
  });

  const { data: modules } = useQuery<Module[]>({
    queryKey: ["modules", projId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/modules/`);
      return (data as { results?: Module[] }).results || (Array.isArray(data) ? data as Module[] : []);
    },
  });

  const { data: tasksData, isLoading } = useQuery<{ results: Task[] }>({
    queryKey: ["tasks", projId, searchQuery],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/tasks/`, {
        params: { view: "kanban", page_size: 100, search: searchQuery || undefined },
      });
      return data as { results: Task[] };
    },
  });

  const tasks = (tasksData as { results: Task[] })?.results || [];

  const createTask = useMutation({
    mutationFn: () => api.post(`/projects/${projId}/tasks/`, {
      title, description: desc, priority,
      iteration: iterationId || null,
      module: moduleId || null,
      due_date: dueDate || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks", projId] });
      setShowCreate(false);
      setTitle(""); setDesc(""); setPriority("none"); setAssigneeEmail("");
      setDueDate(""); setIterationId(""); setModuleId("");
      toast.success("任务创建成功");
    },
    onError: () => toast.error("创建失败"),
  });

  const createStatus = useMutation({
    mutationFn: () => api.post(`/projects/${projId}/task-statuses/`, { name: statusName, color: statusColor }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["task-statuses", projId] });
      setShowStatus(false); setStatusName(""); setStatusColor("#6366f1"); toast.success("状态列已创建");
    },
  });

  const changeStatus = useMutation({
    mutationFn: ({ taskId, statusId }: { taskId: string; statusId: string }) =>
      api.patch(`/tasks/${taskId}/status/`, { status: statusId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks", projId] }),
  });

  const handleDragStart = useCallback((e: React.DragEvent, taskId: string) => {
    e.dataTransfer.setData("taskId", taskId);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, statusId: string) => {
    e.preventDefault();
    setDragOverCol(null);
    const taskId = e.dataTransfer.getData("taskId");
    if (taskId) changeStatus.mutate({ taskId, statusId });
  }, [changeStatus]);

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6 gap-3">
        <input
          type="text"
          placeholder="搜索任务..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="px-3.5 py-2 bg-surface-1 border border-border rounded-xl text-sm text-fg placeholder:text-muted focus:outline-none focus:border-accent w-64"
        />
        <Button onClick={() => setShowStatus(true)} size="sm" variant="ghost">+ 状态列</Button>
        <Button onClick={() => setShowCreate(true)} size="sm">+ 创建任务</Button>
      </div>

      {/* Kanban board */}
      <div className="flex-1 flex gap-4 overflow-x-auto pb-4">
        {statuses?.map((col: TaskStatus) => {
          const colTasks = tasks.filter((t) => t.status === col.id);
          return (
            <div
              key={col.id}
              className="flex-shrink-0 w-72 flex flex-col bg-surface-1 rounded-2xl border border-border"
              onDragOver={(e) => { e.preventDefault(); setDragOverCol(col.id); }}
              onDragLeave={() => setDragOverCol(null)}
              onDrop={(e) => handleDrop(e, col.id)}
            >
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: col.color }} />
                  <span className="text-sm font-semibold">{col.name}</span>
                  <span className="text-xs text-muted bg-surface-2 px-1.5 py-0.5 rounded-full">
                    {colTasks.length}
                  </span>
                </div>
              </div>
              <div className={cn("flex-1 p-2 space-y-2 min-h-[200px] transition-colors", dragOverCol === col.id && "bg-accent/5")}>
                {colTasks.map((task: Task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task.id)}
                    onClick={() => router.push(`/tasks/${task.id}`)}
                    className="p-3 bg-surface-2 border border-border rounded-xl hover:border-accent/30 cursor-pointer transition-all duration-200 group"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className={cn("text-[10px] px-1.5 py-0.5 rounded font-semibold border", priorityColor(task.priority))}>
                        {priorityLabel(task.priority)}
                      </span>
                    </div>
                    <p className="text-sm font-medium leading-snug group-hover:text-accent transition-colors line-clamp-2">
                      {task.title}
                    </p>
                    <div className="flex items-center justify-between mt-2.5 text-xs text-muted">
                      <div className="flex items-center gap-1.5">
                        {task.assignee_name && <Avatar name={task.assignee_name} size="sm" />}
                        <span>{task.assignee_name || "未分配"}</span>
                      </div>
                      {task.due_date && (
                        <span className={cn(
                          "text-[10px]",
                          new Date(task.due_date) < new Date() && "text-danger",
                        )}>
                          {formatDate(task.due_date)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Status Create Modal */}
      <Modal open={showStatus} onClose={() => setShowStatus(false)} title="新建状态列">
        <div className="space-y-4">
          <Input label="状态名称" value={statusName} onChange={(e) => setStatusName(e.target.value)} placeholder="例如：测试中" />
          <div>
            <label className="block text-sm font-medium text-muted mb-1.5">颜色</label>
            <div className="flex items-center gap-3">
              <input type="color" value={statusColor} onChange={(e) => setStatusColor(e.target.value)}
                className="w-10 h-10 rounded-lg border border-border cursor-pointer" />
              <span className="text-sm text-muted font-mono">{statusColor}</span>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setShowStatus(false)}>取消</Button>
            <Button onClick={() => createStatus.mutate()} disabled={!statusName}>创建</Button>
          </div>
        </div>
      </Modal>

      {/* Create Task Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="创建任务">
        <div className="space-y-4">
          <Input label="任务标题" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="输入任务标题" />
          <div>
            <label className="block text-sm font-medium text-muted mb-1.5">描述</label>
            <textarea
              className="w-full px-3.5 py-2.5 bg-surface-1 border border-border rounded-xl text-sm text-fg placeholder:text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 resize-none h-24"
              value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="任务描述（可选）"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-muted mb-1.5">优先级</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-surface-1 border border-border rounded-xl text-sm text-fg focus:outline-none focus:border-accent"
              >
                <option value="none">无</option>
                <option value="urgent">🔴 紧急</option>
                <option value="high">🟠 高</option>
                <option value="medium">🟡 中</option>
                <option value="low">🟢 低</option>
              </select>
            </div>
            <Input label="截止日期" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-muted mb-1.5">迭代</label>
              <select value={iterationId} onChange={(e) => setIterationId(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-surface-1 border border-border rounded-xl text-sm text-fg focus:outline-none focus:border-accent">
                <option value="">无</option>
                {iterations?.filter((i: Iteration) => i.is_active).map((i: Iteration) => (
                  <option key={i.id} value={i.id}>{i.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-muted mb-1.5">模块</label>
              <select value={moduleId} onChange={(e) => setModuleId(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-surface-1 border border-border rounded-xl text-sm text-fg focus:outline-none focus:border-accent">
                <option value="">无</option>
                {modules?.map((m: Module) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>
          </div>
          <Input label="负责人邮箱（可选）" value={assigneeEmail} onChange={(e) => setAssigneeEmail(e.target.value)} placeholder="user@example.com" />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
            <Button onClick={() => createTask.mutate()} disabled={!title || createTask.isPending}>
              {createTask.isPending ? "创建中..." : "创建任务"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
