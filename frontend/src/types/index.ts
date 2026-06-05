// ── MiniPlane TypeScript 类型定义 ──────────────────────────────

// ── 用户 ────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  name: string;
  avatar: string;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  user: User;
  access: string;
  refresh: string;
}

export interface RegisterPayload {
  email: string;
  name: string;
  password: string;
}

// ── 工作空间 ──────────────────────────────────────────────────────
export type WorkspaceRole = "admin" | "member" | "guest";

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string;
  owner: string;
  owner_name: string;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  id: string;
  user: string;
  user_name: string;
  user_email: string;
  role: WorkspaceRole;
  joined_at: string;
}

// ── 项目 ─────────────────────────────────────────────────────────
export type ProjectMemberRole = "admin" | "member" | "viewer";

export interface Project {
  id: string;
  workspace: string;
  name: string;
  identifier: string;
  description: string;
  lead: string | null;
  lead_name: string;
  is_archived: boolean;
  member_count: number;
  task_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectMember {
  id: string;
  user: string;
  user_name: string;
  user_email: string;
  role: ProjectMemberRole;
  added_at: string;
}

// ── 任务 ─────────────────────────────────────────────────────────
export type TaskPriority = "urgent" | "high" | "medium" | "low" | "none";
export type TaskStatusType = "backlog" | "unstarted" | "started" | "completed" | "cancelled";

export interface TaskStatus {
  id: string;
  project: string;
  name: string;
  color: string;
  order: number;
  type: TaskStatusType;
}

export interface Task {
  id: string;
  project: string;
  parent: string | null;
  title: string;
  description: string;
  priority: TaskPriority;
  priority_display: string;
  status: string;
  status_name: string;
  status_color: string;
  status_type: TaskStatusType;
  assignee: string | null;
  assignee_name: string;
  module: string | null;
  module_name: string;
  iteration: string | null;
  iteration_name: string;
  due_date: string | null;
  start_date: string | null;
  order: number;
  created_by: string;
  created_by_name: string;
  subtask_count: number;
  comment_count: number;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  results: Task[];
  page: number;
  page_size: number;
  count: number;
  total_pages: number;
}

// ── 评论 ─────────────────────────────────────────────────────────
export interface Comment {
  id: string;
  task: string;
  author: string;
  author_name: string;
  author_avatar: string;
  content: string;
  created_at: string;
  updated_at: string;
}

// ── 附件 ─────────────────────────────────────────────────────────
export interface Attachment {
  id: string;
  task: string;
  file: string;
  filename: string;
  size: number;
  mime_type: string;
  uploader: string;
  uploader_name: string;
  file_url: string;
  created_at: string;
}

// ── 迭代 ─────────────────────────────────────────────────────────
export interface Iteration {
  id: string;
  project: string;
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  task_count: number;
  completed_count: number;
  created_at: string;
  updated_at: string;
}

// ── 模块 ─────────────────────────────────────────────────────────
export interface Module {
  id: string;
  project: string;
  name: string;
  description: string;
  lead: string | null;
  lead_name: string;
  task_count: number;
  created_at: string;
  updated_at: string;
}

// ── 通知 ─────────────────────────────────────────────────────────
export type NotificationType =
  | "task.assigned"
  | "task.commented"
  | "task.status_changed"
  | "member.added"
  | "mention";

export interface Notification {
  id: string;
  type: NotificationType;
  type_display: string;
  message: string;
  actor: string;
  actor_name: string;
  reference_type: string;
  reference_id: string | null;
  is_read: boolean;
  created_at: string;
}

// ── 操作日志 ──────────────────────────────────────────────────────
export interface Activity {
  id: string;
  task: string | null;
  task_title: string;
  project: string;
  actor: string;
  actor_name: string;
  action: string;
  field: string;
  old_value: string;
  new_value: string;
  created_at: string;
}

// ── 统计 ──────────────────────────────────────────────────────────
export interface ProjectStats {
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
  status_distribution: { status__name: string; status__color: string; status__type: string; count: number }[];
  priority_distribution: { priority: string; count: number }[];
  assignee_distribution: { assignee__name: string; assignee__id: string; count: number }[];
}

export interface IterationStats {
  iteration: { id: string; name: string; start_date: string; end_date: string };
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
  by_status: { status__name: string; status__color: string; count: number }[];
  by_assignee: { assignee__name: string; assignee__id: string; count: number }[];
}

// ── API 响应 ──────────────────────────────────────────────────────
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
  };
}

export interface ApiError {
  success: false;
  message: string;
  errors: Record<string, string[]>;
}
