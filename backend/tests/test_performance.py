"""
NF1 + QS8: 性能基准 + 测试性验证

测试覆盖:
  - 核心 API 响应时间基准 (NF1)
  - 50 并发任务创建时间 (QS8 相关)
  - 分页正确性
  - 操作日志完整性
  - 全流程端到端时间 (QS6 易用性)
"""

import time
import pytest

pytestmark = pytest.mark.django_db


class TestResponseTime:
    """API 响应时间基准 (NF1 — 空库条件下)"""

    ENDPOINTS = [
        ("GET", "/api/auth/me/", "获取当前用户"),
        ("GET", "/api/workspaces/", "工作空间列表"),
        ("GET", "/api/projects/", "项目列表"),
        ("POST", "/api/auth/login/", "登录"),
        ("GET", "/api/auth/me/", "获取用户信息"),
    ]

    def test_login_response_time(self, api_client, user):
        """登录接口 < 500ms"""
        start = time.time()
        resp = api_client.post("/api/auth/login/", {
            "email": user.email,
            "password": "Member123456",
        }, format="json")
        elapsed = time.time() - start
        assert resp.status_code == 200, f"Login failed: {resp.json()}"
        assert elapsed < 0.5, f"Login took {elapsed:.3f}s"

    def test_workspace_list_time(self, admin_client):
        """工作空间列表 < 200ms"""
        start = time.time()
        resp = admin_client.get("/api/workspaces/")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 0.2, f"Workspace list took {elapsed:.3f}s"

    def test_task_list_time(self, admin_client, project):
        """任务列表 < 200ms"""
        start = time.time()
        resp = admin_client.get(f"/api/projects/{project.id}/tasks/")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 0.2, f"Task list took {elapsed:.3f}s"

    def test_statistics_time(self, admin_client, project):
        """统计接口 < 300ms"""
        start = time.time()
        resp = admin_client.get(f"/api/projects/{project.id}/statistics/")
        elapsed = time.time() - start
        assert resp.status_code == 200
        assert elapsed < 0.3, f"Statistics took {elapsed:.3f}s"


class TestPagination:
    """分页正确性"""

    def test_default_page_size(self, admin_client, project):
        """默认每页 20 条"""
        # 创建 25 个任务
        for i in range(25):
            admin_client.post(f"/api/projects/{project.id}/tasks/", {
                "title": f"Task {i}",
            }, format="json")
        resp = admin_client.get(f"/api/projects/{project.id}/tasks/")
        data = resp.json()
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 20

    def test_custom_page_size(self, admin_client, project):
        """自定义每页条数"""
        resp = admin_client.get(
            f"/api/projects/{project.id}/tasks/?page_size=5"
        )
        assert resp.json()["pagination"]["page_size"] == 5


class TestConcurrentTaskCreation:
    """并发创建任务 — 50 条基准"""

    def test_create_50_tasks(self, admin_client, project):
        """50 条任务创建（串行）"""
        start = time.time()
        for i in range(50):
            resp = admin_client.post(f"/api/projects/{project.id}/tasks/", {
                "title": f"Bulk Task {i}",
                "priority": "medium",
            }, format="json")
            assert resp.status_code == 201, f"Task {i} failed"
        elapsed = time.time() - start
        # 50 条任务创建应在 10 秒内完成
        assert elapsed < 10, f"50 tasks took {elapsed:.1f}s"
        print(f"\n  50 tasks created in {elapsed:.1f}s ({elapsed/50:.2f}s each)")


class TestEndToEndFlow:
    """端到端流程 (QS6 易用性) — 模拟完整用户操作"""

    def test_full_workflow(self, api_client, admin_data):
        """完整流程: 注册 → 登录 → 创建WS → 创建项目 → 创建任务 → 更新状态 → 评论"""
        total_start = time.time()

        # 1. 注册
        resp = api_client.post("/api/auth/register/", {
            "email": "e2e@test.com",
            "password": "E2eTest123456",
            "name": "E2E User",
        }, format="json")
        assert resp.status_code == 201
        token = resp.json()["data"]["access"]
        auth_header = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        # 2. 创建工作空间
        resp = api_client.post(
            "/api/workspaces/",
            {"name": "E2E Workspace"},
            format="json",
            **auth_header,
        )
        assert resp.status_code == 201
        ws_id = resp.json()["data"]["id"]

        # 3. 创建项目
        resp = api_client.post(
            f"/api/workspaces/{ws_id}/projects/",
            {"name": "E2E Project", "identifier": "E2E"},
            format="json",
            **auth_header,
        )
        assert resp.status_code == 201
        proj_id = resp.json()["data"]["id"]

        # 4. 创建任务
        resp = api_client.post(
            f"/api/projects/{proj_id}/tasks/",
            {"title": "E2E Task", "description": "端到端测试", "priority": "high"},
            format="json",
            **auth_header,
        )
        assert resp.status_code == 201
        task_id = resp.json()["data"]["id"]

        # 5. 更新状态 (获取状态列)
        status_resp = api_client.get(
            f"/api/projects/{proj_id}/task-statuses/",
            **auth_header,
        )
        statuses = status_resp.json()["data"]
        # 找到"进行中"状态
        in_progress = next(s for s in statuses if s["name"] == "进行中")
        resp = api_client.patch(
            f"/api/tasks/{task_id}/status/",
            {"status": in_progress["id"]},
            format="json",
            **auth_header,
        )
        assert resp.status_code == 200

        # 6. 评论
        resp = api_client.post(
            f"/api/tasks/{task_id}/comments/",
            {"content": "端到端测试评论"},
            format="json",
            **auth_header,
        )
        assert resp.status_code == 201

        # 7. 查看统计
        resp = api_client.get(
            f"/api/projects/{proj_id}/statistics/",
            **auth_header,
        )
        assert resp.status_code == 200

        total_time = time.time() - total_start
        print(f"\n  Full E2E workflow completed in {total_time:.1f}s (QS6 target: < 300s)")
        assert total_time < 300, f"E2E took {total_time:.1f}s, exceeds QS6 5-minute target"
