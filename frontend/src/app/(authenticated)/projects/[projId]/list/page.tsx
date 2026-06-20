"use client";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import Badge from "@/components/ui/Badge";
import Avatar from "@/components/ui/Avatar";
import Spinner from "@/components/ui/Spinner";


import { priorityColor, priorityLabel, formatDate } from "@/lib/utils";
import type { Task } from "@/types";

export default function ListViewPage() {
  const { projId } = useParams<{ projId: string }>();
  const router = useRouter();

  const { data: tasksData, isLoading } = useQuery<Task[]>({
    queryKey: ["tasks", projId, "list"],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projId}/tasks/`, {
        params: { view: "list", page_size: 100 },
      });
      return (data as { results?: Task[] }).results || (Array.isArray(data) ? (data as Task[]) : []);
    },
  });

  const tasks = tasksData || [];

  if (isLoading) return <div className="flex justify-center py-20"><Spinner /></div>;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">列表视图 — {tasks.length} 个任务</h2>
      <div className="bg-surface-1 border border-border rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-muted">
              <th className="text-left px-4 py-3 font-medium">任务</th>
              <th className="text-left px-4 py-3 font-medium">状态</th>
              <th className="text-left px-4 py-3 font-medium">优先级</th>
              <th className="text-left px-4 py-3 font-medium">负责人</th>
              <th className="text-left px-4 py-3 font-medium">截止日期</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task: Task) => (
              <tr
                key={task.id}
                onClick={() => router.push(`/tasks/${task.id}`)}
                className="border-b border-border last:border-0 hover:bg-surface-2 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3 font-medium">{task.title}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: task.status_color }} />
                    <span className="text-xs">{task.status_name}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <Badge color={priorityColor(task.priority)}>{priorityLabel(task.priority)}</Badge>
                </td>
                <td className="px-4 py-3">
                  {task.assignee_name ? (
                    <div className="flex items-center gap-2"><Avatar name={task.assignee_name} size="sm" />{task.assignee_name}</div>
                  ) : <span className="text-muted">—</span>}
                </td>
                <td className="px-4 py-3 text-muted">{formatDate(task.due_date)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {tasks.length === 0 && (
          <div className="text-center py-12 text-muted text-sm">暂无任务</div>
        )}
      </div>
    </div>
  );
}
