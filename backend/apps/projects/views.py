# ── 项目视图 ─────────────────────────────────────────────────────
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.core.permissions import IsProjectAdmin
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.accounts.models import User
from .models import Project, ProjectMember
from .serializers import (
    ProjectSerializer,
    ProjectCreateSerializer,
    ProjectMemberSerializer,
    AddProjectMemberSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="项目列表", tags=["项目"]),
    create=extend_schema(summary="创建项目", tags=["项目"]),
    retrieve=extend_schema(summary="项目详情", tags=["项目"]),
    update=extend_schema(summary="编辑项目", tags=["项目"]),
    destroy=extend_schema(summary="删除项目", tags=["项目"]),
    archive=extend_schema(summary="归档项目", tags=["项目"]),
    restore=extend_schema(summary="恢复归档", tags=["项目"]),
    members=extend_schema(summary="项目成员", tags=["项目"]),
    add_member=extend_schema(summary="添加项目成员", tags=["项目"]),
)
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.select_related("lead").prefetch_related("members")
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "archive", "restore",
                           "add_member", "remove_member"):
            return [IsAuthenticated(), IsProjectAdmin()]
        return [IsAuthenticated()]

    lookup_field = "pk"

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    def create(self, request, *args, **kwargs):
        """创建后用完整 serializer 返回"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(ProjectSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(
            workspace__members__user=user,
        ).select_related("lead").prefetch_related("members").distinct()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == "create":
            ctx["workspace_id"] = self.kwargs.get("ws_id")
        return ctx

    def perform_create(self, serializer):
        project = serializer.save()
        # 创建者加入项目
        ProjectMember.objects.create(
            project=project, user=self.request.user, role=ProjectMember.Role.ADMIN,
        )
        # 指定负责人也加入
        if project.lead and project.lead != self.request.user:
            ProjectMember.objects.get_or_create(
                project=project, user=project.lead,
                defaults={"role": ProjectMember.Role.ADMIN},
            )
        # 初始化默认任务状态列
        from apps.tasks.models import TaskStatus
        defaults = [
            ("Backlog", "#6b7280", TaskStatus.Type.BACKLOG, 0),
            ("待办", "#6366f1", TaskStatus.Type.UNSTARTED, 1),
            ("进行中", "#f59e0b", TaskStatus.Type.STARTED, 2),
            ("待评审", "#8b5cf6", TaskStatus.Type.STARTED, 3),
            ("已完成", "#10b981", TaskStatus.Type.COMPLETED, 4),
            ("已取消", "#ef4444", TaskStatus.Type.CANCELLED, 5),
        ]
        for i, (name, color, type_, order) in enumerate(defaults):
            TaskStatus.objects.create(
                project=project, name=name, color=color, type=type_, order=order,
            )

    @action(methods=["post"], detail=True)
    def archive(self, request, pk=None):
        project = self.get_object()
        project.is_archived = True
        project.save(update_fields=["is_archived"])
        return Response({"detail": "项目已归档"})

    @action(methods=["post"], detail=True)
    def restore(self, request, pk=None):
        project = self.get_object()
        project.is_archived = False
        project.save(update_fields=["is_archived"])
        return Response({"detail": "项目已恢复"})

    @action(methods=["get", "post"], detail=True)
    def members(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            qs = ProjectMember.objects.filter(
                project=project,
            ).select_related("user")
            return Response(ProjectMemberSerializer(qs, many=True).data)

        serializer = AddProjectMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, email=serializer.validated_data["email"])
        member, created = ProjectMember.objects.get_or_create(
            project=project, user=user,
            defaults={"role": serializer.validated_data["role"]},
        )
        if not created:
            return Response({"detail": "该用户已是项目成员"}, status=status.HTTP_409_CONFLICT)
        return Response(ProjectMemberSerializer(member).data, status=status.HTTP_201_CREATED)

    @action(methods=["delete"], detail=True, url_path="members/(?P<uid>[^/.]+)")
    def remove_member(self, request, pk=None, uid=None):
        project = self.get_object()
        member = get_object_or_404(ProjectMember, project=project, user_id=uid)
        member.delete()
        return Response({"detail": "成员已移除"})
