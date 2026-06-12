"""
accounts 模块 — Serializer 层单元测试

测试覆盖:
  - RegisterSerializer: 成功注册 / 密码过短 / 缺少 email
  - LoginSerializer: 正确凭证 / 错误密码 / 禁用账号 / 无效邮箱
  - ChangePasswordSerializer: 正确旧密码 / 错误旧密码
  - UserSerializer: 字段白名单
"""

import pytest
from unittest.mock import Mock, patch
from apps.accounts.serializers import (
    RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, UserSerializer,
)

pytestmark = pytest.mark.django_db


class TestRegisterSerializer:
    """RegisterSerializer 单元测试"""

    def test_valid_registration(self):
        serializer = RegisterSerializer(data={
            "email": "new@test.com",
            "name": "New User",
            "password": "Pass123456",
        })
        assert serializer.is_valid()
        # create 会调用 UserManager.create_user
        user = serializer.save()
        assert user.email == "new@test.com"
        assert user.name == "New User"
        assert user.check_password("Pass123456")

    def test_password_min_length(self):
        serializer = RegisterSerializer(data={
            "email": "short@test.com",
            "name": "Short Pass",
            "password": "12345",  # < 6
        })
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_missing_email(self):
        serializer = RegisterSerializer(data={
            "name": "No Email",
            "password": "Pass123456",
        })
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_invalid_email(self):
        serializer = RegisterSerializer(data={
            "email": "not-an-email",
            "name": "Bad Email",
            "password": "Pass123456",
        })
        assert not serializer.is_valid()
        assert "email" in serializer.errors


class TestLoginSerializer:
    """LoginSerializer 单元测试"""

    def test_valid_login(self):
        with patch("apps.accounts.serializers.authenticate") as mock_auth:
            mock_user = Mock(is_active=True)
            mock_auth.return_value = mock_user
            serializer = LoginSerializer(data={
                "email": "test@example.com",
                "password": "correct",
            })
            assert serializer.is_valid()
            assert serializer.validated_data["user"] == mock_user

    def test_wrong_password(self):
        with patch("apps.accounts.serializers.authenticate", return_value=None):
            serializer = LoginSerializer(data={
                "email": "test@example.com",
                "password": "wrong",
            })
            assert not serializer.is_valid()
            assert "邮箱或密码错误" in str(serializer.errors)

    def test_disabled_account(self):
        with patch("apps.accounts.serializers.authenticate") as mock_auth:
            mock_user = Mock(is_active=False)
            mock_auth.return_value = mock_user
            serializer = LoginSerializer(data={
                "email": "disabled@test.com",
                "password": "correct",
            })
            assert not serializer.is_valid()
            assert "账号已被禁用" in str(serializer.errors)

    def test_invalid_email_format(self):
        serializer = LoginSerializer(data={
            "email": "bad-email",
            "password": "anything",
        })
        assert not serializer.is_valid()
        assert "email" in serializer.errors


class TestChangePasswordSerializer:
    """ChangePasswordSerializer 单元测试"""

    def test_valid_change(self):
        mock_user = Mock()
        mock_user.check_password.return_value = True
        mock_request = Mock(user=mock_user)
        serializer = ChangePasswordSerializer(
            data={"old_password": "OldPass123", "new_password": "NewPass456"},
            context={"request": mock_request},
        )
        assert serializer.is_valid()

    def test_wrong_old_password(self):
        mock_user = Mock()
        mock_user.check_password.return_value = False
        mock_request = Mock(user=mock_user)
        serializer = ChangePasswordSerializer(
            data={"old_password": "WrongOld", "new_password": "NewPass456"},
            context={"request": mock_request},
        )
        assert not serializer.is_valid()
        assert "原密码错误" in str(serializer.errors["old_password"])

    def test_new_password_too_short(self):
        mock_user = Mock()
        mock_user.check_password.return_value = True
        mock_request = Mock(user=mock_user)
        serializer = ChangePasswordSerializer(
            data={"old_password": "OldPass", "new_password": "12345"},
            context={"request": mock_request},
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors


class TestUserSerializer:
    """UserSerializer"""

    def test_fields_whitelist(self, user):
        serializer = UserSerializer(user)
        data = serializer.data
        # 白名单字段
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "avatar" in data
        # 不应包含敏感字段
        assert "password" not in data
