# ── 评论视图 ─────────────────────────────────────────────────────
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.tasks.models import Task
from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer


@extend_schema_view(
    list=extend_schema(summary="任务评论列表", tags=["评论"]),
    create=extend_schema(summary="发表评论", tags=["评论"]),
    update=extend_schema(summary="编辑评论", tags=["评论"]),
    destroy=extend_schema(summary="删除评论", tags=["评论"]),
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related("author")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        return Comment.objects.filter(
            task_id=task_id,
        ).select_related("author")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == "create":
            ctx["task_id"] = self.kwargs.get("task_id")
        return ctx

    def perform_create(self, serializer):
        comment = serializer.save()
        task = Task.objects.only("id", "project_id", "assignee_id", "title").get(
            id=self.kwargs.get("task_id"),
        )
        # 通知任务负责人
        if task.assignee and task.assignee != self.request.user:
            from apps.notifications.services import notify_task_commented
            notify_task_commented(task, comment, self.request.user)

    def check_object_permissions(self, request, obj):
        """评论作者可编辑/删除自己的评论"""
        if self.action in ("update", "partial_update", "destroy"):
            if obj.author != request.user:
                self.permission_denied(request, message="只能操作自己的评论")
        return super().check_object_permissions(request, obj)
