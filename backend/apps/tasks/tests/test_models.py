"""
tasks 模块 — Model 层单元测试

测试覆盖:
  - TaskStatus unique_together (project, name)
  - TaskStatus Type 枚举
  - Task FK 关系、Priority 枚举
  - Task subtask 自引用
"""

import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace
from apps.projects.models import Project
from apps.tasks.models import Task, TaskStatus

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def project(admin_user):
    ws = Workspace.objects.create(name="Task WS", slug="task-ws", owner=admin_user)
    return Project.objects.create(workspace=ws, name="Task Proj", identifier="TASK")


@pytest.fixture
def status_todo(project):
    return TaskStatus.objects.create(
        project=project, name="待办", type=TaskStatus.Type.UNSTARTED, order=1,
    )


class TestTaskStatusModel:
    """TaskStatus 模型"""

    def test_create_status(self, project):
        """创建状态列"""
        status = TaskStatus.objects.create(
            project=project, name="Backlog", type="backlog", order=0,
        )
        assert status.name == "Backlog"
        assert status.type == TaskStatus.Type.BACKLOG
        assert status.order == 0
        assert status.color == "#6366f1"  # 默认颜色

    def test_unique_project_name(self, project):
        """同一项目下 name 唯一"""
        TaskStatus.objects.create(project=project, name="进行中", order=2)
        with pytest.raises(IntegrityError):
            TaskStatus.objects.create(project=project, name="进行中", order=3)

    def test_same_name_different_project_allowed(self, admin_user):
        """不同项目可使用相同 name"""
        ws = Workspace.objects.create(name="S1", slug="s1", owner=admin_user)
        p1 = Project.objects.create(workspace=ws, name="P1", identifier="P1")
        p2 = Project.objects.create(workspace=ws, name="P2", identifier="P2")
        TaskStatus.objects.create(project=p1, name="待办", order=1)
        TaskStatus.objects.create(project=p2, name="待办", order=1)  # 不抛异常

    def test_type_choices(self, project):
        """type 字段接受预定义选项"""
        valid_types = ["backlog", "unstarted", "started", "completed", "cancelled"]
        for t in valid_types:
            status = TaskStatus.objects.create(
                project=project, name=f"Status-{t}", type=t, order=0,
            )
            assert status.type == t

    def test_ordering_by_order_field(self, project):
        """按 order 字段排序"""
        s2 = TaskStatus.objects.create(project=project, name="Second", order=2)
        s1 = TaskStatus.objects.create(project=project, name="First", order=1)
        statuses = list(TaskStatus.objects.filter(project=project))
        assert statuses[0] == s1
        assert statuses[1] == s2


class TestTaskModel:
    """Task 模型"""

    def test_create_task(self, project, status_todo, admin_user):
        """创建任务 — 基本字段"""
        task = Task.objects.create(
            project=project,
            title="Test Task",
            description="A test task",
            priority=Task.Priority.HIGH,
            status=status_todo,
            created_by=admin_user,
        )
        assert task.title == "Test Task"
        assert task.priority == Task.Priority.HIGH
        assert task.status == status_todo
        assert task.created_by == admin_user
        assert task.order == 0.0

    def test_create_subtask(self, project, status_todo, admin_user):
        """创建子任务 — parent 自引用"""
        parent = Task.objects.create(
            project=project, title="Parent", status=status_todo, created_by=admin_user,
        )
        child = Task.objects.create(
            project=project, title="Child", status=status_todo,
            created_by=admin_user, parent=parent,
        )
        assert child.parent == parent
        assert parent.subtasks.count() == 1
        assert parent.subtasks.first() == child

    def test_priority_display(self, project, status_todo, admin_user):
        """get_priority_display 返回中文"""
        task = Task.objects.create(
            project=project, title="Prio Test", status=status_todo,
            created_by=admin_user, priority="urgent",
        )
        assert task.get_priority_display() == "紧急"
        task.priority = "low"
        task.save()
        assert task.get_priority_display() == "低"

    def test_status_is_protected(self, project, status_todo, admin_user):
        """status FK 使用 PROTECT, 删除 status 会被阻止"""
        task = Task.objects.create(
            project=project, title="Protect Test", status=status_todo,
            created_by=admin_user,
        )
        with pytest.raises(Exception):
            status_todo.delete()
