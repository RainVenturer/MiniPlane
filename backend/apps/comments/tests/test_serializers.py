"""
comments 模块 — Serializer 层单元测试

测试覆盖:
  - CommentCreateSerializer.create (注入 task_id 和 author)
  - CommentSerializer 字段
"""

import pytest
from unittest.mock import Mock
from apps.comments.serializers import CommentSerializer, CommentCreateSerializer

pytestmark = pytest.mark.django_db


class TestCommentCreateSerializer:
    """CommentCreateSerializer"""

    def test_create_injects_task_and_author(self, admin_user):
        """create 时注入 task_id 和 author"""
        from apps.workspaces.models import Workspace
        from apps.projects.models import Project
        from apps.tasks.models import Task, TaskStatus

        ws = Workspace.objects.create(name="CC WS", slug="cc-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="CC Proj", identifier="CC")
        status = TaskStatus.objects.create(project=proj, name="待办", order=1)
        task = Task.objects.create(
            project=proj, title="Comment Target", status=status, created_by=admin_user,
        )

        mock_request = Mock(user=admin_user)
        serializer = CommentCreateSerializer(
            data={"content": "我的评论"},
            context={"task_id": task.id, "request": mock_request},
        )
        assert serializer.is_valid()
        comment = serializer.save()
        assert comment.task_id == task.id
        assert comment.author == admin_user
        assert comment.content == "我的评论"

    def test_empty_content_rejected(self):
        serializer = CommentCreateSerializer(data={"content": ""})
        assert not serializer.is_valid()
        assert "content" in serializer.errors


class TestCommentSerializer:
    """CommentSerializer 字段"""

    def test_fields_include_author_info(self, admin_user):
        from apps.workspaces.models import Workspace
        from apps.projects.models import Project
        from apps.tasks.models import Task, TaskStatus
        from apps.comments.models import Comment

        ws = Workspace.objects.create(name="CS WS", slug="cs-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="CS Proj", identifier="CS")
        status = TaskStatus.objects.create(project=proj, name="待办", order=1)
        task = Task.objects.create(
            project=proj, title="Ser Task", status=status, created_by=admin_user,
        )
        comment = Comment.objects.create(task=task, author=admin_user, content="Test")

        serializer = CommentSerializer(comment)
        data = serializer.data
        assert data["author_name"] == admin_user.name
        assert data["content"] == "Test"
