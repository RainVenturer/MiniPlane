"""
UC8: 迭代管理与统计

测试覆盖:
  - 创建迭代 (POST /api/projects/{proj_id}/iterations/)
  - 列出迭代 (GET)
  - 迭代详情/编辑
  - 迭代统计 (GET /api/iterations/{id}/statistics/)
  - 项目统计 (GET /api/projects/{id}/statistics/)

对应 F10、F13
"""

import pytest
from datetime import date

pytestmark = pytest.mark.django_db


class TestIterationCRUD:
    """迭代增删改查"""

    def test_create_iteration(self, admin_client, project):
        """创建迭代周期"""
        resp = admin_client.post(f"/api/projects/{project.id}/iterations/", {
            "name": "Sprint 1",
            "start_date": "2026-06-01",
            "end_date": "2026-06-14",
            "description": "第一轮迭代",
        }, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["name"] == "Sprint 1"

    def test_list_iterations(self, admin_client, project, iteration):
        """列出项目迭代"""
        resp = admin_client.get(f"/api/projects/{project.id}/iterations/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_retrieve_iteration(self, admin_client, iteration):
        """查看迭代详情"""
        resp = admin_client.get(
            f"/api/projects/{iteration.project_id}/iterations/{iteration.id}/"
        )
        assert resp.status_code == 200

    def test_update_iteration(self, admin_client, iteration):
        """编辑迭代"""
        resp = admin_client.patch(
            f"/api/projects/{iteration.project_id}/iterations/{iteration.id}/", {
                "description": "更新后的迭代描述",
            }, format="json")
        assert resp.status_code == 200

    def test_delete_iteration(self, admin_client, iteration):
        """删除迭代"""
        resp = admin_client.delete(
            f"/api/projects/{iteration.project_id}/iterations/{iteration.id}/"
        )
        assert resp.status_code == 204

    def test_create_iteration_invalid_dates(self, admin_client, project):
        """结束日期早于开始日期应拒绝"""
        resp = admin_client.post(f"/api/projects/{project.id}/iterations/", {
            "name": "Invalid Sprint",
            "start_date": "2026-06-14",
            "end_date": "2026-06-01",
        }, format="json")
        assert resp.status_code == 400

    def test_create_iteration_empty_name(self, admin_client, project):
        """空名称应拒绝"""
        resp = admin_client.post(f"/api/projects/{project.id}/iterations/", {
            "name": "",
            "start_date": "2026-06-01",
            "end_date": "2026-06-14",
        }, format="json")
        assert resp.status_code == 400


class TestIterationStatistics:
    """迭代统计"""

    def test_iteration_statistics(self, admin_client, iteration):
        """获取迭代统计数据"""
        resp = admin_client.get(f"/api/iterations/{iteration.id}/statistics/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "completion_rate" in data

    def test_iteration_stats_with_tasks(self, admin_client, project, iteration, task):
        """有任务时的迭代统计"""
        # 将任务分配到迭代
        import json
        admin_client.patch(f"/api/tasks/{task.id}/", json.dumps({
            "iteration": str(iteration.id),
        }), content_type="application/json")
        resp = admin_client.get(f"/api/iterations/{iteration.id}/statistics/")
        assert resp.status_code == 200


class TestProjectStatistics:
    """项目统计 (F13)"""

    def test_project_statistics(self, admin_client, project):
        """获取项目统计数据"""
        resp = admin_client.get(f"/api/projects/{project.id}/statistics/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "completion_rate" in data
        assert "status_distribution" in data
        assert "priority_distribution" in data

    def test_project_stats_with_data(self, admin_client, project, task):
        """有任务数据时的项目统计"""
        resp = admin_client.get(f"/api/projects/{project.id}/statistics/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_tasks"] >= 1
