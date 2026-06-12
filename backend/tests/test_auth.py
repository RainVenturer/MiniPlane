"""
UC1: 用户注册与登录

测试覆盖:
  - 注册新用户 (POST /api/auth/register/)
  - 用户登录 (POST /api/auth/login/)
  - 获取当前用户 (GET /api/auth/me/)
  - 更新用户信息 (PUT /api/auth/me/)
  - 修改密码 (POST /api/auth/change-password/)
  - 退出登录 (POST /api/auth/logout/)

对应 F1、NF3
"""

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestUserRegistration:
    """用户注册测试"""

    def test_register_success(self, api_client, user_data):
        """正常注册应返回 201 + token"""
        resp = api_client.post("/api/auth/register/", user_data, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert "access" in data["data"]
        assert "refresh" in data["data"]
        assert data["data"]["user"]["email"] == user_data["email"]
        assert data["data"]["user"]["name"] == user_data["name"]
        # 密码不应返回
        assert "password" not in data["data"]["user"]

    def test_register_creates_user(self, api_client, user_data):
        """注册后应在数据库创建用户"""
        resp = api_client.post("/api/auth/register/", user_data, format="json")
        assert resp.status_code == 201
        user = User.objects.get(email=user_data["email"])
        assert user.name == user_data["name"]
        assert user.check_password(user_data["password"])

    def test_register_duplicate_email(self, api_client, user_data, user):
        """重复邮箱注册应失败"""
        resp = api_client.post("/api/auth/register/", user_data, format="json")
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_register_missing_email(self, api_client):
        """缺少邮箱应返回 400"""
        resp = api_client.post("/api/auth/register/", {
            "password": "Test123456", "name": "Test",
        }, format="json")
        assert resp.status_code == 400

    def test_register_short_password(self, api_client):
        """密码不足 6 位应拒绝"""
        resp = api_client.post("/api/auth/register/", {
            "email": "test@test.com", "password": "12345", "name": "Test",
        }, format="json")
        assert resp.status_code == 400

    def test_register_invalid_email(self, api_client):
        """无效邮箱格式应拒绝"""
        resp = api_client.post("/api/auth/register/", {
            "email": "not-an-email", "password": "Test123456", "name": "Test",
        }, format="json")
        assert resp.status_code == 400


class TestUserLogin:
    """用户登录测试"""

    def test_login_success(self, api_client, user, user_data):
        """正确凭据应返回 token"""
        resp = api_client.post("/api/auth/login/", {
            "email": user_data["email"],
            "password": user_data["password"],
        }, format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "access" in data["data"]
        assert data["data"]["user"]["email"] == user_data["email"]

    def test_login_wrong_password(self, api_client, user, user_data):
        """错误密码应返回 400"""
        resp = api_client.post("/api/auth/login/", {
            "email": user_data["email"],
            "password": "WrongPassword",
        }, format="json")
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_login_nonexistent_email(self, api_client):
        """不存在的邮箱应返回 400"""
        resp = api_client.post("/api/auth/login/", {
            "email": "nobody@test.com",
            "password": "Test123456",
        }, format="json")
        assert resp.status_code == 400

    def test_login_disabled_user(self, api_client, user):
        """被禁用用户应拒绝登录"""
        user.is_active = False
        user.save()
        resp = api_client.post("/api/auth/login/", {
            "email": user.email,
            "password": "Member123456",
        }, format="json")
        assert resp.status_code == 400

    def test_login_missing_fields(self, api_client):
        """缺少字段应返回 400"""
        resp = api_client.post("/api/auth/login/", {
            "email": "test@test.com",
        }, format="json")
        assert resp.status_code == 400


class TestAuthMe:
    """获取/更新当前用户"""

    def test_get_me(self, admin_client, admin_user):
        """已认证用户可获取自己信息"""
        resp = admin_client.get("/api/auth/me/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == admin_user.email

    def test_get_me_unauthenticated(self, api_client):
        """未认证请求应返回 401"""
        resp = api_client.get("/api/auth/me/")
        assert resp.status_code == 401

    def test_update_me(self, admin_client, admin_user):
        """更新用户名"""
        resp = admin_client.put("/api/auth/me/", {
            "name": "新名字",
        }, format="json")
        assert resp.status_code == 200
        admin_user.refresh_from_db()
        assert admin_user.name == "新名字"

    def test_change_password(self, admin_client, admin_user):
        """修改密码后旧密码失效，新密码可用"""
        resp = admin_client.post("/api/auth/change-password/", {
            "old_password": "Admin123456",
            "new_password": "NewPass789",
        }, format="json")
        assert resp.status_code == 200
        admin_user.refresh_from_db()
        assert admin_user.check_password("NewPass789")

    def test_change_password_wrong_old(self, admin_client):
        """原密码错误应拒绝"""
        resp = admin_client.post("/api/auth/change-password/", {
            "old_password": "WrongOldPass",
            "new_password": "NewPass789",
        }, format="json")
        assert resp.status_code == 400


class TestLogout:
    """退出登录"""

    def test_logout_success(self, admin_client):
        """退出登录应返回 200"""
        resp = admin_client.post("/api/auth/logout/", {}, format="json")
        assert resp.status_code == 200
