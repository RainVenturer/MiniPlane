# ── RBAC 权限类 ──────────────────────────────────────────────────
from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.workspaces.models import WorkspaceMember
from apps.projects.models import ProjectMember


class IsWorkspaceAdmin(BasePermission):
    """工作空间管理员"""
    def has_object_permission(self, request, view, obj):
        return WorkspaceMember.objects.filter(
            workspace=obj, user=request.user, role=WorkspaceMember.Role.ADMIN,
        ).exists()


class IsWorkspaceMember(BasePermission):
    """工作空间成员（含 admin）"""
    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id") or view.kwargs.get("ws_id")
        if not workspace_id:
            return True  # 由 view 级校验
        return WorkspaceMember.objects.filter(
            workspace_id=workspace_id, user=request.user,
        ).exists()


class IsProjectAdmin(BasePermission):
    """项目负责人 / 管理员"""
    def has_object_permission(self, request, view, obj):
        # obj 可能是 Project 或 Task（含 project 属性）
        project = obj if hasattr(obj, "identifier") else obj.project
        return ProjectMember.objects.filter(
            project=project, user=request.user, role__in=[
                ProjectMember.Role.ADMIN,
            ],
        ).exists()


class IsProjectMember(BasePermission):
    """项目成员"""
    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_id") or view.kwargs.get("proj_id")
        if not project_id:
            return True
        return ProjectMember.objects.filter(
            project_id=project_id, user=request.user,
        ).exists()


class IsTaskAssigneeOrProjectAdmin(BasePermission):
    """任务负责人或项目管理员可编辑"""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if obj.assignee == request.user:
            return True
        return ProjectMember.objects.filter(
            project=obj.project, user=request.user, role__in=[
                ProjectMember.Role.ADMIN,
            ],
        ).exists()
