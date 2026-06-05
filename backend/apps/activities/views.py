# ── 操作日志视图 ─────────────────────────────────────────────────
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Activity
from .serializers import ActivitySerializer


@extend_schema_view(
    task_activities=extend_schema(summary="任务操作日志", tags=["操作日志"]),
    project_activities=extend_schema(summary="项目操作日志", tags=["操作日志"]),
)
class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        project_id = self.kwargs.get("project_id")
        qs = Activity.objects.select_related("actor", "task", "project")
        if task_id:
            return qs.filter(task_id=task_id)
        if project_id:
            return qs.filter(project_id=project_id)
        # 只返回用户参与项目的日志
        return qs.filter(
            project__members__user=self.request.user,
        ).distinct()

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
