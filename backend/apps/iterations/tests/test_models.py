"""
iterations 模块 — Model 层单元测试

测试覆盖:
  - Iteration CheckConstraint (end_date > start_date)
  - task_count / completed_count 属性
  - __str__ 格式
"""

import pytest
from datetime import date, timedelta
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace
from apps.projects.models import Project
from apps.iterations.models import Iteration
from apps.tasks.models import Task, TaskStatus

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def project(admin_user):
    ws = Workspace.objects.create(name="Iter WS", slug="iter-ws", owner=admin_user)
    return Project.objects.create(workspace=ws, name="Iter Proj", identifier="ITER")


class TestIterationModel:
    """Iteration 模型"""

    def test_create_iteration(self, project):
        """创建迭代"""
        iteration = Iteration.objects.create(
            project=project,
            name="Sprint 1",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 14),
        )
        assert iteration.name == "Sprint 1"
        assert iteration.is_active is True
        assert str(iteration) == "ITER/Sprint 1"

    def test_end_date_must_be_after_start_date(self, project):
        """结束日期必须晚于开始日期 — CheckConstraint"""
        with pytest.raises(IntegrityError):
            Iteration.objects.create(
                project=project,
                name="Bad Sprint",
                start_date=date(2026, 6, 10),
                end_date=date(2026, 6, 1),
            )

    def test_end_date_equals_start_date_rejected(self, project):
        """结束日期等于开始日期 — 也应拒绝"""
        with pytest.raises(IntegrityError):
            Iteration.objects.create(
                project=project,
                name="Same Day",
                start_date=date(2026, 6, 1),
                end_date=date(2026, 6, 1),
            )

    def test_task_count_property(self, project, admin_user):
        """task_count 属性计算关联任务数"""
        iteration = Iteration.objects.create(
            project=project, name="Sprint 1",
            start_date=date(2026, 6, 1), end_date=date(2026, 6, 14),
        )
        assert iteration.task_count == 0

        status = TaskStatus.objects.create(project=project, name="待办", order=1)
        Task.objects.create(
            project=project, title="T1", status=status,
            created_by=admin_user, iteration=iteration,
        )
        Task.objects.create(
            project=project, title="T2", status=status,
            created_by=admin_user, iteration=iteration,
        )
        assert iteration.task_count == 2

    def test_completed_count_property(self, project, admin_user):
        """completed_count 只计算 type=completed 的任务"""
        iteration = Iteration.objects.create(
            project=project, name="Sprint 2",
            start_date=date(2026, 6, 15), end_date=date(2026, 6, 28),
        )
        todo = TaskStatus.objects.create(project=project, name="待办", order=1, type="unstarted")
        done = TaskStatus.objects.create(project=project, name="已完成", order=2, type="completed")

        Task.objects.create(
            project=project, title="Done Task", status=done,
            created_by=admin_user, iteration=iteration,
        )
        Task.objects.create(
            project=project, title="Todo Task", status=todo,
            created_by=admin_user, iteration=iteration,
        )
        assert iteration.completed_count == 1
        assert iteration.task_count == 2

    def test_ordering_by_start_date_desc(self, project):
        """按 start_date 倒序排列"""
        i1 = Iteration.objects.create(
            project=project, name="Earlier",
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 14),
        )
        i2 = Iteration.objects.create(
            project=project, name="Later",
            start_date=date(2026, 6, 1), end_date=date(2026, 6, 14),
        )
        iterations = list(Iteration.objects.filter(project=project))
        assert iterations[0] == i2
        assert iterations[1] == i1
