"""
comments 模块 — Model 层单元测试

测试覆盖:
  - Comment 创建
  - Comment 排序
"""

import pytest
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace
from apps.projects.models import Project
from apps.tasks.models import Task, TaskStatus
from apps.comments.models import Comment

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestCommentModel:
    """Comment 模型"""

    def test_create_comment(self, admin_user):
        """创建评论"""
        ws = Workspace.objects.create(name="Cmt WS", slug="cmt-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="Cmt Proj", identifier="CMT")
        status = TaskStatus.objects.create(project=proj, name="待办", order=1)
        task = Task.objects.create(
            project=proj, title="Comment Task", status=status, created_by=admin_user,
        )
        comment = Comment.objects.create(
            task=task, author=admin_user, content="这是一条评论",
        )
        assert comment.task == task
        assert comment.author == admin_user
        assert comment.content == "这是一条评论"

    def test_ordering_by_created_at(self, admin_user):
        """按 created_at 正序排列"""
        ws = Workspace.objects.create(name="Ord WS", slug="ord-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="Ord Proj", identifier="ORD")
        status = TaskStatus.objects.create(project=proj, name="待办", order=1)
        task = Task.objects.create(
            project=proj, title="Ord Task", status=status, created_by=admin_user,
        )
        c1 = Comment.objects.create(task=task, author=admin_user, content="First")
        c2 = Comment.objects.create(task=task, author=admin_user, content="Second")
        comments = list(Comment.objects.filter(task=task))
        assert comments[0] == c1
        assert comments[1] == c2

    def test_cascade_on_task_delete(self, admin_user):
        """删除任务时级联删除评论"""
        ws = Workspace.objects.create(name="Cas WS", slug="cas-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="Cas Proj", identifier="CAS")
        status = TaskStatus.objects.create(project=proj, name="待办", order=1)
        task = Task.objects.create(
            project=proj, title="Cas Task", status=status, created_by=admin_user,
        )
        task_id = task.id
        Comment.objects.create(task=task, author=admin_user, content="Test")
        assert Comment.objects.filter(task_id=task_id).count() == 1
        task.delete()
        assert Comment.objects.filter(task_id=task_id).count() == 0
