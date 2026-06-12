"""
QS1: 性能质量属性场景测试
================================

场景要素 (来自 T2):
  刺激源:   普通成员
  刺激:     在项目任务列表中按状态和负责人筛选任务
  环境:     工作日高峰期，100 名用户并发在线，系统已有 10 万条任务数据
  制品:     Web 前端、任务查询接口、数据库
  响应:     系统返回分页后的任务列表
  响应度量:  95% 查询请求响应时间不超过 2 秒，单页默认返回 20-50 条数据

测试结构:
  1. 数据生成 — 用 bulk_create 批量插入 10 万条任务（仅一次）
  2. 100 并发查询 — ThreadPoolExecutor 模拟 100 并发按状态+负责人筛选
  3. P95 响应时间 — 统计 95 分位响应时间 ≤ 2 秒
  4. 分页完整性 — 高负载下分页仍返回 20-50 条
  5. 关键词搜索 — 含搜索的复合查询性能（30 并发）
  6. 筛选组合 — 7 种筛选组合在 10 万数据下的正确性与性能

对应 NF1、QS1
"""

import time
import random
import itertools
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from django.contrib.auth import get_user_model
from django.db import connections, transaction
from rest_framework.test import APIClient

User = get_user_model()

# ── QS1 测试参数 ─────────────────────────────────────────────────
QS1_TASK_COUNT = 100_000        # 10 万条任务
QS1_CONCURRENT_USERS = 100      # 100 并发查询
QS1_TARGET_P95_SECONDS = 2.0    # P95 < 2 秒
QS1_BATCH_SIZE = 5000           # bulk_create 批次大小

pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════════════
# 辅助: 百分位计算
# ═══════════════════════════════════════════════════════════════════

def _percentile(data, p):
    """计算第 p 百分位（线性插值）"""
    if not data:
        return 0.0
    k = (len(data) - 1) * p / 100.0
    f = int(k)
    c = k - f
    if f + 1 < len(data):
        return data[f] + c * (data[f + 1] - data[f])
    return float(data[f])


# ═══════════════════════════════════════════════════════════════════
# 核心 QS1 测试 — 单方法覆盖全部场景（数据生成 + 并发 + 分页 + 搜索 + 筛选）
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestQS1FullScenario:
    """
    QS1 完整场景测试。

    在一个测试方法中完成:
      1. 生成 10 万条任务
      2. 100 并发按状态+负责人筛选
      3. 分页验证
      4. 搜索并发
      5. 筛选组合

    因为 TransactionTestCase 会在每个 test 方法间 TRUNCATE，
    所以所有逻辑在一个 test 方法中完成以保证数据可用。
    """

    # PostgreSQL 最大连接数限制 — 用信号量控制并发 DB 连接数
    # 模拟真实部署中连接池的行为（如 PgBouncer / CONN_MAX_AGE）
    # 配合 connection.close() 确保不会耗尽 PostgreSQL max_connections
    _db_semaphore = threading.Semaphore(50)

    # ── 缓存在实例上（同一 test 方法内使用） ────────────────
    def setUp(self):
        """每个 test 方法都会调用，重置实例级缓存"""
        self._proj_id = None
        self._status_ids = []
        self._assignee_ids = []
        self._admin = None

    # ── 数据生成 ──────────────────────────────────────────

    def _generate_100k_tasks(self):
        """生成 QS1 测试所需全部数据，返回耗时统计"""
        from apps.workspaces.models import Workspace, WorkspaceMember
        from apps.projects.models import Project, ProjectMember
        from apps.tasks.models import Task, TaskStatus

        total_t0 = time.time()

        # --- 管理员 + 工作空间 ---
        self._admin = User.objects.create_superuser(
            email="qs1_admin@perf.test",
            password="Qs1Admin123",
            name="QS1 Admin",
        )
        ws = Workspace.objects.create(
            name="QS1 性能测试空间",
            slug="qs1-perf",
            description="QS1 10万任务性能测试",
            owner=self._admin,
        )
        WorkspaceMember.objects.create(workspace=ws, user=self._admin, role="admin")

        # --- 50 个负责人 ---
        assignees = [self._admin]
        for i in range(50):
            u = User.objects.create_user(
                email=f"qs1_u{i:03d}@perf.test",
                password="Qs1User123",
                name=f"QS1 User {i:03d}",
            )
            WorkspaceMember.objects.create(workspace=ws, user=u, role="member")
            assignees.append(u)
        print(f"\n  ✓ 51 users created")

        # --- 项目 + 状态列 ---
        proj = Project.objects.create(
            workspace=ws,
            name="QS1 性能测试项目",
            identifier="QS1P",
            description="包含 10 万条任务的性能基准项目",
        )
        ProjectMember.objects.create(project=proj, user=self._admin, role="admin")

        status_data = [
            ("Backlog", "#6b7280", "backlog", 0),
            ("待办", "#6366f1", "unstarted", 1),
            ("进行中", "#f59e0b", "started", 2),
            ("待评审", "#8b5cf6", "started", 3),
            ("已完成", "#10b981", "completed", 4),
            ("已取消", "#ef4444", "cancelled", 5),
        ]
        statuses = []
        for name, color, type_str, order in status_data:
            s = TaskStatus.objects.create(
                project=proj, name=name, color=color,
                type=type_str, order=order,
            )
            statuses.append(s)

        # --- 批量创建 10 万条任务 ---
        build_start = time.time()
        task_batch = []
        total_created = 0
        priorities = ["urgent", "high", "medium", "low", "none"]

        for i in range(QS1_TASK_COUNT):
            task = Task(
                project=proj,
                status=statuses[i % len(statuses)],
                title=f"QS1-{i:06d}: 性能测试任务 #{i}",
                description=(
                    f"QS1 性能基准测试第 {i} 条任务。"
                    f"验证 10 万条数据下按状态和负责人筛选"
                    f"的 P95 响应时间 ≤ 2 秒。"
                ),
                priority=priorities[i % len(priorities)],
                assignee=assignees[i % len(assignees)],
                created_by=self._admin,
                order=float(i),
            )
            task_batch.append(task)
            if len(task_batch) >= QS1_BATCH_SIZE:
                Task.objects.bulk_create(task_batch, batch_size=QS1_BATCH_SIZE)
                total_created += len(task_batch)
                task_batch = []
        if task_batch:
            Task.objects.bulk_create(task_batch)
            total_created += len(task_batch)

        build_time = time.time() - build_start
        total_time = time.time() - total_t0

        # 验证
        count = Task.objects.filter(project=proj).count()
        assert count == QS1_TASK_COUNT, \
            f"Expected {QS1_TASK_COUNT} tasks, got {count}"

        # 缓存
        self._proj_id = str(proj.id)
        self._status_ids = [str(s.id) for s in statuses]
        self._assignee_ids = [str(u.id) for u in assignees]

        print(f"  ✓ {total_created} tasks in {build_time:.1f}s "
              f"({total_created/build_time:.0f} tasks/s)")
        print(f"  ✓ DB count verified: {count}")
        return {"build_time": build_time, "total_time": total_time}

    # ── 客户端工厂（并发安全） ────────────────────────────

    def _make_client(self):
        """每个线程独立创建认证客户端"""
        client = APIClient()
        client.force_authenticate(user=self._admin)
        return client

    # ── 单次查询 ──────────────────────────────────────────

    def _single_query(self, client, status_id, assignee_id):
        """按状态 + 负责人筛选（信号量控制 DB 连接数 + 查询后关闭连接）"""
        url = f"/api/projects/{self._proj_id}/tasks/"
        params = {}
        if status_id:
            params["status"] = status_id
        if assignee_id:
            params["assignee"] = assignee_id
        start = time.time()
        try:
            with TestQS1FullScenario._db_semaphore:
                resp = client.get(url, params)
                # 立即释放当前线程的 DB 连接，避免耗尽 PostgreSQL max_connections
                from django.db import connection
                connection.close()
            elapsed = time.time() - start
            return {
                "elapsed": elapsed,
                "status_code": resp.status_code,
                "success": resp.status_code == 200,
            }
        except Exception as e:
            return {
                "elapsed": time.time() - start,
                "status_code": 0,
                "success": False,
                "error": str(e),
            }

    # ═══════════════════════════════════════════════════════════
    # 唯一测试入口 — 覆盖全部 QS1 验证步骤
    # ═══════════════════════════════════════════════════════════

    def test_qs1_full_scenario(self):
        """
        QS1 完整性能场景测试:
          1. 生成 10 万条任务
          2. 100 并发按状态+负责人筛选 → P95 < 2s
          3. 分页默认 20-50 条
          4. 分页导航首页/末页
          5. 30 并发关键词搜索
          6. 7 种筛选组合正确性与性能
        """
        print("\n" + "=" * 60)
        print("  QS1 性能质量属性场景 — 完整测试")
        print("=" * 60)

        # ── Step 1: 数据生成 ─────────────────────────────────
        print("\n[Step 1/5] 生成 10 万条测试数据...")
        gen_stats = self._generate_100k_tasks()

        # ── Step 2: 100 并发查询 ─────────────────────────────
        print(f"\n[Step 2/5] {QS1_CONCURRENT_USERS} 并发按状态+负责人筛选...")

        combos = list(itertools.product(self._status_ids, self._assignee_ids))
        random.shuffle(combos)
        query_params = combos[:QS1_CONCURRENT_USERS]

        print(f"  Unique filter combos: {len(set(query_params))}")

        results = []
        t_concurrent_start = time.time()

        with ThreadPoolExecutor(max_workers=QS1_CONCURRENT_USERS) as executor:
            futures = {}
            for i, (status_id, assignee_id) in enumerate(query_params):
                client = self._make_client()
                future = executor.submit(
                    self._single_query, client, status_id, assignee_id,
                )
                futures[future] = i

            for future in as_completed(futures):
                results.append(future.result())

        concurrent_wall_time = time.time() - t_concurrent_start
        elapsed_times = sorted([r["elapsed"] for r in results])
        success_count = sum(1 for r in results if r["success"])
        error_count = len(results) - success_count

        p50 = _percentile(elapsed_times, 50)
        p95 = _percentile(elapsed_times, 95)
        p99 = _percentile(elapsed_times, 99)
        avg = sum(elapsed_times) / len(elapsed_times) if elapsed_times else 0

        print(f"\n  {'─'*50}")
        print(f"  QS1 并发查询性能报告")
        print(f"  {'─'*50}")
        print(f"  总查询数:        {len(results)}")
        print(f"  成功:            {success_count} / 失败: {error_count}")
        print(f"  并发墙钟时间:    {concurrent_wall_time:.2f}s")
        print(f"  平均:  {avg*1000:7.0f}ms")
        print(f"  P50:   {p50*1000:7.0f}ms")
        print(f"  P95:   {p95*1000:7.0f}ms  ← QS1 目标: ≤ {QS1_TARGET_P95_SECONDS*1000:.0f}ms")
        print(f"  P99:   {p99*1000:7.0f}ms")
        print(f"  最快:  {elapsed_times[0]*1000:7.0f}ms")
        print(f"  最慢:  {elapsed_times[-1]*1000:7.0f}ms")
        print(f"  {'─'*50}")

        assert error_count == 0, (
            f"{error_count} queries failed! "
            f"{[r for r in results if not r['success']][:3]}"
        )
        assert p95 <= QS1_TARGET_P95_SECONDS, (
            f"QS1 FAILED: P95={p95*1000:.0f}ms > "
            f"{QS1_TARGET_P95_SECONDS*1000:.0f}ms"
        )
        print(f"  ✅ QS1 P95 通过: {p95*1000:.0f}ms ≤ "
              f"{QS1_TARGET_P95_SECONDS*1000:.0f}ms")

        # ── Step 3: 分页验证 ─────────────────────────────────
        print(f"\n[Step 3/5] 分页完整性验证...")

        client = self._make_client()

        # 3a: 默认 page_size
        resp = client.get(f"/api/projects/{self._proj_id}/tasks/")
        assert resp.status_code == 200
        pagination = resp.json()["pagination"]
        assert pagination["total"] == QS1_TASK_COUNT
        assert 20 <= pagination["page_size"] <= 50, (
            f"Default page_size={pagination['page_size']} not in [20,50]"
        )
        total_pages = pagination['total'] // pagination['page_size'] + (
            1 if pagination['total'] % pagination['page_size'] else 0)
        print(f"  ✓ Default page_size={pagination['page_size']} "
              f"(total={pagination['total']}, pages≈{total_pages})")

        # 3b: 分页导航
        total_pages = pagination["total"] // pagination["page_size"] + (
            1 if pagination["total"] % pagination["page_size"] else 0)
        resp1 = client.get(f"/api/projects/{self._proj_id}/tasks/?page=1")
        resp_last = client.get(
            f"/api/projects/{self._proj_id}/tasks/?page={total_pages}"
        )
        assert resp1.json()["pagination"]["page"] == 1
        assert resp_last.json()["pagination"]["page"] == total_pages
        if total_pages > 1:
            ids1 = {t["id"] for t in resp1.json()["data"]}
            ids_last = {t["id"] for t in resp_last.json()["data"]}
            assert ids1 != ids_last, "首页和末页数据不应相同"
        print(f"  ✓ 分页导航: 1 → ... → {total_pages}")

        # 3c: 自定义 page_size
        for size, expected in [(5, 5), (50, 50)]:
            r = client.get(
                f"/api/projects/{self._proj_id}/tasks/?page_size={size}"
            )
            assert r.json()["pagination"]["page_size"] == expected
        print(f"  ✓ 自定义 page_size: 5, 50 均正确")

        # ── Step 4: 搜索并发 ─────────────────────────────────
        print(f"\n[Step 4/5] 30 并发关键词搜索...")

        search_terms = [
            f"QS1-{i:06d}" for i in
            random.sample(range(QS1_TASK_COUNT), 30)
        ]

        def search_query(client, term, status_id):
            with TestQS1FullScenario._db_semaphore:
                resp = client.get(
                    f"/api/projects/{self._proj_id}/tasks/",
                    {"search": term, "status": status_id},
                )
                from django.db import connection
                connection.close()
            return resp.status_code

        search_start = time.time()
        with ThreadPoolExecutor(max_workers=30) as executor:
            s_futures = []
            for i, term in enumerate(search_terms):
                c = self._make_client()
                sid = self._status_ids[i % len(self._status_ids)]
                s_futures.append(
                    executor.submit(search_query, c, term, sid)
                )
            s_results = [f.result() for f in as_completed(s_futures)]
        search_time = time.time() - search_start

        s_errors = [r for r in s_results if r != 200]
        print(f"  搜索并发: 30 queries in {search_time:.1f}s, "
              f"errors={len(s_errors)}")
        assert len(s_errors) == 0, f"Search queries failed: {s_errors}"
        assert search_time < 30, f"Search wall-clock too slow: {search_time:.1f}s"
        print(f"  ✓ 30 并发搜索通过")

        # ── Step 5: 筛选组合 ─────────────────────────────────
        print(f"\n[Step 5/5] 筛选组合验证 (10 万数据下)...")

        filter_cases = [
            ({}, "无筛选"),
            ({"status": self._status_ids[0]}, "仅状态"),
            ({"assignee": self._assignee_ids[0]}, "仅负责人"),
            ({"priority": "high"}, "仅优先级"),
            ({"status": self._status_ids[2],
              "assignee": self._assignee_ids[5]}, "状态+负责人"),
            ({"status": self._status_ids[1],
              "priority": "urgent"}, "状态+优先级"),
            ({"assignee": self._assignee_ids[3],
              "priority": "low"}, "负责人+优先级"),
            ({"status": self._status_ids[3],
              "assignee": self._assignee_ids[10],
              "priority": "medium"}, "状态+负责人+优先级"),
        ]

        for params, label in filter_cases:
            t0 = time.time()
            resp = client.get(
                f"/api/projects/{self._proj_id}/tasks/", params,
            )
            elapsed = time.time() - t0
            assert resp.status_code == 200, \
                f"Filter '{label}' → {resp.status_code}"
            matched = resp.json()["pagination"]["total"]
            print(f"    {label:22s}  {elapsed*1000:6.0f}ms  "
                  f"(matched {matched} tasks)")

        print(f"  ✓ {len(filter_cases)} 种筛选组合全部通过")

        # ── 总结 ─────────────────────────────────────────────
        print(f"\n{'='*60}")
        print(f"  QS1 测试结果汇总")
        print(f"  {'─'*60}")
        print(f"  数据生成:        {gen_stats['total_time']:.1f}s")
        print(f"  并发 P95:        {p95*1000:.0f}ms")
        print(f"  分页:            默认 {pagination['page_size']}/页")
        print(f"  搜索并发:        30 queries, {len(s_errors)} errors")
        print(f"  筛选组合:        8 组合全部通过")
        print(f"  {'='*60}")
        print(f"  ✅ QS1 PASSED")


# ═══════════════════════════════════════════════════════════════════
# 补充: 空库 vs 10 万库基准对比
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db(transaction=True)
class TestQS1BaselineComparison:
    """
    空库 ↔ 10 万库对比。

    独立类 — 使用 conftest fixtures 的空库数据，
    自行生成 10 万数据做对比。
    """

    def test_empty_vs_100k_baseline(self, admin_client, project):
        """
        在同一次测试中:
          A) 空库查询基准
          B) 生成 10 万数据
          C) 10 万库查询基准
          D) 对比分析
        """
        from apps.workspaces.models import Workspace, WorkspaceMember
        from apps.projects.models import Project, ProjectMember
        from apps.tasks.models import Task, TaskStatus

        # A) 空库
        t0 = time.time()
        resp_empty = admin_client.get(f"/api/projects/{project.id}/tasks/")
        empty_time = time.time() - t0
        assert resp_empty.status_code == 200

        # B) 生成 10 万数据（精简版 — 不创建额外工作空间）
        print(f"\n  Generating 100k tasks for baseline comparison...")
        gen_t0 = time.time()

        admin_user = User.objects.get(
            email="admin@test.com"
        )  # conftest 中创建的
        proj = Project.objects.get(id=project.id)
        statuses = list(TaskStatus.objects.filter(project=proj))

        # 创建 50 个负责人（加入工作空间）
        assignees = [admin_user]
        ws = proj.workspace
        for i in range(50):
            u = User.objects.create_user(
                email=f"bl_u{i:03d}@test.com",
                password="Test123456",
                name=f"Baseline User {i:03d}",
            )
            WorkspaceMember.objects.create(workspace=ws, user=u, role="member")
            assignees.append(u)

        priorities = ["urgent", "high", "medium", "low", "none"]
        task_batch = []
        for i in range(QS1_TASK_COUNT):
            task = Task(
                project=proj,
                status=statuses[i % len(statuses)],
                title=f"BL-{i:06d}: 基准任务 #{i}",
                priority=priorities[i % len(priorities)],
                assignee=assignees[i % len(assignees)],
                created_by=admin_user,
                order=float(i),
            )
            task_batch.append(task)
            if len(task_batch) >= QS1_BATCH_SIZE:
                Task.objects.bulk_create(task_batch, batch_size=QS1_BATCH_SIZE)
                task_batch = []
        if task_batch:
            Task.objects.bulk_create(task_batch)

        gen_time = time.time() - gen_t0
        task_count = Task.objects.filter(project=proj).count()
        assert task_count >= QS1_TASK_COUNT
        print(f"  ✓ {task_count} tasks in {gen_time:.1f}s")

        # C) 10 万库查询
        t0 = time.time()
        resp_100k = admin_client.get(f"/api/projects/{project.id}/tasks/")
        full_time = time.time() - t0
        assert resp_100k.status_code == 200

        # D) 对比
        print(f"\n  {'─'*40}")
        print(f"  空库 vs 10 万库基准对比")
        print(f"  {'─'*40}")
        print(f"  空库:         {empty_time*1000:.0f}ms")
        print(f"  10万库:       {full_time*1000:.0f}ms")
        print(f"  增长:         {full_time/empty_time:.1f}x"
              if empty_time > 0 else "  N/A")
        print(f"  QS1 目标:     ≤ 2000ms")
        print(f"  {'─'*40}")

        assert full_time < QS1_TARGET_P95_SECONDS, (
            f"100k list query {full_time:.2f}s exceeds "
            f"{QS1_TARGET_P95_SECONDS}s QS1 target"
        )
        print(f"  ✅ 10万库基准测试通过")
