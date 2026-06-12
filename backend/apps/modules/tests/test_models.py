"""
modules 模块 — Model 层单元测试

测试覆盖:
  - Module 创建与 unique_together (project, name)
  - Module __str__
"""

import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace
from apps.projects.models import Project
from apps.modules.models import Module

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestModuleModel:
    """Module 模型"""

    def test_create_module(self, admin_user):
        """创建模块"""
        ws = Workspace.objects.create(name="Mod WS", slug="mod-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="Mod Proj", identifier="MOD")
        module = Module.objects.create(project=proj, name="Frontend")
        assert module.name == "Frontend"
        assert module.project == proj
        assert str(module) == "MOD/Frontend"

    def test_unique_project_name(self, admin_user):
        """同一项目下 name 唯一"""
        ws = Workspace.objects.create(name="U WS", slug="u-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="U Proj", identifier="UP")
        Module.objects.create(project=proj, name="API")
        with pytest.raises(IntegrityError):
            Module.objects.create(project=proj, name="API")

    def test_same_name_different_project_allowed(self, admin_user):
        """不同项目可使用相同 name"""
        ws = Workspace.objects.create(name="M WS", slug="m-ws", owner=admin_user)
        p1 = Project.objects.create(workspace=ws, name="P1", identifier="P1")
        p2 = Project.objects.create(workspace=ws, name="P2", identifier="P2")
        Module.objects.create(project=p1, name="Shared")
        Module.objects.create(project=p2, name="Shared")  # 不抛异常

    def test_lead_set_null_on_delete(self, admin_user, extra_user):
        """lead 使用 SET_NULL"""
        ws = Workspace.objects.create(name="L WS", slug="l-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="L Proj", identifier="LP")
        module = Module.objects.create(project=proj, name="Backend", lead=extra_user)
        extra_user.delete()
        module.refresh_from_db()
        assert module.lead is None
