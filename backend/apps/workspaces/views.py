# ── 工作空间视图 ─────────────────────────────────────────────────
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.core.permissions import IsWorkspaceAdmin, IsWorkspaceMember
from apps.accounts.models import User
from .models import Workspace, WorkspaceMember
from .serializers import (
    WorkspaceSerializer,
    WorkspaceCreateSerializer,
    WorkspaceMemberSerializer,
    AddMemberSerializer,
    ChangeRoleSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="我的工作空间列表", tags=["工作空间"]),
    create=extend_schema(summary="创建工作空间", tags=["工作空间"]),
    retrieve=extend_schema(summary="工作空间详情", tags=["工作空间"]),
    update=extend_schema(summary="编辑工作空间", tags=["工作空间"]),
    destroy=extend_schema(summary="删除工作空间", tags=["工作空间"]),
    members=extend_schema(summary="成员列表", tags=["工作空间"]),
    add_member=extend_schema(summary="添加成员", tags=["工作空间"]),
    change_role=extend_schema(summary="修改成员角色", tags=["工作空间"]),
    remove_member=extend_schema(summary="移除成员", tags=["工作空间"]),
)
class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.prefetch_related("members")
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return WorkspaceCreateSerializer
        return WorkspaceSerializer

    def create(self, request, *args, **kwargs):
        """创建后用完整 serializer 返回"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 用完整序列化器返回
        ws = serializer.instance
        return Response(WorkspaceSerializer(ws).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        """只返回用户所属的工作空间"""
        return Workspace.objects.filter(
            members__user=self.request.user,
        ).prefetch_related("members").distinct()

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy",
                           "add_member", "change_role", "remove_member"):
            return [IsAuthenticated(), IsWorkspaceAdmin()]
        if self.action in ("members",):
            return [IsAuthenticated(), IsWorkspaceMember()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        ws = serializer.save(owner=self.request.user)
        # 创建者自动成为管理员
        WorkspaceMember.objects.create(
            workspace=ws, user=self.request.user, role=WorkspaceMember.Role.ADMIN,
        )

    # ── 成员管理 ────────────────────────────────────────────────

    @action(methods=["get", "post"], detail=True)
    def members(self, request, pk=None):
        workspace = self.get_object()
        if request.method == "GET":
            qs = WorkspaceMember.objects.filter(
                workspace=workspace,
            ).select_related("user")
            serializer = WorkspaceMemberSerializer(qs, many=True)
            return Response(serializer.data)

        # POST — 添加成员
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]
        user = get_object_or_404(User, email=email)
        member, created = WorkspaceMember.objects.get_or_create(
            workspace=workspace, user=user,
            defaults={"role": role},
        )
        if not created:
            return Response({"detail": "该用户已是成员"}, status=status.HTTP_409_CONFLICT)
        return Response(
            WorkspaceMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )

    @action(methods=["put"], detail=True, url_path="members/(?P<uid>[^/.]+)")
    def change_role(self, request, pk=None, uid=None):
        workspace = self.get_object()
        serializer = ChangeRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = get_object_or_404(WorkspaceMember, workspace=workspace, user_id=uid)
        member.role = serializer.validated_data["role"]
        member.save(update_fields=["role"])
        return Response(WorkspaceMemberSerializer(member).data)

    @action(methods=["delete"], detail=True, url_path="members/(?P<uid>[^/.]+)")
    def remove_member(self, request, pk=None, uid=None):
        workspace = self.get_object()
        if str(workspace.owner_id) == uid:
            return Response(
                {"detail": "不能移除工作空间所有者"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member = get_object_or_404(WorkspaceMember, workspace=workspace, user_id=uid)
        member.delete()
        return Response({"detail": "成员已移除"})
