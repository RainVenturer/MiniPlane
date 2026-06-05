# ── 迭代视图 ─────────────────────────────────────────────────────
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.tasks.models import Task
from .models import Iteration
from .serializers import (
    IterationSerializer,
    IterationCreateSerializer,
    AddTasksToIterationSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="迭代列表", tags=["迭代"]),
    create=extend_schema(summary="创建迭代", tags=["迭代"]),
    retrieve=extend_schema(summary="迭代详情", tags=["迭代"]),
    update=extend_schema(summary="编辑迭代", tags=["迭代"]),
    destroy=extend_schema(summary="删除迭代", tags=["迭代"]),
    add_tasks=extend_schema(summary="向迭代添加任务", tags=["迭代"]),
)
class IterationViewSet(viewsets.ModelViewSet):
    queryset = Iteration.objects.all()
    serializer_class = IterationSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return IterationCreateSerializer
        return IterationSerializer

    def get_queryset(self):
        project_id = self.kwargs.get("proj_id")
        return Iteration.objects.filter(project_id=project_id)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == "create":
            ctx["project_id"] = self.kwargs.get("proj_id")
        return ctx

    @action(methods=["post"], detail=True)
    def add_tasks(self, request, pk=None):
        iteration = self.get_object()
        serializer = AddTasksToIterationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task_ids = serializer.validated_data["task_ids"]
        updated = Task.objects.filter(
            id__in=task_ids, project_id=iteration.project_id,
        ).update(iteration=iteration)
        return Response({"detail": f"已将 {updated} 个任务加入迭代"})
