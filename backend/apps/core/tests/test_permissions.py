"""
core 模块 — Permission 层单元测试

测试覆盖:
  - IsWorkspaceAdmin: has_object_permission (admin/member)
  - IsWorkspaceMember: has_permission (有/无 workspace_id)
  - IsProjectAdmin: has_object_permission (Project/Task 对象)
  - IsProjectMember: has_permission
  - IsTaskAssigneeOrProjectAdmin: has_object_permission (SAFE/assignee/admin)
"""

import pytest
from unittest.mock import Mock, patch
from apps.core.permissions import (
    IsWorkspaceAdmin, IsWorkspaceMember,
    IsProjectAdmin, IsProjectMember,
    IsTaskAssigneeOrProjectAdmin,
)
from apps.workspaces.models import WorkspaceMember
from apps.projects.models import ProjectMember


class TestIsWorkspaceAdmin:
    """IsWorkspaceAdmin 权限"""

    def test_admin_has_permission(self):
        with patch.object(WorkspaceMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            request = Mock(user=Mock(id=1))
            obj = Mock()
            perm = IsWorkspaceAdmin()
            assert perm.has_object_permission(request, Mock(), obj) is True
            mock_filter.assert_called_once_with(
                workspace=obj, user=request.user,
                role=WorkspaceMember.Role.ADMIN,
            )

    def test_non_admin_lacks_permission(self):
        with patch.object(WorkspaceMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = False
            perm = IsWorkspaceAdmin()
            assert perm.has_object_permission(Mock(), Mock(), Mock()) is False


class TestIsWorkspaceMember:
    """IsWorkspaceMember 权限"""

    def test_member_has_permission(self):
        with patch.object(WorkspaceMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            request = Mock(user=Mock(id=1))
            view = Mock(kwargs={"workspace_id": "ws-uuid"})
            perm = IsWorkspaceMember()
            assert perm.has_permission(request, view) is True

    def test_non_member_lacks_permission(self):
        with patch.object(WorkspaceMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = False
            request = Mock(user=Mock(id=1))
            view = Mock(kwargs={"ws_id": "ws-uuid"})
            perm = IsWorkspaceMember()
            assert perm.has_permission(request, view) is False

    def test_no_workspace_id_returns_true(self):
        """无 workspace_id 时不做校验（由 view 层处理）"""
        request = Mock(user=Mock(id=1))
        view = Mock(kwargs={})
        perm = IsWorkspaceMember()
        assert perm.has_permission(request, view) is True

    def test_uses_ws_id_fallback(self):
        """优先 workspace_id，其次 ws_id"""
        with patch.object(WorkspaceMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            request = Mock(user=Mock(id=1))
            view = Mock(kwargs={"ws_id": "ws-uuid"})
            perm = IsWorkspaceMember()
            assert perm.has_permission(request, view) is True
            mock_filter.assert_called_once_with(
                workspace_id="ws-uuid", user=request.user,
            )


class TestIsProjectAdmin:
    """IsProjectAdmin 权限"""

    def test_admin_on_project_obj(self):
        with patch.object(ProjectMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            request = Mock(user=Mock(id=1))
            obj = Mock(identifier="PROJ-1")
            perm = IsProjectAdmin()
            assert perm.has_object_permission(request, Mock(), obj) is True
            mock_filter.assert_called_once_with(
                project=obj, user=request.user,
                role__in=[ProjectMember.Role.ADMIN],
            )

    def test_admin_on_task_obj_resolves_project(self):
        """Task 对象 — 通过 .project 属性查找"""
        with patch.object(ProjectMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            request = Mock(user=Mock(id=1))
            task_obj = Mock(project=Mock(identifier="PROJ-1"))
            # 确保 task_obj 没有 identifier 属性来触发 else 分支
            del task_obj.identifier
            perm = IsProjectAdmin()
            assert perm.has_object_permission(request, Mock(), task_obj) is True
            # 应查询 task_obj.project
            assert mock_filter.call_args[1]["project"] == task_obj.project

    def test_non_admin_lacks_permission(self):
        with patch.object(ProjectMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = False
            perm = IsProjectAdmin()
            obj = Mock(identifier="PROJ")
            assert perm.has_object_permission(Mock(), Mock(), obj) is False


class TestIsProjectMember:
    """IsProjectMember 权限"""

    def test_member_has_permission(self):
        with patch.object(ProjectMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            request = Mock(user=Mock(id=1))
            view = Mock(kwargs={"project_id": "proj-uuid"})
            perm = IsProjectMember()
            assert perm.has_permission(request, view) is True

    def test_non_member_lacks_permission(self):
        with patch.object(ProjectMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = False
            request = Mock(user=Mock(id=1))
            view = Mock(kwargs={"proj_id": "proj-uuid"})
            perm = IsProjectMember()
            assert perm.has_permission(request, view) is False

    def test_no_project_id_returns_true(self):
        request = Mock(user=Mock(id=1))
        view = Mock(kwargs={})
        perm = IsProjectMember()
        assert perm.has_permission(request, view) is True


class TestIsTaskAssigneeOrProjectAdmin:
    """IsTaskAssigneeOrProjectAdmin 权限"""

    def test_safe_methods_allowed(self):
        """GET/HEAD/OPTIONS 等 SAFE_METHODS 始终通过"""
        perm = IsTaskAssigneeOrProjectAdmin()
        request = Mock(method="GET")
        obj = Mock()
        assert perm.has_object_permission(request, Mock(), obj) is True

    def test_assignee_can_write(self):
        """任务的 assignee 可编辑"""
        perm = IsTaskAssigneeOrProjectAdmin()
        request = Mock(method="PUT", user=Mock(id="user1"))
        obj = Mock(assignee=request.user)
        assert perm.has_object_permission(request, Mock(), obj) is True

    def test_project_admin_can_write(self):
        """项目管理员可编辑"""
        with patch.object(ProjectMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            request = Mock(method="PUT", user=Mock(id="admin1"))
            obj = Mock(assignee=Mock(id="user2"), project=Mock())
            perm = IsTaskAssigneeOrProjectAdmin()
            assert perm.has_object_permission(request, Mock(), obj) is True

    def test_other_user_lacks_permission(self):
        """非 assignee 且非 admin — 拒绝"""
        with patch.object(ProjectMember.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = False
            request = Mock(method="DELETE", user=Mock(id="user3"))
            obj = Mock(assignee=Mock(id="user2"), project=Mock())
            perm = IsTaskAssigneeOrProjectAdmin()
            assert perm.has_object_permission(request, Mock(), obj) is False
