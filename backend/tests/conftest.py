"""
MiniPlane 自动化测试 — 全局 Fixtures

覆盖 UC1-UC8 和 QS1-QS8 所需的测试数据。
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


# ═══════════════════════════════════════════════════════════════
# Django 测试配置 — 在 pytest 收集前生效
# ═══════════════════════════════════════════════════════════════


def pytest_configure():
    """覆盖测试环境设置"""
    from django.conf import settings
    # 使用内存文件存储替代 MinIO（测试环境 MinIO 不可用）
    settings.DEFAULT_FILE_STORAGE = (
        "django.core.files.storage.InMemoryStorage"
    )
    # 确保 DEBUG=True 以显示详细错误
    settings.DEBUG = True
    # 使用与生产环境一致的 APIRenderer（统一 {success, data, message} 格式）
    settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
        "apps.core.renderers.APIRenderer",
    )
    # 使用更快的密码哈希
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]

User = get_user_model()

# ═══════════════════════════════════════════════════════════════
# 基础 Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def api_client():
    """未认证的 API 客户端"""
    return APIClient()


@pytest.fixture
def user_data():
    """普通用户注册数据"""
    return {
        "email": "member@test.com",
        "password": "Member123456",
        "name": "普通成员",
    }


@pytest.fixture
def user(db, user_data):
    """已创建的普通用户"""
    return User.objects.create_user(**user_data)


@pytest.fixture
def admin_data():
    """管理员注册数据"""
    return {
        "email": "admin@test.com",
        "password": "Admin123456",
        "name": "管理员",
    }


@pytest.fixture
def admin_user(db, admin_data):
    """已创建的管理员 (is_superuser)"""
    return User.objects.create_superuser(**admin_data)


@pytest.fixture
def extra_user(db):
    """额外用户 — 用于测试跨用户权限隔离"""
    return User.objects.create_user(
        email="other@test.com",
        password="Other123456",
        name="其他用户",
    )


@pytest.fixture
def admin_client(db, admin_user):
    """已认证的管理员客户端"""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def user_client(db, user):
    """已认证的普通用户客户端"""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def extra_client(db, extra_user):
    """已认证的其他用户客户端"""
    client = APIClient()
    client.force_authenticate(user=extra_user)
    return client


# ═══════════════════════════════════════════════════════════════
# 工作空间 Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def workspace_data():
    return {"name": "测试团队", "description": "自动化测试工作空间"}


@pytest.fixture
def workspace(db, admin_user, user, workspace_data):
    """已创建的工作空间 — admin 是 owner"""
    from apps.workspaces.models import Workspace, WorkspaceMember

    ws = Workspace.objects.create(
        name=workspace_data["name"],
        slug="test-team",
        description=workspace_data["description"],
        owner=admin_user,
    )
    # admin 自动成为管理员
    WorkspaceMember.objects.create(workspace=ws, user=admin_user, role="admin")
    # 普通成员也加入
    WorkspaceMember.objects.create(workspace=ws, user=user, role="member")
    return ws


# ═══════════════════════════════════════════════════════════════
# 项目 Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def project_data():
    return {"name": "MiniPlane 开发", "identifier": "DEV", "description": "主开发项目"}


@pytest.fixture
def project(db, workspace, admin_user):
    """已创建的项目 — 含 6 个默认状态"""
    from apps.projects.models import Project, ProjectMember
    from apps.tasks.models import TaskStatus

    project = Project.objects.create(
        workspace=workspace,
        name="MiniPlane 开发",
        identifier="DEV",
        description="主开发项目",
    )
    ProjectMember.objects.create(project=project, user=admin_user, role="admin")
    # 初始化默认状态列 (与 views.py perform_create 一致)
    defaults = [
        ("Backlog", "#6b7280", "backlog", 0),
        ("待办", "#6366f1", "unstarted", 1),
        ("进行中", "#f59e0b", "started", 2),
        ("待评审", "#8b5cf6", "started", 3),
        ("已完成", "#10b981", "completed", 4),
        ("已取消", "#ef4444", "cancelled", 5),
    ]
    for name, color, type_, order in defaults:
        TaskStatus.objects.create(
            project=project, name=name, color=color, type=type_, order=order,
        )
    return project


# ═══════════════════════════════════════════════════════════════
# 任务 Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def task_status(project):
    """默认任务状态 — "待办" (unstarted)"""
    from apps.tasks.models import TaskStatus
    return TaskStatus.objects.get(project=project, type="unstarted")


@pytest.fixture
def task_in_progress(project):
    """"进行中" 状态"""
    from apps.tasks.models import TaskStatus
    return TaskStatus.objects.get(project=project, name="进行中")


@pytest.fixture
def task_done(project):
    """"已完成" 状态"""
    from apps.tasks.models import TaskStatus
    return TaskStatus.objects.get(project=project, name="已完成")


@pytest.fixture
def task_data():
    return {
        "title": "修复登录 Bug",
        "description": "特殊字符密码登录失败",
        "priority": "high",
    }


@pytest.fixture
def task(db, project, task_status, task_data, admin_user):
    """已创建的任务"""
    from apps.tasks.models import Task

    return Task.objects.create(
        project=project,
        status=task_status,
        title=task_data["title"],
        description=task_data["description"],
        priority=task_data["priority"],
        created_by=admin_user,
    )


# ═══════════════════════════════════════════════════════════════
# 迭代 Fixture
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def iteration(db, project):
    """已创建的迭代"""
    from apps.iterations.models import Iteration
    from datetime import date

    return Iteration.objects.create(
        project=project,
        name="Sprint 1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 14),
        description="第一轮迭代",
    )


# ═══════════════════════════════════════════════════════════════
# URL 辅助函数
# ═══════════════════════════════════════════════════════════════


def api(path):
    """拼接 API 路径"""
    return f"/api{path}"


def ws_url(ws_id):
    return api(f"/workspaces/{ws_id}/")


def proj_url(ws_id):
    return api(f"/workspaces/{ws_id}/projects/")


def task_url(proj_id):
    return api(f"/projects/{proj_id}/tasks/")
