# ── 任务视图 ─────────────────────────────────────────────────────
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.core.permissions import IsProjectMember, IsTaskAssigneeOrProjectAdmin
from apps.projects.models import Project
from .models import Task, TaskStatus
from .serializers import (
    TaskSerializer,
    TaskListSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskStatusSerializer,
    TaskStatusChangeSerializer,
)
from .filters import TaskFilter


@extend_schema_view(
    list=extend_schema(summary="任务列表", tags=["任务"]),
    create=extend_schema(summary="创建任务", tags=["任务"]),
    retrieve=extend_schema(summary="任务详情", tags=["任务"]),
    update=extend_schema(summary="编辑任务", tags=["任务"]),
    partial_update=extend_schema(summary="部分更新任务", tags=["任务"]),
    destroy=extend_schema(summary="删除任务", tags=["任务"]),
    change_status=extend_schema(summary="更新任务状态", tags=["任务"]),
    subtasks=extend_schema(summary="创建子任务", tags=["任务"]),
    statuses=extend_schema(summary="任务状态列", tags=["任务"]),
)
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related(
        "status", "assignee", "module", "iteration", "created_by",
    ).prefetch_related("subtasks", "comments")
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsProjectMember, IsTaskAssigneeOrProjectAdmin]
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "due_date", "priority", "order"]
    ordering = ["order", "-created_at"]

    def get_permissions(self):
        # 状态变更（拖拽）：任何项目成员均可操作，不限于负责人/管理员
        if self.action == "change_status":
            return [IsAuthenticated(), IsProjectMember()]
        # 状态列管理（GET/POST）：与 modules、iterations 等子资源一致
        if self.action == "statuses":
            if self.request.method == "GET":
                return [IsAuthenticated()]
            return [IsAuthenticated(), IsProjectMember()]
        return [IsAuthenticated(), IsProjectMember(), IsTaskAssigneeOrProjectAdmin()]

    def get_serializer_class(self):
        if self.action == "list":
            return TaskListSerializer
        if self.action == "create":
            return TaskCreateSerializer
        if self.action in ("update", "partial_update"):
            return TaskUpdateSerializer
        if self.action == "statuses":
            return TaskStatusSerializer
        return TaskSerializer

    def create(self, request, *args, **kwargs):
        """创建后用完整 serializer 返回"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(TaskSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        project_id = self.kwargs.get("proj_id")
        qs = Task.objects.all()
        if project_id:
            qs = qs.filter(project_id=project_id)
        # 看板/列表视图默认只看顶层任务
        if self.action == "list" and project_id:
            view_type = self.request.query_params.get("view", "list")
            if view_type in ("kanban", "list") and "parent__isnull" not in self.request.query_params:
                qs = qs.filter(parent__isnull=True)
        return qs.select_related(
            "status", "assignee", "created_by",
        ).prefetch_related("subtasks")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == "create":
            ctx["project_id"] = self.kwargs.get("proj_id")
        return ctx

    def perform_create(self, serializer):
        task = serializer.save()
        # 记录创建日志
        from apps.activities.models import Activity
        Activity.objects.create(
            task=task, project=task.project,
            actor=self.request.user, action="created",
        )
        # 通知负责人
        if task.assignee and task.assignee != self.request.user:
            from apps.notifications.services import notify_task_assigned
            notify_task_assigned(task, self.request.user)

    # ── 状态变更 (看板拖拽) ──────────────────────────────────
    @action(methods=["patch"], detail=True, url_path="status")
    def change_status(self, request, pk=None):
        task = self.get_object()
        serializer = TaskStatusChangeSerializer(
            data=request.data, context={"task": task, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task).data)

    # ── 子任务 ────────────────────────────────────────────────
    @action(methods=["post"], detail=True)
    def subtasks(self, request, pk=None):
        parent = self.get_object()
        serializer = TaskCreateSerializer(
            data=request.data,
            context={"project_id": str(parent.project_id), "request": request},
        )
        serializer.is_valid(raise_exception=True)
        task = serializer.save(parent=parent)
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    # ── 状态列管理 ────────────────────────────────────────────
    @action(methods=["get", "post"], detail=False, url_path="task-statuses")
    def statuses(self, request, proj_id=None):
        project = get_object_or_404(Project, id=proj_id)
        if request.method == "GET":
            qs = TaskStatus.objects.filter(project=project)
            return Response(TaskStatusSerializer(qs, many=True).data)

        serializer = TaskStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(project=project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
