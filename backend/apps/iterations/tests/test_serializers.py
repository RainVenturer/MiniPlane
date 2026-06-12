"""
iterations 模块 — Serializer 层单元测试

测试覆盖:
  - IterationCreateSerializer.validate (end_date > start_date)
  - AddTasksToIterationSerializer 校验
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock
from apps.iterations.serializers import (
    IterationSerializer, IterationCreateSerializer,
    AddTasksToIterationSerializer,
)
from apps.workspaces.models import Workspace
from apps.projects.models import Project
from apps.iterations.models import Iteration

pytestmark = pytest.mark.django_db


class TestIterationCreateSerializer:
    """IterationCreateSerializer 校验"""

    def test_valid_dates(self, admin_user):
        """正常日期范围"""
        ws = Workspace.objects.create(name="ID WS", slug="id-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="ID Proj", identifier="ID")
        serializer = IterationCreateSerializer(
            data={
                "name": "Sprint 1",
                "start_date": "2026-06-01",
                "end_date": "2026-06-14",
            },
            context={"project_id": proj.id},
        )
        assert serializer.is_valid()
        iteration = serializer.save()
        assert iteration.project_id == proj.id

    def test_end_date_before_start_date(self):
        """结束日期早于开始日期 — 校验拒绝"""
        serializer = IterationCreateSerializer(data={
            "name": "Bad Sprint",
            "start_date": "2026-06-10",
            "end_date": "2026-06-01",
        })
        assert not serializer.is_valid()
        assert "结束日期必须晚于开始日期" in str(serializer.errors["end_date"])

    def test_end_date_equals_start_date(self):
        """结束日期等于开始日期 — 校验拒绝"""
        serializer = IterationCreateSerializer(data={
            "name": "Zero Sprint",
            "start_date": "2026-06-01",
            "end_date": "2026-06-01",
        })
        assert not serializer.is_valid()
        assert "end_date" in serializer.errors

    def test_missing_dates(self):
        """缺少日期字段"""
        serializer = IterationCreateSerializer(data={"name": "No Dates"})
        assert not serializer.is_valid()
        assert "start_date" in serializer.errors
        assert "end_date" in serializer.errors

    def test_create_injects_project_id(self, admin_user):
        """create 时注入 project_id"""
        ws = Workspace.objects.create(name="IP WS", slug="ip-ws", owner=admin_user)
        proj = Project.objects.create(workspace=ws, name="IP Proj", identifier="IP")
        serializer = IterationCreateSerializer(
            data={
                "name": "Sprint X",
                "start_date": "2026-07-01",
                "end_date": "2026-07-14",
            },
            context={"project_id": proj.id},
        )
        assert serializer.is_valid()
        iteration = serializer.save()
        assert iteration.project_id == proj.id


class TestAddTasksToIterationSerializer:
    """AddTasksToIterationSerializer 校验"""

    def test_valid_task_ids(self):
        import uuid
        ids = [str(uuid.uuid4()) for _ in range(3)]
        serializer = AddTasksToIterationSerializer(data={"task_ids": ids})
        assert serializer.is_valid()

    def test_empty_list_rejected(self):
        """空列表 — min_length=1"""
        serializer = AddTasksToIterationSerializer(data={"task_ids": []})
        assert not serializer.is_valid()
        assert "task_ids" in serializer.errors

    def test_too_many_ids_rejected(self):
        """超过 100 个 ID — max_length=100"""
        import uuid
        ids = [str(uuid.uuid4()) for _ in range(101)]
        serializer = AddTasksToIterationSerializer(data={"task_ids": ids})
        assert not serializer.is_valid()

    def test_invalid_uuid_rejected(self):
        serializer = AddTasksToIterationSerializer(data={
            "task_ids": ["not-a-uuid"],
        })
        assert not serializer.is_valid()
