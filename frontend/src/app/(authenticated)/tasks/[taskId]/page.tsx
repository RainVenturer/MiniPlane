"use client";
import { useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Badge from "@/components/ui/Badge";
import Avatar from "@/components/ui/Avatar";
import Spinner from "@/components/ui/Spinner";
import Modal from "@/components/ui/Modal";
import { priorityColor, priorityLabel, formatDate, timeAgo } from "@/lib/utils";
import type { Task, Comment, Activity, Attachment, Iteration, Module } from "@/types";
import { toast } from "sonner";

export default function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);

  // Edit states
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [priority, setPriority] = useState("");
  const [assigneeEmail, setAssigneeEmail] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [editIterationId, setEditIterationId] = useState("");
  const [editModuleId, setEditModuleId] = useState("");
  const [showSubtask, setShowSubtask] = useState(false);
  const [subtaskTitle, setSubtaskTitle] = useState("");

  // Comment states
  const [commentText, setCommentText] = useState("");
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null);
  const [editCommentText, setEditCommentText] = useState("");

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["task", taskId] });
    queryClient.invalidateQueries({ queryKey: ["comments", taskId] });
    queryClient.invalidateQueries({ queryKey: ["activities", taskId] });
    queryClient.invalidateQueries({ queryKey: ["attachments", taskId] });
  };

  const { data: task, isLoading } = useQuery<Task>({
    queryKey: ["task", taskId],
    queryFn: async () => (await api.get<Task>(`/tasks/${taskId}/`)).data,
  });

  const { data: comments } = useQuery<Comment[]>({
    queryKey: ["comments", taskId],
    queryFn: async () => {
      const { data } = await api.get(`/tasks/${taskId}/comments/`);
      return (data as { results?: Comment[] }).results || (Array.isArray(data) ? data as Comment[] : []);
    },
  });

  const { data: activities } = useQuery<Activity[]>({
    queryKey: ["activities", taskId],
    queryFn: async () => {
      const { data } = await api.get(`/tasks/${taskId}/activities/`);
      return (data as { results?: Activity[] }).results || (Array.isArray(data) ? data as Activity[] : []);
    },
  });

  const { data: iterations } = useQuery<Iteration[]>({
    queryKey: ["iterations", task?.project],
    queryFn: async () => {
      if (!task?.project) return [];
      const { data } = await api.get(`/projects/${task.project}/iterations/`);
      return (data as { results?: Iteration[] }).results || (Array.isArray(data) ? data as Iteration[] : []);
    },
    enabled: !!task?.project,
  });

  const { data: modules } = useQuery<Module[]>({
    queryKey: ["modules", task?.project],
    queryFn: async () => {
      if (!task?.project) return [];
      const { data } = await api.get(`/projects/${task.project}/modules/`);
      return (data as { results?: Module[] }).results || (Array.isArray(data) ? data as Module[] : []);
    },
    enabled: !!task?.project,
  });

  const { data: attachments } = useQuery<Attachment[]>({
    queryKey: ["attachments", taskId],
    queryFn: async () => {
      const { data } = await api.get(`/tasks/${taskId}/attachments/`);
      return (data as { results?: Attachment[] }).results || (Array.isArray(data) ? data as Attachment[] : []);
    },
  });

  // ── Mutations ──────────────────────────────────────────────
  const updateTask = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.put(`/tasks/${taskId}/`, payload),
    onSuccess: () => { invalidate(); setEditing(false); toast.success("任务已更新"); },
    onError: () => toast.error("更新失败"),
  });

  const deleteTask = useMutation({
    mutationFn: () => api.delete(`/tasks/${taskId}/`),
    onSuccess: () => { toast.success("任务已删除"); router.back(); },
  });

  const changeStatus = useMutation({
    mutationFn: (statusId: string) => api.patch(`/tasks/${taskId}/status/`, { status: statusId }),
    onSuccess: () => invalidate(),
  });

  const addComment = useMutation({
    mutationFn: () => api.post(`/tasks/${taskId}/comments/`, { content: commentText }),
    onSuccess: () => { invalidate(); setCommentText(""); toast.success("评论已发表"); },
  });

  const updateComment = useMutation({
    mutationFn: ({ cid, content }: { cid: string; content: string }) => api.put(`/comments/${cid}/`, { content }),
    onSuccess: () => { invalidate(); setEditingCommentId(null); toast.success("评论已更新"); },
  });

  const deleteComment = useMutation({
    mutationFn: (cid: string) => api.delete(`/comments/${cid}/`),
    onSuccess: () => { invalidate(); toast.success("评论已删除"); },
  });

  const uploadAttachment = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return api.post(`/tasks/${taskId}/attachments/`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: () => { invalidate(); toast.success("文件上传成功"); },
    onError: () => toast.error("上传失败"),
  });

  const createSubtask = useMutation({
    mutationFn: () => api.post(`/tasks/${taskId}/subtasks/`, { title: subtaskTitle }),
    onSuccess: () => { invalidate(); setShowSubtask(false); setSubtaskTitle(""); toast.success("子任务已创建"); },
  });

  const deleteAttachment = useMutation({
    mutationFn: (aid: string) => api.delete(`/attachments/${aid}/`),
    onSuccess: () => { invalidate(); toast.success("附件已删除"); },
  });

  // ── Start editing ──────────────────────────────────────────
  const startEditing = () => {
    if (!task) return;
    setTitle(task.title);
    setDesc(task.description || "");
    setPriority(task.priority);
    setAssigneeEmail(task.assignee_name || "");
    setDueDate(task.due_date || "");
    setEditIterationId(task.iteration || "");
    setEditModuleId(task.module || "");
    setEditing(true);
  };

  const saveEdit = () => {
    updateTask.mutate({
      title,
      description: desc,
      priority,
      iteration: editIterationId || null,
      module: editModuleId || null,
      due_date: dueDate || null,
    });
    // Also handle assignee separately if changed
    if (assigneeEmail && assigneeEmail !== task?.assignee_name) {
      api.put(`/tasks/${taskId}/`, { assignee: assigneeEmail }).catch(() => {});
    }
  };

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>;
  if (!task) return null;

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <button onClick={() => router.back()} className="text-muted hover:text-fg text-sm transition-colors">← 返回</button>
        <div className="flex gap-2">
          {!editing && <Button variant="secondary" size="sm" onClick={startEditing}>编辑</Button>}
          <Button variant="danger" size="sm" onClick={() => { if (confirm("确定删除此任务？")) deleteTask.mutate(); }}>删除</Button>
        </div>
      </div>

      <div className="bg-surface-1 border border-border rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-border">
          {editing ? (
            <div className="space-y-3">
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="任务标题" />
              <textarea
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="任务描述"
                className="w-full px-3.5 py-2.5 bg-surface-2 border border-border rounded-xl text-sm text-fg placeholder:text-muted focus:outline-none focus:border-accent resize-none h-24"
              />
              <div className="grid grid-cols-3 gap-3">
                <select value={priority} onChange={(e) => setPriority(e.target.value)}
                  className="px-3 py-2 bg-surface-2 border border-border rounded-xl text-sm text-fg focus:outline-none focus:border-accent">
                  <option value="none">无优先级</option>
                  <option value="urgent">🔴 紧急</option>
                  <option value="high">🟠 高</option>
                  <option value="medium">🟡 中</option>
                  <option value="low">🟢 低</option>
                </select>
                <select value={editIterationId} onChange={(e) => setEditIterationId(e.target.value)}
                  className="px-3 py-2 bg-surface-2 border border-border rounded-xl text-sm text-fg focus:outline-none focus:border-accent">
                  <option value="">无迭代</option>
                  {iterations?.filter((i: Iteration) => i.is_active).map((i: Iteration) => (
                    <option key={i.id} value={i.id}>{i.name}</option>
                  ))}
                </select>
                <select value={editModuleId} onChange={(e) => setEditModuleId(e.target.value)}
                  className="px-3 py-2 bg-surface-2 border border-border rounded-xl text-sm text-fg focus:outline-none focus:border-accent">
                  <option value="">无模块</option>
                  {modules?.map((m: Module) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
                <Input value={assigneeEmail} onChange={(e) => setAssigneeEmail(e.target.value)} placeholder="负责人邮箱" />
              </div>
              <div className="flex justify-end gap-2 pt-1">
                <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>取消</Button>
                <Button size="sm" onClick={saveEdit} disabled={!title || updateTask.isPending}>
                  {updateTask.isPending ? "保存中..." : "保存"}
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-start justify-between gap-4 mb-4">
                <h1 className="text-xl font-bold leading-snug flex-1">{task.title}</h1>
                <Badge color={priorityColor(task.priority)}>{priorityLabel(task.priority)}</Badge>
              </div>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: task.status_color }} />
                  <select
                    value={task.status}
                    onChange={(e) => changeStatus.mutate(e.target.value)}
                    className="bg-transparent border-none text-sm text-muted cursor-pointer focus:outline-none"
                  >
                    <option value="">切换状态...</option>
                  </select>
                  {task.status_name}
                </div>
                <span>·</span>
                <span>{task.assignee_name || "未分配"}</span>
                <span>·</span>
                <span>创建者 {task.created_by_name}</span>
                <span>·</span>
                <span>{formatDate(task.created_at)}</span>
              </div>
              {task.due_date && <p className="text-sm text-muted mt-2">📅 截止: {formatDate(task.due_date)}</p>}
            </>
          )}
        </div>

        {/* Description (view only) */}
        {task.description && !editing && (
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-sm font-semibold text-muted mb-2">描述</h3>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{task.description}</p>
          </div>
        )}

        {/* Meta */}
        <div className="px-6 py-4 border-b border-border grid grid-cols-3 gap-4 text-sm">
          <div><span className="text-muted">模块</span><p>{task.module_name || "—"}</p></div>
          <div><span className="text-muted">迭代</span><p>{task.iteration_name || "—"}</p></div>
          <div>
            <div className="flex items-center justify-between">
              <span className="text-muted">子任务</span>
              <button onClick={() => setShowSubtask(!showSubtask)} className="text-xs text-accent hover:text-accent-dim">+ 添加</button>
            </div>
            <p>{task.subtask_count} 个</p>
            {showSubtask && (
              <div className="flex gap-2 mt-2">
                <input value={subtaskTitle} onChange={(e) => setSubtaskTitle(e.target.value)}
                  placeholder="子任务标题"
                  className="flex-1 px-2 py-1.5 text-xs bg-surface-2 border border-border rounded-lg focus:outline-none focus:border-accent" />
                <Button size="sm" onClick={() => createSubtask.mutate()} disabled={!subtaskTitle}>创建</Button>
              </div>
            )}
          </div>
        </div>

        {/* Attachments */}
        <div className="px-6 py-4 border-b border-border">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">附件 ({attachments?.length || 0})</h3>
            <Button size="sm" variant="secondary" onClick={() => fileRef.current?.click()}>+ 上传</Button>
            <input ref={fileRef} type="file" className="hidden" onChange={(e) => {
              const f = e.target.files?.[0]; if (f) uploadAttachment.mutate(f);
            }} />
          </div>
          {attachments?.map((a: Attachment) => (
            <div key={a.id} className="flex items-center justify-between py-2 text-sm">
              <a href={a.file_url} target="_blank" className="text-accent hover:underline truncate flex-1">{a.filename}</a>
              <span className="text-xs text-muted mx-3">{(a.size / 1024).toFixed(1)} KB</span>
              <button onClick={() => { if (confirm("删除附件？")) deleteAttachment.mutate(a.id); }}
                className="text-muted hover:text-danger text-sm">×</button>
            </div>
          ))}
          {(!attachments || attachments.length === 0) && (
            <p className="text-sm text-muted">暂无附件</p>
          )}
        </div>

        {/* Comments */}
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-sm font-semibold mb-3">评论 ({comments?.length || 0})</h3>
          <div className="space-y-3 mb-4">
            {comments?.map((c: Comment) => (
              <div key={c.id} className="flex gap-3 group">
                <Avatar name={c.author_name} size="sm" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">{c.author_name}</span>
                    <span className="text-xs text-muted">{timeAgo(c.created_at)}</span>
                    <div className="hidden group-hover:flex items-center gap-1 ml-auto">
                      <button onClick={() => { setEditingCommentId(c.id); setEditCommentText(c.content); }}
                        className="text-xs text-muted hover:text-accent">编辑</button>
                      <button onClick={() => { if (confirm("删除评论？")) deleteComment.mutate(c.id); }}
                        className="text-xs text-muted hover:text-danger">删除</button>
                    </div>
                  </div>
                  {editingCommentId === c.id ? (
                    <div className="flex gap-2">
                      <input value={editCommentText} onChange={(e) => setEditCommentText(e.target.value)}
                        className="flex-1 px-3 py-1.5 bg-surface-2 border border-border rounded-lg text-sm focus:outline-none focus:border-accent" />
                      <Button size="sm" onClick={() => updateComment.mutate({ cid: c.id, content: editCommentText })}
                        disabled={!editCommentText}>保存</Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingCommentId(null)}>取消</Button>
                    </div>
                  ) : (
                    <p className="text-sm leading-relaxed">{c.content}</p>
                  )}
                </div>
              </div>
            ))}
            {(!comments || comments.length === 0) && <p className="text-sm text-muted">暂无评论</p>}
          </div>
          <div className="flex gap-2">
            <input value={commentText} onChange={(e) => setCommentText(e.target.value)}
              placeholder="输入评论..."
              className="flex-1 px-3.5 py-2 bg-surface-2 border border-border rounded-xl text-sm text-fg placeholder:text-muted focus:outline-none focus:border-accent"
              onKeyDown={(e) => { if (e.key === "Enter" && commentText) addComment.mutate(); }} />
            <Button size="sm" onClick={() => addComment.mutate()} disabled={!commentText || addComment.isPending}>
              {addComment.isPending ? "..." : "发送"}
            </Button>
          </div>
        </div>

        {/* Activity log */}
        <div className="px-6 py-4">
          <h3 className="text-sm font-semibold text-muted mb-3">操作日志</h3>
          <div className="space-y-2">
            {activities?.slice(0, 20).map((a: Activity) => (
              <div key={a.id} className="flex items-center gap-3 text-xs text-muted">
                <Avatar name={a.actor_name} size="sm" />
                <span className="font-medium text-fg">{a.actor_name}</span>
                <span>{a.action === "created" ? "创建了任务" : a.action === "status_changed" ? "变更了状态" : a.action}</span>
                <span>{timeAgo(a.created_at)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
