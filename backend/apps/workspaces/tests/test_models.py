"""
workspaces 模块 — Model 层单元测试

测试覆盖:
  - Workspace 创建与字段
  - WorkspaceMember unique_together 约束
  - WorkspaceMember Role 枚举
"""

import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace, WorkspaceMember

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestWorkspaceModel:
    """Workspace 模型"""

    def test_create_workspace_success(self, admin_user):
        """创建工作空间 — 基本字段"""
        ws = Workspace.objects.create(
            name="Test Team",
            slug="test-team",
            owner=admin_user,
        )
        assert ws.name == "Test Team"
        assert ws.slug == "test-team"
        assert ws.owner == admin_user
        assert str(ws) == "Test Team"

    def test_slug_is_unique(self, admin_user):
        """slug 唯一约束"""
        Workspace.objects.create(name="A", slug="same-slug", owner=admin_user)
        with pytest.raises(IntegrityError):
            Workspace.objects.create(name="B", slug="same-slug", owner=admin_user)

    def test_owner_protected_on_delete(self, admin_user):
        """owner 使用 PROTECT，删除 owner 会被阻止"""
        ws = Workspace.objects.create(name="Protect Test", slug="protect", owner=admin_user)
        with pytest.raises(Exception):
            admin_user.delete()


class TestWorkspaceMemberModel:
    """WorkspaceMember 模型"""

    def test_create_member(self, admin_user, extra_user):
        """添加工作空间成员"""
        ws = Workspace.objects.create(name="Member Test", slug="member-test", owner=admin_user)
        member = WorkspaceMember.objects.create(
            workspace=ws, user=extra_user, role=WorkspaceMember.Role.MEMBER,
        )
        assert member.workspace == ws
        assert member.user == extra_user
        assert member.role == WorkspaceMember.Role.MEMBER

    def test_unique_together_workspace_user(self, admin_user, extra_user):
        """同一用户不能重复加入同一工作空间"""
        ws = Workspace.objects.create(name="Unique Test", slug="unique-test", owner=admin_user)
        WorkspaceMember.objects.create(workspace=ws, user=extra_user, role="member")
        with pytest.raises(IntegrityError):
            WorkspaceMember.objects.create(workspace=ws, user=extra_user, role="admin")

    def test_role_choices(self, admin_user):
        """Role 字段接受预定义选项"""
        ws = Workspace.objects.create(name="Role Test", slug="role-test", owner=admin_user)
        for role in ["admin", "member", "guest"]:
            u = User.objects.create_user(
                email=f"ws_role_{role}@test.com",
                password="pass1234",
                name=f"Role {role}",
            )
            member = WorkspaceMember.objects.create(
                workspace=ws, user=u, role=role,
            )
            assert member.role == role

    def test_cascade_deletes_members(self, admin_user):
        """删除工作空间时级联删除成员记录"""
        ws = Workspace.objects.create(name="Cascade Test", slug="cascade", owner=admin_user)
        ws_id = ws.id
        u = User.objects.create_user(
            email="cascade_member@test.com", password="pass1234", name="Cascade",
        )
        WorkspaceMember.objects.create(workspace=ws, user=u, role="member")
        member_count = WorkspaceMember.objects.filter(workspace_id=ws_id).count()
        assert member_count == 1
        ws.delete()
        assert WorkspaceMember.objects.filter(workspace_id=ws_id).count() == 0
