"""
tasks 模块 — Serializer 层单元测试

测试覆盖:
  - TaskCreateSerializer: 自动分配 UNSTARTED 状态 / 回退到首个状态
  - TaskStatusChangeSerializer: 跨项目状态拒绝 / 事务内创建 Activity+通知
  - TaskStatusSerializer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from apps.tasks.serializers import (
    TaskStatusSerializer, TaskCreateSerializer,
    TaskStatusChangeSerializer, TaskSerializer,
)
from apps.tasks.models import Task, TaskStatus
from apps.workspaces.models import Workspace
from apps.projects.models import Project

pytestmark = pytest.mark.django_db


class TestTaskCreateSerializer:
    """TaskCreateSerializer"""

    def test_create_auto_assigns_unstarted_status(self, admin_user):
        """未指定 status 时自动分配 UNSTARTED 状态"""
        ws = Workspace.objects.create(name="TC WS", slug="tc-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="TC Proj", identifier="TC")
        unstarted = TaskStatus.objects.create(
            project=proj, name="待办", type=TaskStatus.Type.UNSTARTED, order=1,
        )
        mock_request = Mock(user=admin_user)
        serializer = TaskCreateSerializer(
            data={"title": "Auto Status Task"},
            context={"project_id": proj.id, "request": mock_request},
        )
        assert serializer.is_valid()
        task = serializer.save()
        assert task.status == unstarted

    def test_create_falls_back_to_first_status(self, admin_user):
        """无 UNSTARTED 状态时回退到首个状态"""
        ws = Workspace.objects.create(name="FB WS", slug="fb-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="FB Proj", identifier="FB")
        first_status = TaskStatus.objects.create(
            project=proj, name="Backlog", type=TaskStatus.Type.BACKLOG, order=0,
        )
        mock_request = Mock(user=admin_user)
        serializer = TaskCreateSerializer(
            data={"title": "Fallback Task"},
            context={"project_id": proj.id, "request": mock_request},
        )
        assert serializer.is_valid()
        task = serializer.save()
        assert task.status == first_status

    def test_create_with_explicit_status(self, admin_user):
        """指定 status 时使用指定的状态"""
        ws = Workspace.objects.create(name="ES WS", slug="es-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="ES Proj", identifier="ES")
        explicit = TaskStatus.objects.create(
            project=proj, name="Custom", type=TaskStatus.Type.STARTED, order=1,
        )
        mock_request = Mock(user=admin_user)
        serializer = TaskCreateSerializer(
            data={"title": "Explicit Status", "status": str(explicit.id)},
            context={"project_id": proj.id, "request": mock_request},
        )
        assert serializer.is_valid()
        task = serializer.save()
        assert task.status == explicit

    def test_create_injects_created_by(self, admin_user):
        """create 时注入 created_by = request.user"""
        ws = Workspace.objects.create(name="CB WS", slug="cb-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="CB Proj", identifier="CB")
        TaskStatus.objects.create(
            project=proj, name="待办", type=TaskStatus.Type.UNSTARTED, order=1,
        )
        mock_request = Mock(user=admin_user)
        serializer = TaskCreateSerializer(
            data={"title": "Creator Test"},
            context={"project_id": proj.id, "request": mock_request},
        )
        assert serializer.is_valid()
        task = serializer.save()
        assert task.created_by == admin_user


class TestTaskStatusChangeSerializer:
    """TaskStatusChangeSerializer — 状态变更"""

    def test_validate_rejects_cross_project_status(self, admin_user):
        """拒绝跨项目状态 ID"""
        ws = Workspace.objects.create(name="CP WS", slug="cp-ws", owner=admin_user)
        p1 = Project.objects.create(workspace=ws, name="P1", identifier="P1")
        p2 = Project.objects.create(workspace=ws, name="P2", identifier="P2")
        s1 = TaskStatus.objects.create(project=p1, name="待办", type="unstarted", order=1)
        s2 = TaskStatus.objects.create(project=p2, name="待办", type="unstarted", order=1)
        task = Task.objects.create(
            project=p1, title="Cross Task", status=s1, created_by=admin_user,
        )
        serializer = TaskStatusChangeSerializer(
            data={"status": str(s2.id)},
            context={"task": task},
        )
        assert not serializer.is_valid()
        assert "目标状态不属于当前项目" in str(serializer.errors["status"])

    def test_validate_accepts_same_project_status(self, admin_user):
        """接受同项目状态 ID"""
        ws = Workspace.objects.create(name="SP WS", slug="sp-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="SP Proj", identifier="SP")
        s1 = TaskStatus.objects.create(project=proj, name="待办", type="unstarted", order=1)
        s2 = TaskStatus.objects.create(project=proj, name="进行中", type="started", order=2)
        task = Task.objects.create(
            project=proj, title="Inline Task", status=s1, created_by=admin_user,
        )
        serializer = TaskStatusChangeSerializer(
            data={"status": str(s2.id)},
            context={"task": task},
        )
        assert serializer.is_valid()

    @patch("apps.notifications.services._create_and_send")
    def test_save_creates_activity_and_notification(self, mock_create_send, admin_user, extra_user):
        """save() 在事务内创建 Activity 并发送通知"""
        ws = Workspace.objects.create(name="SA WS", slug="sa-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="SA Proj", identifier="SA")
        s1 = TaskStatus.objects.create(project=proj, name="待办", type="unstarted", order=1)
        s2 = TaskStatus.objects.create(project=proj, name="已完成", type="completed", order=2)
        task = Task.objects.create(
            project=proj, title="Notify Task", status=s1,
            created_by=admin_user, assignee=extra_user,  # 设置 assignee 触发通知
        )
        mock_request = Mock(user=admin_user)
        serializer = TaskStatusChangeSerializer(
            data={"status": str(s2.id)},
            context={"task": task, "request": mock_request},
        )
        assert serializer.is_valid()
        result = serializer.save()
        assert result.status == s2
        # 验证通知被调用
        mock_create_send.assert_called_once()
        # 验证 Activity 被创建
        from apps.activities.models import Activity
        activities = Activity.objects.filter(task=task, action="status_changed")
        assert activities.count() == 1
        assert activities.first().old_value == str(s1.id)
        assert activities.first().new_value == str(s2.id)


class TestTaskSerializer:
    """TaskSerializer 字段"""

    def test_subtask_and_comment_counts(self, admin_user):
        """subtask_count 和 comment_count 属性"""
        ws = Workspace.objects.create(name="TCnt WS", slug="tcnt-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="TCnt Proj", identifier="TCNT")
        status = TaskStatus.objects.create(project=proj, name="待办", order=1)
        parent = Task.objects.create(
            project=proj, title="Parent", status=status, created_by=admin_user,
        )
        Task.objects.create(
            project=proj, title="Child", status=status, created_by=admin_user, parent=parent,
        )
        serializer = TaskSerializer(parent)
        data = serializer.data
        assert data["subtask_count"] == 1
        assert data["comment_count"] == 0
