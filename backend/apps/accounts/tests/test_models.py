"""
accounts 模块 — Model 层单元测试

测试覆盖:
  - UserManager.create_user / create_superuser
  - User.__str__
  - UserManager 参数校验
"""

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestUserManager:
    """UserManager 方法"""

    def test_create_user_success(self):
        """正常创建用户 — 密码加密、is_active=True"""
        user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123",
            name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.check_password("StrongPass123") is True
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_empty_email_raises(self):
        """空邮箱应抛出 ValueError"""
        with pytest.raises(ValueError, match="邮箱地址为必填项"):
            User.objects.create_user(email="", password="pass1234")

    def test_create_user_no_email_raises(self):
        """未传 email 应抛出 TypeError（required arg）"""
        with pytest.raises(TypeError):
            User.objects.create_user(password="pass1234")

    def test_create_superuser_sets_staff_and_superuser(self):
        """超级用户 is_staff=True, is_superuser=True"""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123",
            name="Admin",
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True

    def test_create_superuser_defaults_can_override(self):
        """superuser 默认值可被覆盖"""
        user = User.objects.create_superuser(
            email="super@example.com",
            password="SuperPass123",
            name="Super",
            is_staff=False,
            is_superuser=False,
        )
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_normalizes_email(self):
        """邮箱自动转为小写"""
        user = User.objects.create_user(
            email="Test@Example.COM",
            password="pass1234",
            name="Email Test",
        )
        assert user.email == "Test@example.com"


class TestUserModel:
    """User 模型行为"""

    def test_str_with_name(self, user):
        """__str__: 有 name 时，格式为 'name (email)'"""
        expected = f"{user.name} ({user.email})"
        assert str(user) == expected

    def test_str_without_name(self):
        """__str__: 无 name 时，格式为 'email (email)'"""
        user = User.objects.create_user(
            email="noname@test.com",
            password="pass1234",
        )
        assert str(user) == f"{user.email} ({user.email})"

    def test_uuid_primary_key(self, user):
        """主键为 UUID"""
        import uuid
        assert isinstance(user.id, uuid.UUID)

    def test_ordering_newest_first(self):
        """按 created_at 倒序排列"""
        u1 = User.objects.create_user(
            email="older@test.com", password="pass1234", name="Older",
        )
        u2 = User.objects.create_user(
            email="newer@test.com", password="pass1234", name="Newer",
        )
        users = list(User.objects.all())
        # 最新创建的在前
        assert users[0] == u2
        assert users[1] == u1
