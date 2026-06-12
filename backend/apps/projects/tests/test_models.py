"""
projects 模块 — Model 层单元测试

测试覆盖:
  - Project 创建与 unique_together (workspace, identifier)
  - ProjectMember unique_together
  - Project is_archived 默认值
"""

import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace
from apps.projects.models import Project, ProjectMember

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestProjectModel:
    """Project 模型"""

    def test_create_project_success(self, admin_user):
        """创建项目 — 基本字段"""
        ws = Workspace.objects.create(name="Proj WS", slug="proj-ws", owner=admin_user)
        proj = Project.objects.create(
            workspace=ws, name="My Project", identifier="PROJ",
        )
        assert proj.name == "My Project"
        assert proj.identifier == "PROJ"
        assert proj.workspace == ws
        assert proj.is_archived is False
        assert str(proj) == "Proj WS/My Project"

    def test_unique_workspace_identifier(self, admin_user):
        """同一 workspace 下 identifier 唯一"""
        ws = Workspace.objects.create(name="Unique WS", slug="unique-ws", owner=admin_user)
        Project.objects.create(workspace=ws, name="A", identifier="SAME")
        with pytest.raises(IntegrityError):
            Project.objects.create(workspace=ws, name="B", identifier="SAME")

    def test_same_identifier_different_workspace_allowed(self, admin_user):
        """不同 workspace 下可重复使用相同 identifier"""
        ws1 = Workspace.objects.create(name="WS 1", slug="ws-1", owner=admin_user)
        ws2 = Workspace.objects.create(name="WS 2", slug="ws-2", owner=admin_user)
        # 不应抛出异常
        Project.objects.create(workspace=ws1, name="P1", identifier="DUP")
        Project.objects.create(workspace=ws2, name="P2", identifier="DUP")

    def test_is_archived_defaults_to_false(self, admin_user):
        """is_archived 默认为 False"""
        ws = Workspace.objects.create(name="Arch Test", slug="arch-test", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="P", identifier="ARC")
        assert proj.is_archived is False

    def test_lead_set_null_on_user_delete(self, admin_user, extra_user):
        """lead 使用 SET_NULL, 删除用户时 lead 置空"""
        ws = Workspace.objects.create(name="Lead WS", slug="lead-ws", owner=admin_user)
        proj = Project.objects.create(
            workspace=ws, name="Lead Proj", identifier="LEAD", lead=extra_user,
        )
        extra_user.delete()
        proj.refresh_from_db()
        assert proj.lead is None


class TestProjectMemberModel:
    """ProjectMember 模型"""

    def test_create_project_member(self, admin_user, extra_user):
        """添加项目成员"""
        ws = Workspace.objects.create(name="PM WS", slug="pm-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="PM Proj", identifier="PM")
        member = ProjectMember.objects.create(
            project=proj, user=extra_user, role=ProjectMember.Role.MEMBER,
        )
        assert member.project == proj
        assert member.role == ProjectMember.Role.MEMBER

    def test_unique_project_user(self, admin_user, extra_user):
        """同一用户不能重复加项目"""
        ws = Workspace.objects.create(name="PU WS", slug="pu-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="PU Proj", identifier="PU")
        ProjectMember.objects.create(project=proj, user=extra_user, role="member")
        with pytest.raises(IntegrityError):
            ProjectMember.objects.create(project=proj, user=extra_user, role="admin")

    def test_role_choices(self, admin_user, extra_user):
        """Role 接受 admin/member/viewer"""
        ws = Workspace.objects.create(name="PR WS", slug="pr-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="PR Proj", identifier="PR")
        for role in ["admin", "member", "viewer"]:
            # 每个角色单独创建
            u = User.objects.create_user(
                email=f"{role}_proj@test.com",
                password="pass1234",
                name=f"Role {role}",
            )
            member = ProjectMember.objects.create(project=proj, user=u, role=role)
            assert member.role == role
