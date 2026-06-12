"""
activities 模块 — Model 层单元测试

测试覆盖:
  - Activity 创建
  - Activity 排序
"""

import pytest
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace
from apps.projects.models import Project
from apps.tasks.models import Task, TaskStatus
from apps.activities.models import Activity

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestActivityModel:
    """Activity 模型"""

    def test_create_activity(self, admin_user):
        """创建活动日志"""
        ws = Workspace.objects.create(name="Act WS", slug="act-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="Act Proj", identifier="ACT")
        status = TaskStatus.objects.create(project=proj, name="待办", order=1)
        task = Task.objects.create(
            project=proj, title="Act Task", status=status, created_by=admin_user,
        )
        activity = Activity.objects.create(
            task=task, project=proj, actor=admin_user,
            action="created", field="status",
            old_value="", new_value=str(status.id),
        )
        assert activity.action == "created"
        assert activity.project == proj
        assert activity.task == task
        assert activity.actor == admin_user

    def test_ordering_by_created_at_desc(self, admin_user):
        """按 created_at 倒序排列"""
        import time
        ws = Workspace.objects.create(name="AOrd WS", slug="aord-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="AOrd Proj", identifier="AORD")
        status = TaskStatus.objects.create(project=proj, name="待办", order=1)
        task = Task.objects.create(
            project=proj, title="AOrd Task", status=status, created_by=admin_user,
        )
        a1 = Activity.objects.create(task=task, project=proj, actor=admin_user, action="created")
        import time
        time.sleep(0.01)
        a2 = Activity.objects.create(task=task, project=proj, actor=admin_user, action="updated")
        activities = list(Activity.objects.filter(task=task))
        assert activities[0].id == a2.id  # 最新的在前
        assert activities[1].id == a1.id

    def test_activity_without_task(self, admin_user):
        """Activity 可以不关联 task（task 可为 None）"""
        ws = Workspace.objects.create(name="NoT WS", slug="not-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="NoT Proj", identifier="NOT")
        activity = Activity.objects.create(
            project=proj, actor=admin_user,
            action="project_created", field="",
        )
        assert activity.task is None
        assert activity.project == proj
