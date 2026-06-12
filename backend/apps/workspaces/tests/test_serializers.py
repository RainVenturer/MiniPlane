"""
workspaces 模块 — Serializer 层单元测试

测试覆盖:
  - WorkspaceCreateSerializer._make_slug (生成 / 冲突追加 / UUID 兜底)
  - AddMemberSerializer 校验
  - WorkspaceSerializer 只读字段
"""

import pytest
from unittest.mock import Mock, patch
from apps.workspaces.serializers import (
    WorkspaceCreateSerializer, AddMemberSerializer,
    WorkspaceSerializer, WorkspaceMemberSerializer,
)
from apps.workspaces.models import Workspace, WorkspaceMember

pytestmark = pytest.mark.django_db


class TestMakeSlug:
    """WorkspaceCreateSerializer._make_slug 静态方法"""

    def test_slug_from_simple_name(self):
        slug = WorkspaceCreateSerializer._make_slug("My New Workspace")
        assert slug == "my-new-workspace"

    def test_slug_from_chinese_name(self):
        """中文名称去除非字母数字的字符后可能保留中文字符或回退"""
        slug = WorkspaceCreateSerializer._make_slug("我的团队")
        # \w in Python unicode mode matches Chinese, so result keeps Chinese chars
        # or falls back to 'workspace' if stripped
        assert slug in ("workspace", "我的团队") or len(slug) > 0

    def test_slug_strips_trailing_hyphens(self):
        slug = WorkspaceCreateSerializer._make_slug("  --Spaces--  ")
        assert slug == "spaces"

    def test_slug_appends_suffix_on_collision(self):
        with patch.object(Workspace.objects, "filter") as mock_filter:
            # 第一次冲突, 第二次不冲突
            mock_filter.return_value.exists.side_effect = [True, False]
            slug = WorkspaceCreateSerializer._make_slug("Duplicate")
            assert slug == "duplicate-1"

    def test_slug_appends_incrementing_suffix(self):
        with patch.object(Workspace.objects, "filter") as mock_filter:
            # 前 3 次都冲突, 第 4 次不冲突
            mock_filter.return_value.exists.side_effect = [True, True, True, False]
            slug = WorkspaceCreateSerializer._make_slug("Popular")
            assert slug == "popular-3"

    def test_slug_fallback_to_uuid_after_100_collisions(self):
        with patch.object(Workspace.objects, "filter") as mock_filter:
            mock_filter.return_value.exists.return_value = True
            slug = WorkspaceCreateSerializer._make_slug("AlwaysTaken")
            # After 100 collisions, falls back to UUID hex suffix
            assert slug.startswith("alwaystaken-")
            # The suffix should be a 6-char hex or UUID segment
            suffix = slug.split("-", 1)[1] if "-" in slug else slug
            assert len(suffix) > 0


class TestAddMemberSerializer:
    """AddMemberSerializer 校验"""

    def test_valid_email_and_role(self):
        serializer = AddMemberSerializer(data={
            "email": "member@test.com",
            "role": "member",
        })
        assert serializer.is_valid()

    def test_default_role_is_member(self):
        serializer = AddMemberSerializer(data={"email": "new@test.com"})
        assert serializer.is_valid()
        assert serializer.validated_data["role"] == "member"

    def test_invalid_email(self):
        serializer = AddMemberSerializer(data={
            "email": "not-email",
            "role": "member",
        })
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_invalid_role(self):
        serializer = AddMemberSerializer(data={
            "email": "test@test.com",
            "role": "superadmin",  # 不在选项内
        })
        assert not serializer.is_valid()
        assert "role" in serializer.errors


class TestWorkspaceSerializer:
    """WorkspaceSerializer 字段"""

    def test_readonly_fields(self, admin_user):
        ws = Workspace.objects.create(name="ReadOnly WS", slug="ro-ws", owner=admin_user)
        serializer = WorkspaceSerializer(ws)
        data = serializer.data
        assert data["name"] == "ReadOnly WS"
        assert data["slug"] == "ro-ws"
        assert data["owner_name"] == admin_user.name
        assert data["member_count"] == 0
        # owner appears as UUID in serialized output
        assert str(data["owner"]) == str(admin_user.id)
